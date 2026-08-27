# 传天羽经营看板 · 登录系统部署脚本（Windows Server 2022）
$ErrorActionPreference = 'Stop'
$dst = 'C:\dashapp'
Write-Output '== 1/4 检查 Python =='
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
  $installer = "$env:TEMP\python-3.12.7-amd64.exe"
  Write-Output '下载 Python 3.12.7 ...'
  Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile $installer -UseBasicParsing
  Write-Output '静默安装 Python ...'
  Start-Process -Wait -FilePath $installer -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 Include_test=0'
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
} else { Write-Output 'Python 已存在' }
python --version
Write-Output '== 2/4 防火墙放行 8003 =='
netsh advfirewall firewall delete rule name='dash-login-8003' | Out-Null
netsh advfirewall firewall add rule name='dash-login-8003' dir=in action=allow protocol=TCP localport=8003
Write-Output '== 3/4 启动应用（后台） =='
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Set-Location $dst
Start-Process -WindowStyle Hidden -FilePath 'python' -ArgumentList 'app.py' -WorkingDirectory $dst
Start-Sleep -Seconds 3
try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8003/' -UseBasicParsing -TimeoutSec 8; Write-Output ('本地检查 HTTP ' + $r.StatusCode) } catch { Write-Output ('本地检查失败: ' + $_.Exception.Message) }
Write-Output '== 4/4 开机自启（计划任务） =='
schtasks /Create /F /TN 'DashApp8003' /TR "powershell -NoProfile -WindowStyle Hidden -Command \"Set-Location C:\dashapp; python app.py\"" /SC ONSTART
Write-Output '== 部署完成 =='