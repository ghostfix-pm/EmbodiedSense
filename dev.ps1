# Project-local uv entry point; no permanent system setting changes.
$ErrorActionPreference = 'Stop'
$taskUv = Get-Command uv -ErrorAction SilentlyContinue
$taskUvPath = if ($taskUv) { $taskUv.Source } else { 'D:\DevTools\uv\bin\uv.exe' }
if (-not (Test-Path -LiteralPath $taskUvPath)) {
    throw 'uv not found. Install uv from https://docs.astral.sh/uv/getting-started/installation/'
}
if (Test-Path -LiteralPath 'D:\') {
    $taskCache = 'D:\DevCache\EmbodiedSense'
    New-Item -ItemType Directory -Path $taskCache -Force | Out-Null
    $env:UV_CACHE_DIR = Join-Path $taskCache 'uv'
    $env:TEMP = $taskCache
    $env:TMP = $taskCache
}
& $taskUvPath @args
exit $LASTEXITCODE
