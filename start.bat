@echo off
cd /d "%~dp0"
if not exist ".venv-alarm\Scripts\python.exe" (
  echo First run: right-click setup.ps1 and select Run with PowerShell.
  pause
  exit /b 1
)
".venv-alarm\Scripts\python.exe" main.py
if errorlevel 1 pause
