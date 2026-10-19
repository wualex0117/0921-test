# LINE AI 隨身好友「小光」- 智慧即時連網助理 🚀

本專案實作了一套兼具 **Google Apps Script 雲端 24H 伺服器** 與 **本地端轉接站 (Relay Station)** 的 LINE AI 聊天機器人。整合了 Google Gemini 最新大語言模型，並具備即時網路搜尋與資訊來源附帶功能。

---

## 🛠️ 一、怎麼裝 (Installation)

### 1. 環境需求
* Python 3.9+ 
* 依賴套件（本地轉接站使用）：
```bash
pip install fastapi uvicorn[standard] httpx
```

### 2. 金鑰準備
* **Google Gemini API Key**：至 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請。
* **LINE Messaging API Token**：至 [LINE Developers Console](https://developers.line.biz/) 取得 Channel Access Token。

---

## 🚀 二、怎麼跑 (How to Run)

本專案提供兩種運行架構：

### 架構 A：Google Apps Script 雲端 24H 模式（免開電腦）
1. 進入 [Google Apps Script](https://script.google.com/) 建立新專案。
2. 將本倉庫的 [`Code.gs`](./Code.gs) 程式碼完整複製並貼入編輯器中。
3. 填入 `CONFIG` 中的 `CHANNEL_ACCESS_TOKEN` 與 `GEMINI_API_KEY`。
4. 點選 **「部署」➔「新增部署」➔ 選擇「網頁應用程式」**：
   * 執行身分：`我`
   * 誰可以存取：`所有人 (Anyone)`
5. 將生成的 Web App 網址貼回 LINE Developers 的 **Webhook URL** 並開啟 **Use Webhook** 即可全天候自動運作！

### 架構 B：本地端轉接站監控模式 (Relay Station)
1. 在終端機啟動轉接站伺服器：
   ```bash
   python bot.py
   ```
2. （或執行即時模擬測試，供終端機日誌查驗與截圖）：
   ```bash
   python bot.py --simulate
   ```
3. 搭配 `ngrok http 8000` 將本地端暴露至外網，亦可直接作為 LINE Webhook 本地中繼站。

---

## 📝 三、你改了什麼 (Changelog & Technical Improvements)

在開發與除錯過程中，完成了以下重大架構重構與優化：

### 1. 模型遷移與適配 (`gemini-3.8-flash`)
* **原狀況**：原本設定之舊版模型 (`gemini-2.0-flash` / `gemini-2.5-flash`) 因 Google 官方接口異動報出 `404 NOT_FOUND` 錯誤。
* **修改後**：全面遷移至官方現行最新標準模型 **`gemini-3.8-flash`**，確保對話接口穩定回應。

### 2. 解決 Google Search 429 配額卡住問題（自建免信用卡連網搜尋引擎）
* **原狀況**：開啟官方原生 `tools: [{googleSearch:{}}]` 時，未綁定信用卡的免費帳號會直接觸發 `429 RESOURCE_EXHAUSTED (You exceeded your current quota)` 導致機器人中斷當機。
* **修改後**：自研了輕量級即時抓取架構，利用 Google 新聞 RSS 與維基百科 OpenSearch API，在背景即時抓取最新時事快訊注入 Prompt，**徹底避開 429 配額限制，實現 100% 免費即時上網搜尋**。

### 3. 明確標註資訊來源 (Source Citation)
* **修改後**：在系統提示詞中強制要求模型在查閱最新網路快訊後，必須於回覆末端附上【資訊來源】，提升事實可信度。

### 4. 雙軌架構整合
* 提供雲端零主機成本運行的 `Code.gs` 與具備終端機即時通訊日誌監控的 `bot.py`，完整兼顧 24H 穩定度與本地端可觀測性。
