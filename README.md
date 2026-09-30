# B-roll Workflow MVP

無 AI 模型的旁白驅動素材搜尋與粗剪工具。

## V1 流程

1. 建立專案並貼入旁白稿。
2. 依標點自動切成 Scene，可手動拆分或合併。
3. Edge-TTS 逐 Scene 配音，依實際音檔長度建立時間碼與 SRT。
4. 一次貼入整批素材搜尋詞，每行自動對應一個 Scene。
5. 按一次「套用並搜尋全部素材」，同時搜尋 Pexels、Pixabay、Wikimedia Commons。
6. 每個 Scene 顯示候選素材，可人工挑選、單幕重搜，或加入自己的圖片／影片。
7. 選過或上傳過的素材會進入「專案素材庫」，檔案只存一份，並保留搜尋詞、來源標籤、作者與來源網址。
8. 素材庫可重新搜尋，並把同一支素材指定給其他 Scene，不需再次下載。
9. FFmpeg 依 Scene 長度產生 1920×1080 粗剪預覽。
10. 透過 pyJianYingDraft 建立剪映草稿，繼續人工剪輯。

## 安裝（Windows）

需求：Python 3.11 優先、Node.js、FFmpeg、剪映專業版 6.0.1。

1. 下載 ZIP 並解壓縮。
2. 雙擊 `START_HERE.cmd`。
3. 若要使用 Pexels／Pixabay，編輯根目錄 `.env`：

```env
PEXELS_API_KEY=你的Key
PIXABAY_API_KEY=你的Key
PROJECTS_DIR=./projects
DEFAULT_VOICE=zh-TW-YunJheNeural
```

4. 工具會開在 `http://127.0.0.1:5173`。

Pexels／Pixabay Key 都只存在本機 `.env`，`.env` 已加入 `.gitignore`。
Wikimedia Commons 不需要 Key。

## 操作重點

- 重新「依標點切 Scene」會重建 Scene；正式搜尋素材前先把 Scene 拆分／合併調整好。
- 素材搜尋詞可一次貼上，每行依序對應 Scene 1、2、3……。
- 可按一次「套用並搜尋全部素材」批次取得所有 Scene 的候選素材。
- 配音後才有精準的 Scene 起訖時間。
- 每幕候選素材由人選，不做 AI 排名。
- 缺少的畫面可在其他工具自行生成，再用「加入自己的素材」拖入。
- 粗剪缺素材時會用深灰畫面佔位，不阻止預覽輸出。

## 剪映

V1 使用 `pyJianYingDraft` 建立新草稿，不讀取既有模板。輸出軌道：

- `main_video`：各 Scene 畫面
- `narration`：完整旁白
- `caption`：Scene 字幕

第一次輸出時，在畫面填入剪映「全域設定 → 草稿位置」顯示的資料夾路徑。

## 專案資料

執行後資料放在 `projects/`，此目錄不會進 Git：

```text
projects/<project-id>/
├─ project.json
├─ script.txt
├─ audio/
├─ assets/
├─ library.json
├─ subtitles/
└─ exports/
```

## API

FastAPI 文件：`http://127.0.0.1:8000/docs`

## 已知 V1 限制

- 搜尋詞由使用者自己輸入。
- 不自動判斷素材好壞。
- Pixabay 預覽縮圖偶爾會因來源端限制顯示失敗，但下載 URL 不受影響。
- Edge-TTS 需要網路連線。
- 剪映草稿輸出針對目前使用的剪映專業版 6.0.1；若日後升版，只需更換 exporter。
