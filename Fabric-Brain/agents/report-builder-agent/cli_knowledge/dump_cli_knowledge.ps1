# Dump powerbi-report-author CLI knowledge into versioned JSON files.
#
# Usage:
#   pwsh ./dump_cli_knowledge.ps1
#
# Requires:
#   npm install -g @microsoft/powerbi-report-authoring-cli
#
# Output structure:
#   cli_knowledge/
#     metadata.json
#     dump_summary.json
#     visual_types.json
#     vcos/index.json
#     vcos/<vco>.json
#     visuals/<type>/catalog.json              (catalog describe)
#     visuals/<type>/formatting.json           (formatting list-objects)
#     visuals/<type>/effective.json            (formatting effective-properties)
#     visuals/<type>/objects/<obj>.json        (formatting describe-object)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$visualsDir = Join-Path $root "visuals"
$vcosDir = Join-Path $root "vcos"

function Ensure-Dir($p) { if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null } }

function Invoke-CLI {
    param([string[]]$CliArgs)
    $out = & powerbi-report-author @CliArgs --pretty 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "powerbi-report-author $($CliArgs -join ' ') failed: $out"
    }
    return ($out -join "`n")
}

Ensure-Dir $visualsDir
Ensure-Dir $vcosDir

Write-Host "1/6 doctor + version" -ForegroundColor Cyan
$cliVersion = (& powerbi-report-author --version).Trim()
$doctorRaw = Invoke-CLI @("doctor")
$doctor = $doctorRaw | ConvertFrom-Json

$metadata = [ordered]@{
    cli_version       = $cliVersion
    dumped_at_utc     = (Get-Date).ToUniversalTime().ToString("o")
    visual_type_count = $doctor.data.provider.visualTypeCount
    vco_count         = $doctor.data.provider.vcoCount
    provider_source   = $doctor.data.provider.source
}
$metadata | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $root "metadata.json") -Encoding UTF8

Write-Host "2/6 visual types list" -ForegroundColor Cyan
$catalogList = Invoke-CLI @("catalog", "list")
$catalogList | Set-Content -Path (Join-Path $root "visual_types.json") -Encoding UTF8
$visualTypes = ($catalogList | ConvertFrom-Json).data.visualTypes
Write-Host "   -> $($visualTypes.Count) visual types"

# Pick a reference visual type to query VCOs against (describe-object needs visualType + vcoName).
$refVisual = if ($visualTypes -contains "cardVisual") { "cardVisual" } else { $visualTypes[0] }
Write-Host "   -> using '$refVisual' as reference for VCO descriptions"

Write-Host "3/6 VCOs (shared visualContainerObjects)" -ForegroundColor Cyan
$vcoListRaw = Invoke-CLI @("formatting", "list-vcos")
$vcoListRaw | Set-Content -Path (Join-Path $vcosDir "index.json") -Encoding UTF8
$vcoParsed = ($vcoListRaw | ConvertFrom-Json).data
$vcoList = if ($vcoParsed.vcos) { $vcoParsed.vcos } elseif ($vcoParsed.visualContainerObjects) { $vcoParsed.visualContainerObjects } else { @() }

foreach ($vco in $vcoList) {
    $name = if ($vco.PSObject.Properties['name']) { $vco.name } else { [string]$vco }
    Write-Host "   - vco: $name"
    try {
        $detail = Invoke-CLI @("formatting", "describe-object", $refVisual, $name)
        $detail | Set-Content -Path (Join-Path $vcosDir "$name.json") -Encoding UTF8
    } catch {
        Write-Warning "   describe-object $refVisual $name failed: $_"
    }
}

Write-Host "4/6 catalog + formatting per visual type" -ForegroundColor Cyan
$failures = @()
$i = 0
foreach ($vt in $visualTypes) {
    $i++
    Write-Host ("   [{0}/{1}] {2}" -f $i, $visualTypes.Count, $vt)
    $vdir = Join-Path $visualsDir $vt
    Ensure-Dir $vdir
    Ensure-Dir (Join-Path $vdir "objects")

    try {
        $cat = Invoke-CLI @("catalog", "describe", $vt)
        $cat | Set-Content -Path (Join-Path $vdir "catalog.json") -Encoding UTF8
    } catch { $failures += "catalog describe $vt :: $_"; continue }

    try {
        $eff = Invoke-CLI @("formatting", "effective-properties", $vt)
        $eff | Set-Content -Path (Join-Path $vdir "effective.json") -Encoding UTF8
    } catch { $failures += "effective-properties $vt :: $_" }

    try {
        $fmt = Invoke-CLI @("formatting", "list-objects", $vt)
        $fmt | Set-Content -Path (Join-Path $vdir "formatting.json") -Encoding UTF8
        $fmtData = ($fmt | ConvertFrom-Json).data
        $objects = if ($fmtData.objects) { $fmtData.objects } else { @() }
        foreach ($obj in $objects) {
            $oname = if ($obj.PSObject.Properties['name']) { $obj.name } else { [string]$obj }
            try {
                $od = Invoke-CLI @("formatting", "describe-object", $vt, $oname)
                $od | Set-Content -Path (Join-Path $vdir "objects" "$oname.json") -Encoding UTF8
            } catch { $failures += "describe-object $vt $oname :: $_" }
        }
    } catch { $failures += "list-objects $vt :: $_" }
}

Write-Host "5/6 summary" -ForegroundColor Cyan
$summary = [ordered]@{
    cli_version       = $cliVersion
    visual_types      = $visualTypes.Count
    vcos              = $vcoList.Count
    failures_count    = $failures.Count
    failures          = $failures
}
$summary | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $root "dump_summary.json") -Encoding UTF8

Write-Host "6/6 done" -ForegroundColor Green
Write-Host "Visual types : $($visualTypes.Count)"
Write-Host "VCOs         : $($vcoList.Count)"
Write-Host "Failures     : $($failures.Count)"
if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "First failures (see dump_summary.json):" -ForegroundColor Yellow
    $failures | Select-Object -First 10 | ForEach-Object { Write-Host "  - $_" }
}
