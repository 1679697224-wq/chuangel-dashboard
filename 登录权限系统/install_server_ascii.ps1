# Dash Login System - Windows Server install script (ASCII only)
$ErrorActionPreference = 'Stop'
$dst = 'C:\dashapp'
Write-Output '== 1/4 Check Python =='
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
  $installer = "$env:TEMP\python-3.12.7-amd64.exe"
  Write-Output 'Downloading Python 3.12.7 ...'
  Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile $installer -UseBasicParsing
  Write-Output 'Installing Python silently ...'
  Start-Process -Wait -FilePath $installer -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 Include_test=0'
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
} else { Write-Output 'Python already exists' }
python --version
Write-Output '== 2/4 Firewall 8003 =='
netsh advfirewall firewall delete rule name='dash-login-8003' | Out-Null
netsh advfirewall firewall add rule name='dash-login-8003' dir=in action=allow protocol=TCP localport=8003
Write-Output '== 3/4 Start app =='
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Set-Location $dst
Start-Process -WindowStyle Hidden -FilePath 'python' -ArgumentList 'app.py' -WorkingDirectory $dst
Start-Sleep -Seconds 3
try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8003/' -UseBasicParsing -TimeoutSec 8; Write-Output ('Local check HTTP ' + $r.StatusCode) } catch { Write-Output ('Local check FAIL: ' + $_.Exception.Message) }
Write-Output '== 4/4 Auto-start task =='
schtasks /Create /F /TN 'DashApp8003' /TR "powershell -NoProfile -WindowStyle Hidden -Command \"Set-Location C:\dashapp; python app.py\"" /SC ONSTART
Write-Output '== DONE =='