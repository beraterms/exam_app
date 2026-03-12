@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
  ".venv\Scripts\pythonw.exe" "app.py"
  exit /b 0
)

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "app.py"
  exit /b 0
)

if exist "C:\Python311\pythonw.exe" (
  "C:\Python311\pythonw.exe" "app.py"
  exit /b 0
)

pythonw app.py
exit /b 0
