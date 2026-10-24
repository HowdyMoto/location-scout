@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo First run: python -m venv .venv
  echo Then: .venv\Scripts\python.exe -m pip install -r scout/requirements.txt
  pause
  exit /b 1
)
.venv\Scripts\python.exe scout/server.py %*
