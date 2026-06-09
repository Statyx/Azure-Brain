# Second fixup pass: handle decorated object names from formatting.json
# e.g. "fill (selector: default|hover|...)" → base "fill"
# Only fetches missing object files.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$visualsDir = Join-Path $root "visuals"

function Invoke-CLI {
    param([string[]]$CliArgs)
    $out = & powerbi-report-author @CliArgs --pretty 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "powerbi-report-author $($CliArgs -join ' ') failed: $out"
    }
    return ($out -join "`n")
}

$visualTypes = (Get-Content (Join-Path $root "visual_types.json") -Raw | ConvertFrom-Json).data.visualTypes
$saved = 0
$skipped = 0
$failures = @()

foreach ($vt in $visualTypes) {
    $vdir = Join-Path $visualsDir $vt
    $objectsDir = Join-Path $vdir "objects"
    if (-not (Test-Path $objectsDir)) { New-Item -ItemType Directory -Path $objectsDir -Force | Out-Null }

    $fmtPath = Join-Path $vdir "formatting.json"
    if (-not (Test-Path $fmtPath)) { continue }
    $rawObjects = (Get-Content $fmtPath -Raw | ConvertFrom-Json).data.objects
    if (-not $rawObjects) { continue }

    # Strip "(selector: ...)" suffix and dedup base names
    $baseNames = @{}
    foreach ($o in $rawObjects) {
        $name = [string]$o
        $stripped = ($name -replace '\s*\(selector:[^)]+\)\s*$', '').Trim()
        if ($stripped) { $baseNames[$stripped] = $true }
    }

    foreach ($oname in $baseNames.Keys) {
        $outPath = Join-Path $objectsDir "$oname.json"
        if (Test-Path $outPath) { $skipped++; continue }
        try {
            $od = Invoke-CLI @("formatting", "describe-object", $vt, $oname)
            $od | Set-Content -Path $outPath -Encoding UTF8
            $saved++
            Write-Host "  + $vt / $oname"
        } catch {
            $failures += "describe-object $vt $oname :: $_"
        }
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Saved : $saved"
Write-Host "Skipped (already present): $skipped"
Write-Host "Failures : $($failures.Count)"

$summaryPath = Join-Path $root "fixup2_summary.json"
$summary = [ordered]@{
    saved          = $saved
    skipped        = $skipped
    failures_count = $failures.Count
    failures       = $failures
}
$summary | ConvertTo-Json -Depth 4 | Set-Content -Path $summaryPath -Encoding UTF8
Write-Host "Summary: $summaryPath"

# Also patch every formatting.json: add objectsBase (deduped, stripped) for consumers.
foreach ($vt in $visualTypes) {
    $fmtPath = Join-Path $visualsDir $vt "formatting.json"
    if (-not (Test-Path $fmtPath)) { continue }
    $obj = Get-Content $fmtPath -Raw | ConvertFrom-Json
    $base = @{}
    foreach ($o in @($obj.data.objects)) {
        $name = [string]$o
        $stripped = ($name -replace '\s*\(selector:[^)]+\)\s*$', '').Trim()
        if ($stripped) { $base[$stripped] = $true }
    }
    $obj.data | Add-Member -NotePropertyName objectsBase -NotePropertyValue ([string[]]($base.Keys | Sort-Object)) -Force
    $obj | ConvertTo-Json -Depth 8 | Set-Content -Path $fmtPath -Encoding UTF8
}
Write-Host "All formatting.json now have an 'objectsBase' field (stripped, deduped)."
