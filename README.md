# 惡魔鬧鐘 · Devil Alarm

結合攝影機姿勢辨識與 AI 吐槽語音的 Windows 桌面鬧鐘。響鈴後，讓肩膀、臀部與膝蓋完整入鏡，站直持續指定秒數即可完成起床挑戰。

## 原型示範

- [觀看／下載早期原型影片（MP4）](https://github.com/haoyulee-302/DevilAlarm/releases/download/v1.0.0/DevilAlarm-prototype-demo.mp4)

影片使用舊介面，展示原型的攝影機骨架辨識與解鎖流程，也暴露需要使用新版重測的疑似坐姿誤判；它不是目前 v1.0.0 EXE 的完整驗證。

## 後續功能與維護計畫

以下為規劃項目，尚未全部實作，會依問題重現結果與實際測試逐步調整。

| 優先順序 | 功能改善 | 驗收方向 |
| --- | --- | --- |
| P0 | 改善坐姿誤判，結合關節角度、可見度與連續幀判斷 | 比較站姿通過率與非站姿誤放率，附測試案例數與限制 |
| P0 | 取景校準、光線與關鍵部位提示 | 遮擋、過近或離開畫面時給出清楚提示，避免誤累積解鎖時間 |
| P0 | 攝影機中斷、配音失敗與網路錯誤的恢復流程 | 驗證提示、重試、取消與資源釋放行為 |
| P1 | 明確離線模式、語音快取狀態及攝影機偵測 | 離線模式不發出雲端請求，記錄實測裝置與解析度 |
| P1 | 星期、多組排程及恢復運作後的時間處理 | 覆蓋跨日、取消、衝突及恢復運作情境，保留關機無法響鈴的限制 |
| P2 | 替代解除動作、難度調整與鍵盤操作 | 為不同動作建立獨立規則及測試，改善不同活動能力與取景條件下的操作 |
| P2 | 分離姿勢、排程及語音介面，補充中英文範例 | 提供容易測試及替換的小型模組，方便其他 Python 桌面工具與教學專案參考 |

持續維護工作包括：

- 對確認的問題保留最小重現方式與回歸測試；公開合成骨架案例與標註規則，真實影片由測試者自行決定是否分享。
- 建立 Windows CI、依賴版本紀錄及 EXE 自我檢查，發布時核對版本、模型、音效與校驗碼。
- 整理 MediaPipe、Tk 高 DPI、TTS 及 PyInstaller 的整合與故障排查經驗，降低相似專案重複排錯的成本。
- 補齊維護者選定的專案授權、第三方素材說明、問題回報格式與貢獻文件。
- 程式修改經人工審核及測試後再合併；每次發布記錄驗證範圍、變更與已知限制。

## EXE 快速開始

[下載 Windows EXE／ZIP](https://github.com/haoyulee-302/DevilAlarm/releases/latest)

1. 解壓縮 `DevilAlarm-Windows-x64.zip`。
2. 雙擊 `DevilAlarm.exe`，不需要另外安裝 Python。
3. 選擇攝影機編號，點「測試攝影機」確認取景。
4. 停止預覽，設定時間、音量與站姿秒數，再點「啟動鬧鐘」。

目標平台：Windows 10／11、64 位元。需有攝影機與音訊輸出裝置。EXE 包含 Python、MediaPipe 模型、提示音及三段備用配音；啟動時須解開資源，請稍候。

`dist/DevilAlarm.exe` 是單檔版本，可獨立複製使用。發布 ZIP 另附本說明及 `SHA256SUMS.txt`。

## 功能與操作

| 功能 | 操作說明 |
| --- | --- |
| 鬧鐘排程 | 24 小時制；已過的時間排到明天，一次設定一個鬧鐘 |
| 站姿解鎖 | 選擇站直持續 2、3 或 5 秒，畫面顯示骨架及進度 |
| 攝影機預覽 | 先測試取景，停止預覽後再啟動排程 |
| 音量 | 可調整提示音及語音音量 |
| AI 吐槽 | 三段漸進語氣的台詞，搭配 Edge TTS 台灣中文配音 |
| Gemini | API Key 選填，嘗試生成新的台詞 |
| 高 DPI | 原生像素字體與隨螢幕 DPI 調整的間距 |

### 攝影機與 iVCam

一般攝影機先試編號 `0`，再試 `1`、`2`。使用 iVCam 時，先在手機及電腦端完成連線，再選對應編號。確認肩膀、臀部與膝蓋完整入鏡，保持足夠光線。

程式會嘗試取得 1280×720 影像，實際解析度依攝影機或 iVCam 設定決定。預覽使用等比例高品質縮放。

### 排程與解除

點「啟動鬧鐘」後立即排程，語音在背景準備，不會延後倒數。到時站直，保持指定秒數即可停止；姿勢不符合或離開畫面時，連續計時歸零。

- 尚未響起時可點「取消排程」。
- 響鈴時可點「停止鬧鐘」或按 `Q` 手動中止。
- 關閉程式會取消排程，重新啟動後需重新設定。
- 程式與電腦必須保持開啟。睡眠、關機時不會響鈴，也不會自動喚醒電腦；若恢復運作時已超過排定時間，程式再次檢查時會觸發。

### 語音與網路

- 關閉語音：只播放提示音。
- 開啟語音、Key 留白：從本機台詞庫選取文字，再嘗試使用 Edge TTS 配音。
- 填入 Gemini Key：嘗試由 Gemini 生成台詞，再以 Edge TTS 配音。

Gemini 與 Edge TTS 均需要網路。失敗時使用內建台詞或打包的備用 MP3；沒有可用語音時仍播放提示音。提示音約每 10 秒穿插一段語音，共三段，之後持續播放提示音。

## 設定與隱私

| 資料 | 位置或處理方式 |
| --- | --- |
| EXE 偏好設定 | `%LOCALAPPDATA%\DevilAlarm\settings.json` |
| EXE 啟動錯誤 | `%LOCALAPPDATA%\DevilAlarm\startup-error.log`，僅啟動失敗時建立 |
| 原始碼偏好設定 | 專案內的 `settings.json` |
| 攝影機影像 | 只在本機處理，不錄影、儲存或上傳 |
| Gemini Key | 僅保留在當次執行的記憶體，傳送到 Google Gemini API |
| Gemini 請求 | 傳送台詞生成提示，不傳送影像 |
| Edge TTS 請求 | 傳送配音文字，不傳送影像 |
| 新生成配音 | 系統暫存資料夾，正常結束任務時嘗試清理 |

偏好包含攝影機、音量、站姿秒數與語音開關，不包含鬧鐘時間或金鑰。舊 `api_key.txt` 不再讀取、寫入，也不包含於發布檔案。

## 常見問題

**攝影機無法開啟或黑畫面**：先確認系統或 iVCam 本身能顯示影像，關閉可能占用鏡頭的程式，再試其他編號。使用手機時確認兩端仍保持連線。

**站直卻無法解鎖**：後退一些，讓肩膀、臀部、膝蓋全部入鏡，改善光線並避免遮擋。判斷使用二維啟發式規則，受取景影響，無法保證排除所有坐姿或誤判。

**沒有 AI 語音或台詞沒有更新**：檢查語音開關、網路及 Key。服務失敗時使用備用配音，提示音仍會照常播放。

**裝置錯誤後鬧鐘停止**：目前版本會停止任務並顯示錯誤。確認攝影機與音訊裝置可用，再重新排程。正式使用前，建議先以一分鐘後的時間測試完整流程。

**字體仍模糊**：退出舊視窗，再開本次打包的 EXE。高 DPI 模式在建立視窗前啟用，舊視窗不會自動更新。影像畫質另受攝影機輸出解析度與光線限制。

**EXE 無法啟動**：查看上述 `startup-error.log`；沒有記錄時，保留 Windows 顯示的錯誤訊息供排查。

## 從原始碼執行

需要 Windows 64 位元 Python 3.12 或 3.11，在專案資料夾執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

安裝工具建立 `.venv-alarm`，保留舊 `.venv`。該 ExecutionPolicy 參數只套用於本次程序。若本機有 Codex 隨附 Python，可作為建立環境的備用來源；該 Python 日後被移除時需重建環境。

完成後雙擊 `start.bat`，或執行：

```powershell
.\.venv-alarm\Scripts\python.exe main.py
```

## 重新打包 EXE

先完成原始碼環境安裝，再執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

輸出為 `dist\DevilAlarm.exe`。建置工具會產生多尺寸圖示，收集模型、DLL 與音效，建立無命令列視窗的單檔 EXE。資源使用明確清單，不包含 API Key、個人設定、虛擬環境及備份。建置工具版本記錄於 `requirements-build.txt`。

打包參考：[PyInstaller 使用文件](https://www.pyinstaller.org/en/stable/usage.html)、[執行期資源路徑](https://www.pyinstaller.org/en/stable/runtime-information.html)。

## 驗證

不開鏡頭、不播放聲音的自動測試：

```powershell
.\.venv-alarm\Scripts\python.exe -m unittest test_alarm -v
```

EXE 離線自我檢查（會短暫建立介面並載入模型，不開鏡頭、不播放聲音、不連線）：

```powershell
Start-Process -FilePath .\dist\DevilAlarm.exe -ArgumentList '--self-test', 'self-test.json' -Wait
Get-Content .\self-test.json
```

自我檢查涵蓋介面、DPI、Pillow、OpenCV、姿勢模型、WAV／MP3 解碼、語音參數及設定路徑；不代表已驗證真實攝影機、實際站姿或線上 Gemini／TTS 服務。

## 專案檔案

| 檔案 | 用途 |
| --- | --- |
| `main.py` | 介面、排程、姿勢與音訊任務 |
| `display.py` | 高 DPI 字體與版面縮放 |
| `app_paths.py` | 資源及使用者設定路徑 |
| `launcher.py` | EXE 入口、錯誤記錄及自我檢查 |
| `generate_alarm.py` | 提示音生成工具 |
| `alarm.wav`、`roast_*.mp3` | 提示音及備用配音 |
| `app.ico`、`make_icon.py` | 應用圖示與生成工具 |
| `requirements.txt`、`requirements-build.txt` | 執行與建置依賴 |
| `setup.ps1`、`start.bat` | 原始碼安裝與啟動 |
| `DevilAlarm.spec`、`build_exe.ps1` | EXE 打包設定與工具 |
| `test_alarm.py` | 排程、狀態及顯示回歸測試 |
