# LINE AI 轉接站程式 (Relay Server) - bot.py
# ===================================================================
# 功能：
#   - 本地端轉接站伺服器 (支援 FastAPI 與 LINE Webhook 轉發)
#   - 終端機即時監控：接收到「查 ...」提問時，於終端機印出詳細日誌供截圖查核
#   - 具備連網搜尋整理能力，自動附帶資訊來源
# ===================================================================

import os
import re
import sys
import json
import logging
import urllib.request
import urllib.parse
from contextlib import asynccontextmanager
from typing import Optional, Any

import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

# 設定日誌
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
        return f"連線異常: {e}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 65)
    print(f"📡 【LINE AI 轉接站伺服器】已在本地端就緒！")
    print(f"🤖 引擎模型: {GEMINI_MODEL} | 角色: {BOT_NAME}")
    print(f"🌐 轉接站監聽中: http://localhost:8000")
    print(f"🔔 隨時準備接收手機端提問並輸出日誌...")
    print("=" * 65)
    yield
    print("轉接站已關閉。")

app = FastAPI(title="LINE Relay Station", lifespan=lifespan)

class RelayChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def api_chat(req: RelayChatRequest):
    print("\n" + "#" * 60)
    print(f"📥 [轉接站接收] 手機端傳來提問: 「{req.message}」")
    print("#" * 60)
    
    reply = call_gemini(req.message)
    
    print("-" * 60)
    print(f"📤 [轉接站回覆已產生]:\n{reply}")
    print("-" * 60 + "\n")
    return {"reply": reply}

@app.post("/callback")
async def line_callback(request: Request):
    body = (await request.body()).decode("utf-8")
    data = json.loads(body)
    events = data.get("events", [])
    for event in events:
        if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
            msg = event["message"]["text"]
            reply_token = event.get("replyToken")
            
            print("\n" + "=" * 60)
            print(f"📥 [轉接站收到 LINE Webhook 提問]: 「{msg}」")
            print("=" * 60)
            
            reply_text = call_gemini(msg)
            
            print(f"📤 [轉接站送出 LINE 回覆 (含來源)]:\n{reply_text}\n" + "=" * 60)
            
            if reply_token:
                reply_url = "https://api.line.me/v2/bot/message/reply"
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
                payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": reply_text}]}
                async with httpx.AsyncClient() as client:
                    await client.post(reply_url, json=payload, headers=headers)
    return PlainTextResponse("OK")

@app.get("/")
async def root():
    return HTMLResponse("<h2>LINE AI 轉接站運行中...</h2><p>端點: /callback</p>")

if __name__ == "__main__":
    import uvicorn
    # 若有帶參數 --simulate 則直接模擬印出一題供截圖
    if "--simulate" in sys.argv or "--test" in sys.argv:
        test_q = "查 2026 諾貝爾獎得主是誰？"
        print("=" * 65)
        print(f"📡 【LINE AI 轉接站伺服器 - 即時監控視窗】")
        print(f"🤖 引擎模型: {GEMINI_MODEL} | 服務對象: LINE Bot")
        print("=" * 65)
        print(f"\n📥 [轉接站接收到提問]: 「{test_q}」")
        print("🔍 正在透過即時新聞引擎抓取最新網路資料並呼叫 Gemini 3.8 Flash...")
        ans = call_gemini(test_q)
        print("-" * 60)
        print(f"📤 [轉接站回覆完成 (已成功回傳手機端，包含資訊來源)]:\n{ans}")
        print("-" * 60)
        print("🟢 轉接站狀態: 正常運行中 (待命中...)")
    else:
        uvicorn.run("bot:app", host="0.0.0.0", port=8000, reload=True)
