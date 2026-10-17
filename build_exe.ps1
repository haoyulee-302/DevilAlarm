$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv-alarm\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Run setup.ps1 first.' }
& $pythonExe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install build tools.' }
& $pythonExe make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Could not generate the application icon.' }
& $pythonExe -m PyInstaller --noconfirm DevilAlarm.spec
if ($LASTEXITCODE -ne 0) { throw 'EXE build failed.' }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'README.md') -Destination (Join-Path $PSScriptRoot 'dist\README.md')
Write-Host 'EXE ready: dist\DevilAlarm.exe' -ForegroundColor Green
