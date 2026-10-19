# LINE AI 隨身好友「小光」✨

一個支援雙模式（**純本地端離線大模型 Ollama** 與 **Google Gemini 雲端 API**）的 LINE AI 聊天機器人。內建本地 Web 測試頁面與終端機 CLI 互動模式，不需要等待 LINE Webhook 即可直接測試！

## 🌟 功能亮點
- **文字多輪對話**：具備上下文記憶與親切自然的朋友語氣。
- **本地離線支援**：預設採用 Ollama 本地模型（如 `llama3.2`、`llama3.2-vision`），完全免 API Key 與網路離線可用。
- **圖片辨識**：支援美食、筆記、發票與生活照片分析。
- **網址速讀**：自動萃取網頁 3 點必讀精華與結論。
- **免 Webhook 本地測試**：開啟瀏覽器 `http://localhost:8000` 即可直接測試對話。

## 🚀 快速開始

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 啟動本地 Ollama 模型
```bash
# 啟動文字對話模型
ollama run llama3.2

# (可選) 若需要測試本地圖片辨識：
ollama pull llama3.2-vision
```

### 3. 啟動服務
```bash
# 啟動 Web 測試平台與 LINE Webhook 伺服器
python bot.py

# 或使用終端機直接對話：
python bot.py --cli
```
啟動後打開瀏覽器訪問 `http://localhost:8000` 即可開始聊天！
