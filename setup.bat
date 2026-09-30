@echo off
setlocal
cd /d "%~dp0"
if not exist .env copy .env.example .env >nul

where py >nul 2>nul
if %errorlevel%==0 (
  py -3.11 -c "import sys" >nul 2>nul
  if %errorlevel%==0 (set PY=py -3.11) else (set PY=python)
) else (
  set PY=python
)

if not exist .venv (
  echo [1/4] 建立 Python 虛擬環境...
  %PY% -m venv .venv || exit /b 1
)
echo [2/4] 安裝 Python 套件...
.venv\Scripts\python.exe -m pip install -U pip
.venv\Scripts\python.exe -m pip install -r apps\server\requirements.txt || exit /b 1

echo [3/4] 安裝前端套件...
cd apps\web
call npm install || exit /b 1
cd ..\..

echo [4/4] 完成。
echo 請編輯 .env 填入 PEXELS_API_KEY / PIXABAY_API_KEY，再雙擊 start.bat。
pause
