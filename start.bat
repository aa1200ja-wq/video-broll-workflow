@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo 尚未安裝，先執行 setup.bat
  pause
  exit /b 1
)
if not exist apps\web\node_modules (
  echo 前端套件尚未安裝，先執行 setup.bat
  pause
  exit /b 1
)
start "B-roll Server" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/server --host 127.0.0.1 --port 8000"
start "B-roll Web" cmd /k "cd /d %~dp0apps\web && npm run dev"
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:5173
