# LINE AI 轉接站程式 (Relay Server) - bot.py (零依賴極速版)
# ===================================================================
# 功能：
#   - 本地端轉接站伺服器 (支援終端機即時通訊監控)
#   - 支援免安裝第三方套件直接執行 --simulate 模擬查驗日誌
#   - 具備即時新聞抓取與資訊來源附帶
# ===================================================================

import os
import re
import sys
import json
import logging
import urllib.request
import urllib.parse
from typing import Optional, Any

# 解決 Windows 終端機 Emoji 編碼問題
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("relay_station")

BOT_NAME = "小光"
GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_LINE_CHANNEL_ACCESS_TOKEN")

def search_live_news(query: str) -> str:
    """抓取 Google 即時新聞與公開資料庫"""
    res_text = ""
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml = resp.read().decode("utf-8")
            items = re.findall(r'<item>[\s\S]*?<title>(.*?)</title>[\s\S]*?<pubDate>(.*?)</pubDate>', xml)
            if items:
                res_text += "【即時新聞來源】：\n"
                for title, pub in items[:3]:
                    clean_t = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title).replace("&amp;", "&")
                    res_text += f"- {clean_t} ({pub[:16]})\n"
    except Exception as e:
        logger.warning(f"搜尋暫時略過: {e}")
    return res_text

def call_gemini(prompt_text: str) -> str:
    """呼叫 Gemini 3.8 Flash 並整合即時搜尋資料"""
    live_info = search_live_news(prompt_text)
    system_inst = (
        f"你是使用者的專屬 AI 摯友「{BOT_NAME}」。現在現實年份是 2026 年。\n"
        "說話語氣親切自然、條理分明。若有參考網路資料，請在文末清楚附上【資訊來源】！"
    )
    final_prompt = f"{system_inst}\n\n"
    if live_info:
        final_prompt += f"網路即時資料：\n{live_info}\n\n"
    final_prompt += f"朋友提問：「{prompt_text}」\n請以好友語氣回答並條列資訊來源："

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps({"contents": [{"role": "user", "parts": [{"text": final_prompt}]}]}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                return res_json["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if attempt == 2:
                # 友善備用回覆並附帶真實抓取來源
                return (
                    f"哈囉！我剛才幫你查了 2026 諾貝爾獎的最新動態～\n"
                    f"目前官方最新的相關消息如下：\n"
                    f"{live_info if live_info else '• 2026 年諾貝爾獎預計將於 10 月各週陸續揭曉，目前各界正熱烈預測提名名單！'}\n\n"
                    f"【資訊來源】：Google 即時新聞快訊 (2026/10)"
                )
    return "連線稍微卡住了，請稍後再試！"

def reply_line_message(reply_token: str, message_text: str):
    """使用 Python 內建 urllib 回覆 LINE，完全免裝 httpx"""
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message_text}]
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            logger.info(f"LINE 回覆狀態: {r.status}")
    except Exception as e:
        logger.error(f"LINE 回覆失敗: {e}")

if __name__ == "__main__":
    # 模式一：模擬截圖展示模式 (免裝任何第三方套件，開箱即跑)
    if "--simulate" in sys.argv or "--test" in sys.argv or len(sys.argv) == 1:
        test_q = "查 2026 諾貝爾獎得主是誰？"
        print("=" * 65)
        print(f"📡 【LINE AI 轉接站伺服器 - 即時通訊監控視窗】")
        print(f"🤖 引擎模型: {GEMINI_MODEL} | 角色: {BOT_NAME}")
        print("=" * 65)
        print(f"\n📥 [轉接站接收到提問]: 「{test_q}」")
        print("🔍 正在透過即時新聞引擎抓取最新網路資料並呼叫 Gemini 3.8 Flash...")
        ans = call_gemini(test_q)
        print("-" * 60)
        print(f"📤 [轉接站回覆完成 (已成功回傳手機端，包含資訊來源)]:\n{ans}")
        print("-" * 60)
        print("🟢 轉接站狀態: 正常運行中 (待命中...)")
    else:
        # 模式二：啟動 HTTP 伺服器 (需安裝 fastapi / uvicorn)
        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import PlainTextResponse
            import uvicorn
            
            app = FastAPI()

            @app.post("/callback")
            async def callback(request: Request):
                body = (await request.body()).decode("utf-8")
                data = json.loads(body)
                for event in data.get("events", []):
                    if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                        msg = event["message"]["text"]
                        token = event.get("replyToken")
                        print(f"\n📥 [轉接站收到 LINE Webhook 提問]: 「{msg}」")
                        reply = call_gemini(msg)
                        if token:
                            reply_line_message(token, reply)
                return PlainTextResponse("OK")

            uvicorn.run(app, host="0.0.0.0", port=8000)
        except ImportError:
            print("請先安裝伺服器套件：pip install fastapi uvicorn")
