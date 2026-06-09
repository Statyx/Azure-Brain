# Add objectsBase[] field (stripped + deduped) to every visuals/<vt>/formatting.json
# PS 5.1 compatible (only 2-arg Join-Path).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$visualsDir = Join-Path $root "visuals"

$visualTypes = (Get-Content (Join-Path $root "visual_types.json") -Raw | ConvertFrom-Json).data.visualTypes
$patched = 0
foreach ($vt in $visualTypes) {
    $vdir = Join-Path $visualsDir $vt
    $fmtPath = Join-Path $vdir "formatting.json"
    if (-not (Test-Path $fmtPath)) { continue }
    $obj = Get-Content $fmtPath -Raw | ConvertFrom-Json
    $base = @{}
    foreach ($o in @($obj.data.objects)) {
        $name = [string]$o
        $stripped = ($name -replace '\s*\(selector:[^)]+\)\s*$', '').Trim()
        if ($stripped) { $base[$stripped] = $true }
    }
    $sorted = [string[]]($base.Keys | Sort-Object)
    $obj.data | Add-Member -NotePropertyName objectsBase -NotePropertyValue $sorted -Force
    $obj | ConvertTo-Json -Depth 8 | Set-Content -Path $fmtPath -Encoding UTF8
    $patched++
}
Write-Host "Patched $patched formatting.json files with 'objectsBase'."
