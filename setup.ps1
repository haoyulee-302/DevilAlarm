$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv-alarm\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    $runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $created = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv .venv-alarm
        $created = $LASTEXITCODE -eq 0
        if (-not $created) {
            & py -3.11 -m venv .venv-alarm
            $created = $LASTEXITCODE -eq 0
        }
    }
    if (-not $created -and (Test-Path -LiteralPath $runtimePython)) {
        & $runtimePython -m venv .venv-alarm
        $created = $LASTEXITCODE -eq 0
    }
    if (-not $created) { throw 'Install Python 3.12 (64-bit), then run setup.ps1 again.' }
}
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your network and retry setup.ps1.' }
Write-Host 'Ready. Double-click start.bat to launch Devil Alarm.' -ForegroundColor Green
