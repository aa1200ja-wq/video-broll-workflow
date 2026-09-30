@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title B-roll Workflow

echo ========================================
echo B-roll Workflow - START
echo ========================================
echo.
echo Current folder:
echo %CD%
echo.

where py >nul 2>nul
if not errorlevel 1 (
  set "PY=py"
) else (
  where python >nul 2>nul
  if errorlevel 1 goto :no_python
  set "PY=python"
)

where npm >nul 2>nul
if errorlevel 1 goto :no_node

if not exist .env (
  echo Creating local config...
  >.env echo PEXELS_API_KEY=
  >>.env echo PIXABAY_API_KEY=
  >>.env echo PROJECTS_DIR=./projects
  >>.env echo DEFAULT_VOICE=zh-TW-YunJheNeural
)

if not exist .venv\Scripts\python.exe (
  echo [1/4] Creating Python environment...
  %PY% -m venv .venv
  if errorlevel 1 goto :failed
)

echo [2/4] Checking Python packages...
.venv\Scripts\python.exe -c "import fastapi,uvicorn,httpx,edge_tts" >nul 2>nul
if errorlevel 1 (
  echo Installing Python packages...
  .venv\Scripts\python.exe -m pip install -U pip
  if errorlevel 1 goto :failed
  .venv\Scripts\python.exe -m pip install -r apps\server\requirements.txt
  if errorlevel 1 goto :failed
)

echo [3/4] Checking web packages...
if not exist apps\web\node_modules (
  pushd apps\web
  call npm install
  if errorlevel 1 (
    popd
    goto :failed
  )
  popd
)

echo [4/4] Starting...
start "B-roll Server" cmd /k "cd /d "%CD%" && .venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/server --host 127.0.0.1 --port 8000"
start "B-roll Web" cmd /k "cd /d "%CD%\apps\web" && npm run dev"

timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5173"

echo.
echo Tool started: http://127.0.0.1:5173
echo You can close this launcher window.
timeout /t 3 /nobreak >nul
exit /b 0

:no_python
echo.
echo ERROR: Python was not found.
echo Install Python 3.11 and enable Add Python to PATH.
goto :hold

:no_node
echo.
echo ERROR: Node.js/npm was not found.
echo Install Node.js LTS.
goto :hold

:failed
echo.
echo ERROR: Setup or startup failed.
echo Take a screenshot of the lines above and send it back.
goto :hold

:hold
echo.
pause
exit /b 1
