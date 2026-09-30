@echo off
setlocal
cd /d "%~dp0"

if not exist .env (
  echo PEXELS_API_KEY=>.env
  echo PIXABAY_API_KEY=>>.env
  echo PROJECTS_DIR=./projects>>.env
  echo DEFAULT_VOICE=zh-TW-YunJheNeural>>.env
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3.11 -c "import sys" >nul 2>nul
  if %errorlevel%==0 (set PY=py -3.11) else (set PY=python)
) else (
  set PY=python
)

if not exist .venv (
  echo [1/4] Creating Python virtual environment...
  %PY% -m venv .venv || goto :error
)

echo [2/4] Installing Python packages...
.venv\Scripts\python.exe -m pip install -U pip || goto :error
.venv\Scripts\python.exe -m pip install -r apps\server\requirements.txt || goto :error

echo [3/4] Installing web packages...
cd apps\web
call npm install || goto :error
cd ..\..

echo [4/4] Setup complete.
echo Edit .env with your PEXELS_API_KEY / PIXABAY_API_KEY, then run start.bat.
pause
exit /b 0

:error
echo.
echo Setup failed. Please take a screenshot of this window and send it back.
pause
exit /b 1
