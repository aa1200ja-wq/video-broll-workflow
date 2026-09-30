# V1 測試狀態

已完成：

- Python 語法編譯通過。
- 腳本依標點切 Scene 測試通過。
- 專案 JSON 保存／讀取通過。
- 缺素材時 FFmpeg 產生佔位粗剪通過。
- FastAPI `/api/health`、建立專案、寫入腳本、無 Key 搜尋降級行為通過。
- 所有 `.py`、`.ts`、`.vue`、`.css` 檔案均未超過 250 行。
- V1 程式碼已上傳至 GitHub：`aa1200ja-wq/video-broll-workflow`。
- GitHub Actions 後端測試通過：2 tests passed。
- GitHub Actions 前端 Vue／TypeScript 建置通過。
- 批次搜尋已改成「一次貼搜尋詞 → 一鍵套用並搜尋全部 Scene」。

仍需在 Windows 本機使用 `START_HERE.cmd` 驗證：

- Edge-TTS 實際配音。
- Pexels / Pixabay 實際 API Key 搜尋與下載。
- Wikimedia 實際搜尋與下載。
- `pyJianYingDraft` 對剪映專業版 6.0.1 的草稿開啟結果。
- Windows 實機啟動後的完整操作流程。
