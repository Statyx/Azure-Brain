# Fix-up pass: redo describe-object calls for every visual.
# Run after dump_cli_knowledge.ps1 if objects/*.json files are missing.
# Uses 2-arg Join-Path only (PS 5.1 compatible).

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
Write-Host "Will redo describe-object for $($visualTypes.Count) visuals"

$failures = @()
$savedCount = 0
$i = 0
foreach ($vt in $visualTypes) {
    $i++
    $vdir = Join-Path $visualsDir $vt
    $objectsDir = Join-Path $vdir "objects"
    if (-not (Test-Path $objectsDir)) { New-Item -ItemType Directory -Path $objectsDir -Force | Out-Null }

    $fmtPath = Join-Path $vdir "formatting.json"
    if (-not (Test-Path $fmtPath)) {
        Write-Warning "[$i/$($visualTypes.Count)] $vt - formatting.json missing, skip"
        continue
    }
    $fmtData = (Get-Content $fmtPath -Raw | ConvertFrom-Json).data
    $objects = if ($fmtData.objects) { $fmtData.objects } else { @() }

    Write-Host ("[{0}/{1}] {2} - {3} objects" -f $i, $visualTypes.Count, $vt, $objects.Count)

    foreach ($obj in $objects) {
        $oname = if ($obj.PSObject.Properties['name']) { $obj.name } else { [string]$obj }
        $outPath = Join-Path $objectsDir "$oname.json"
        try {
            $od = Invoke-CLI @("formatting", "describe-object", $vt, $oname)
            $od | Set-Content -Path $outPath -Encoding UTF8
            $savedCount++
        } catch {
            $failures += "describe-object $vt $oname :: $_"
        }
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Object files saved : $savedCount"
Write-Host "Failures           : $($failures.Count)"

$summaryPath = Join-Path $root "fixup_summary.json"
$summary = [ordered]@{
    saved          = $savedCount
    failures_count = $failures.Count
    failures       = $failures
}
$summary | ConvertTo-Json -Depth 4 | Set-Content -Path $summaryPath -Encoding UTF8
Write-Host "Summary: $summaryPath"
