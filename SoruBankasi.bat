@echo off
setlocal
cd /d "%~dp0"

set "APP=%~dp0app.py"
set "LOG=%~dp0run.log"
set "PYTHONW="
set "PYTHON="
set "PYLAUNCHER="

if not exist "%APP%" (
  echo app.py bulunamadi. Lutfen bu .bat dosyasini proje klasorunde calistirin.
  pause
  exit /b 1
)

if exist ".venv\Scripts\pythonw.exe" set "PYTHONW=%~dp0.venv\Scripts\pythonw.exe"
if exist ".venv\Scripts\python.exe" set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not defined PYTHONW (
  for /f "delims=" %%P in ('where pythonw 2^>nul') do if not defined PYTHONW set "PYTHONW=%%P"
)
if not defined PYTHON (
  for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON set "PYTHON=%%P"
)
if not defined PYLAUNCHER (
  for /f "delims=" %%P in ('where py 2^>nul') do if not defined PYLAUNCHER set "PYLAUNCHER=%%P"
)

if defined PYTHONW (
  "%PYTHONW%" "%APP%" > "%LOG%" 2>&1
  if errorlevel 1 (
    echo Uygulama baslayamadi. Hata gunlugu aciliyor: %LOG%
    notepad "%LOG%"
    pause
  )
  exit /b 0
)

if defined PYTHON (
  "%PYTHON%" "%APP%"
  if errorlevel 1 pause
  exit /b 0
)

if defined PYLAUNCHER (
  "%PYLAUNCHER%" -3 "%APP%"
  if errorlevel 1 pause
  exit /b 0
)

echo Python bulunamadi. Lutfen Python 3.11+ yukleyin.
pause
exit /b 1
