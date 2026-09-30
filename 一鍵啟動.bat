@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title B-roll Workflow 一鍵啟動

echo ========================================
echo B-roll Workflow
echo 一鍵安裝 / 啟動
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo [錯誤] 找不到 Python。
    echo 請先安裝 Python 3.11，安裝時勾選 Add Python to PATH。
    pause
    exit /b 1
  )
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [錯誤] 找不到 Node.js / npm。
  echo 請先安裝 Node.js LTS。
  pause
  exit /b 1
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo [錯誤] 找不到 FFmpeg。
  echo 請先安裝 FFmpeg 並加入 PATH。
  pause
  exit /b 1
)

if not exist .env (
  echo [初始化] 建立本機設定檔...
  (
    echo PEXELS_API_KEY=
    echo PIXABAY_API_KEY=
    echo PROJECTS_DIR=./projects
    echo DEFAULT_VOICE=zh-TW-YunJheNeural
  )>.env
)

if not exist .venv\Scripts\python.exe (
  echo [第一次使用] 建立 Python 環境...
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3.11 -m venv .venv 2>nul
    if errorlevel 1 py -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 goto :error
)

.venv\Scripts\python.exe -c "import fastapi,uvicorn,httpx,edge_tts" >nul 2>nul
if errorlevel 1 (
  echo [第一次使用] 安裝後端套件，請稍候...
  .venv\Scripts\python.exe -m pip install -U pip
  if errorlevel 1 goto :error
  .venv\Scripts\python.exe -m pip install -r apps\server\requirements.txt
  if errorlevel 1 goto :error
)

if not exist apps\web\node_modules (
  echo [第一次使用] 安裝前端套件，請稍候...
  pushd apps\web
  call npm install
  if errorlevel 1 (
    popd
    goto :error
  )
  popd
)

echo.
echo [啟動] 後端服務...
start "B-roll Workflow Server" /min cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --app-dir apps/server --host 127.0.0.1 --port 8000"

echo [啟動] 操作介面...
start "B-roll Workflow Web" /min cmd /k "cd /d %~dp0apps\web && npm run dev"

echo [啟動] 等待服務...
timeout /t 4 /nobreak >nul
start "" http://127.0.0.1:5173

echo.
echo ========================================
echo 已啟動。
echo 瀏覽器網址：http://127.0.0.1:5173
echo.
echo Pexels / Pixabay 的 Key 之後再填 .env 即可，
echo 沒填也可以先使用 Wikimedia 與本機素材。
echo ========================================
timeout /t 3 /nobreak >nul
exit /b 0

:error
echo.
echo ========================================
echo 啟動失敗。
echo 請不要關閉這個視窗，直接截圖最後的錯誤給小周。
echo ========================================
pause
exit /b 1
