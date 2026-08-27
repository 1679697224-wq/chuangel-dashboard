$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime = Join-Path $root "runtime"
$node = "C:\Users\w4245\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
$cloudflared = Join-Path $runtime "cloudflared.exe"
$tunnelLog = Join-Path $runtime "tunnel.log"
$processFile = Join-Path $runtime "processes.json"

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
if (-not (Test-Path -LiteralPath $node)) { throw "Node runtime not found" }
if (-not (Test-Path -LiteralPath $cloudflared)) { throw "cloudflared not found" }

function Start-HiddenProcess([string]$filePath, [string]$arguments, [string]$workingDirectory) {
  $info = New-Object System.Diagnostics.ProcessStartInfo
  $info.FileName = $filePath
  $info.Arguments = $arguments
  $info.WorkingDirectory = $workingDirectory
  $info.UseShellExecute = $false
  $info.CreateNoWindow = $true
  $info.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
  return [System.Diagnostics.Process]::Start($info)
}

$server = Start-HiddenProcess $node 'server.mjs' $root
Start-Sleep -Seconds 1
$tunnelArguments = "tunnel --url http://127.0.0.1:8766 --no-autoupdate --logfile `"$tunnelLog`" --loglevel info"
$tunnel = Start-HiddenProcess $cloudflared $tunnelArguments $root

@{
  serverPid = $server.Id
  tunnelPid = $tunnel.Id
  startedAt = (Get-Date).ToString("s")
} | ConvertTo-Json | Set-Content -LiteralPath $processFile -Encoding UTF8

Write-Output "server=$($server.Id) tunnel=$($tunnel.Id)"
