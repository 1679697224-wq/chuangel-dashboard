$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$processFile = Join-Path $root "runtime\processes.json"
if (-not (Test-Path -LiteralPath $processFile)) {
  Write-Output "No recorded briefing processes."
  exit 0
}

$processes = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
foreach ($id in @($processes.serverPid, $processes.tunnelPid)) {
  if ($id -and (Get-Process -Id $id -ErrorAction SilentlyContinue)) {
    Stop-Process -Id $id
  }
}
Write-Output "Briefing server and tunnel stopped."
