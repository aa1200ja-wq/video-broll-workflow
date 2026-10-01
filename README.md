# B-roll Workflow

本機執行的「網頁 UI + 背景服務」講解影片粗剪工具。

最終用途不是自動完成精剪，而是把：

**旁白腳本 → Scene → 配音時間碼 → 搜素材 → 選素材 → 素材庫 → 粗剪預覽 → 剪映草稿**

一次串起來。

## 使用者看到的東西

啟動後只會開一個自適應網頁介面：

- 電腦版：側欄專案 + 完整工作區
- 窄螢幕／手機寬度：自動改成單欄
- 不需要操作 Python、Node.js、FFmpeg、npm 或 pip

### 正式 Windows 版

GitHub Actions 會自動產生：

`BrollWorkflow-Windows.zip`

解壓縮後直接執行：

`BrollWorkflow.exe`

正式打包版已包含 Python Runtime 所需套件與 FFmpeg，不要求使用者另外安裝 Node.js 或 FFmpeg。

### 原始碼開發版

也可以下載原始碼後雙擊：

`START_HERE.cmd`

開發版只需要 Python 3.11；若電腦沒有 Python 且有 winget，啟動器會嘗試自動安裝。

## 完整流程

1. 建立專案。
2. 一次貼完整旁白稿。
3. 依標點切成 Scene，可手動拆分／合併。
4. Edge-TTS 逐 Scene 產生旁白，依 MP3 實際長度建立時間碼與 SRT。
5. 一次貼整批素材搜尋詞，每行自動對應一個 Scene。
6. 一鍵平行搜尋 Pexels、Pixabay、Wikimedia Commons。
7. 每個 Scene 人工挑選候選素材，也可單幕重搜或上傳自己的素材。
8. 已下載／上傳素材進入專案素材庫，保留搜尋詞、來源標籤、作者與來源網址。
9. 素材庫可重新搜尋，同一支檔案可以指定給任意 Scene，不重複下載。
10. 產生 1920×1080 粗剪 MP4 供快速檢查。
11. 建立剪映草稿，包含 `main_video`、`narration`、`caption` 三軌。

## 素材來源設定

在網頁「設定」頁直接填：

- Pexels API Key
- Pixabay API Key

Wikimedia Commons 不需要 Key。

Key 只保存在這台電腦的本機資料目錄，不進 GitHub。

Pexels 與 Pixabay 的候選素材介面會保留來源資訊；正式使用仍應遵守各來源平台的 API 與內容授權規範。

## 剪映設定

在「設定」頁按「自動偵測」尋找常見剪映草稿位置；若找不到，可從：

**剪映 → 全域設定 → 草稿位置**

複製資料夾路徑貼入。

目前目標版本：**剪映專業版 6.0.1**。

建立草稿後若剪映首頁沒有立即刷新，可重新進出草稿或重啟剪映。

## 本機資料

Windows 預設放在：

`%LOCALAPPDATA%\BrollWorkflow`

其中包含：

```text
BrollWorkflow/
├─ .env
└─ projects/
   └─ <project-id>/
      ├─ project.json
      ├─ script.txt
      ├─ library.json
      ├─ audio/
      ├─ assets/
      ├─ subtitles/
      └─ exports/
```

素材檔只保存一份；Scene 只引用素材路徑。

## 技術結構

- UI：原生 HTML / CSS / JavaScript，不需要前端編譯器
- 本機服務：FastAPI / Python
- 配音：Edge-TTS
- 素材：Pexels / Pixabay / Wikimedia Commons
- 媒體：內建 imageio-ffmpeg runtime
- MP3 時長：mutagen
- 剪映草稿：pyJianYingDraft
- Windows 封裝：PyInstaller
- 專案資料：JSON + 本機檔案

## V1 原則

- 不使用 GPT、Claude、Ollama、OpenCLIP 等 AI 模型。
- 不自動判斷哪個素材最好，由使用者人工選。
- 搜尋詞由使用者提供。
- 粗剪 MP4 只是預覽；主要輸出是可繼續編輯的剪映草稿。
