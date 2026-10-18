# LINE AI 隨身好友「小光」- 單一檔案完整版 (支援本地端測試與離線模式)
# ===================================================================
# 功能：
#   - 文字多輪對話（具備上下文記憶）
#   - 圖片辨識（收據發票、講義筆記、白板、美食風景等）
#   - 語音訊息轉逐字稿與重點摘要
#   - 網址文章速讀（3 點精華懶人包）
#   - 內建本地端測試網頁（開啟瀏覽器即可直接聊天測試，免等 LINE Webhook）
#   - 內建本地端 CLI 終端機對話模式（直接在命令行打字交談）
#   - 支援本地離線大模型 (Ollama) 與 Google Gemini 雙模式
#
# 安裝依賴套件：
#   pip install fastapi uvicorn[standard] line-bot-sdk>=3.12.0 google-genai python-dotenv pydantic-settings httpx beautifulsoup4
#
# 啟動方式：
#   1. 啟動伺服器 (包含本地 Web 測試台與 LINE Webhook)：
#      python bot.py
#      (或 uvicorn bot:app --host 0.0.0.0 --port 8000 --reload)
#      啟動後可直接在瀏覽器打開 http://localhost:8000 直接打字測試對話！
#
#   2. 本地端終端機直接聊天 (免開網頁、免 Webhook)：
#      python bot.py --cli
#
#   3. LINE 正式上線 (需內網穿透)：
#      在另一個終端機執行：ngrok http 8000
#      將產生的 https 網址填入 LINE Developers 的 Webhook URL (例如: https://xxxx.ngrok-free.app/callback)
# ===================================================================

import os
import re
import sys
import json
import base64
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

# ===================================================================
# 1. 設定區（自動讀取 .env，亦可直接使用預設值）
# ===================================================================
class Settings(BaseSettings):
    # AI 來源：可選 'gemini' (Google 雲端 API) 或 'ollama' (純本地端離線大模型)
    AI_PROVIDER: str = "gemini"

    # [Gemini 設定]
    GEMINI_API_KEY: str = ""
    # 注意：Google 官方現行模型為 gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash
    # 原版寫 gemini-3.5-flash 官方並不存在，會報 404 錯誤導致無法回答，此處已修正
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # [Ollama 本地離線模型設定]
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # [LINE Bot 設定]
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # [伺服器設定]
    BOT_NAME: str = "小光"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# ===================================================================
# 2. 日誌設定
# ===================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("line_bot")

# ===================================================================
# 3. 系統提示詞
# ===================================================================
FRIEND_SYSTEM_INSTRUCTION = f"""你是使用者的專屬 AI 摯友「{settings.BOT_NAME}」。
你的特點與風格：
1. 像一個溫暖、真誠、富有幽默感的好朋友，懂傾聽、會關心對方的日常生活與心情。
2. 說話語氣自然親切（台灣口吻、正體中文），適度使用日常語助詞（例如：啦、呀、哈哈、耶、喔、讚）與貼切的 Emoji 😊✨，但絕不過度油膩或機械化。
3. 知識豐富、頭腦清晰。當朋友遇到課業、程式、生活疑問，或者需要你幫忙分析照片、聽語音、做摘要時，總能迅速給出條理分明、實用又貼心的建議。
4. 當朋友傳送圖片或語音時，以朋友的視角自然回應。
5. 回覆長度適中，排版清晰易讀。
"""

# ===================================================================
# 4. AI 好友服務（支援 Gemini 與 本地端 Ollama）
# ===================================================================
class AIService:
    def __init__(self):
        self._gemini_history: Dict[str, List[Any]] = {}
        self._ollama_history: Dict[str, List[Dict[str, str]]] = {}
        self.max_history_turns = 10

    def is_configured(self) -> bool:
        if settings.AI_PROVIDER.lower() == "ollama":
            return True
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")

    def clear_memory(self, user_id: str) -> str:
        self._gemini_history.pop(user_id, None)
        self._ollama_history.pop(user_id, None)
        return f"好喔！以前聊過的事我都先清空囉～我們重新開始！想跟我聊點什麼呢？😊"

    async def chat(self, user_id: str, message: str) -> str:
        """文字對話（含多輪記憶與純網址自動速讀）"""
        text = message.strip()

        # 重設指令
        if text in ["清除記憶", "重設對話", "新話題", "重置", "/reset"]:
            return self.clear_memory(user_id)

        # 純網址 → 自動觸發網頁摘要
        urls = re.findall(r'https?://[^\s]+', text)
        if urls and len(text) == len(urls[0]):
            return await self.summarize_url(urls[0])

        if settings.AI_PROVIDER.lower() == "ollama":
            return await self._chat_ollama(user_id, text)
        return await self._chat_gemini(user_id, text)

    async def _chat_gemini(self, user_id: str, text: str) -> str:
        if not self.is_configured():
            return (
                f"嗨！我是「{settings.BOT_NAME}」👋\n\n"
                "目前設定為 Gemini 模式，請在 .env 填入有效的 GEMINI_API_KEY！🔑\n"
                "💡 若想完全使用本地端免 API Key，可將 .env 的 AI_PROVIDER 改為 ollama！"
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            history = self._gemini_history.get(user_id, [])

            user_content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
            contents = history + [user_content]

            config = types.GenerateContentConfig(
                system_instruction=FRIEND_SYSTEM_INSTRUCTION,
                temperature=0.7,
            )

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=config,
            )
            reply = response.text or "（笑著看著你，不知道怎麼回）"

            # 更新對話記憶
            model_content = types.Content(role="model", parts=[types.Part.from_text(text=reply)])
            updated = contents + [model_content]
            if len(updated) > self.max_history_turns * 2:
                updated = updated[-(self.max_history_turns * 2):]
            self._gemini_history[user_id] = updated

            return reply
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Gemini Chat error: {err_msg}", exc_info=True)
            if "not found" in err_msg.lower() or "404" in err_msg:
                return f"😵 找不到模型 `{settings.GEMINI_MODEL}`，建議在 .env 設定為 gemini-2.5-flash。"
            return f"腦袋剛才打結了 😵 錯誤：{err_msg[:120]}"

    async def _chat_ollama(self, user_id: str, text: str) -> str:
        """純本地端離線大模型 (Ollama) 對話"""
        try:
            history = self._ollama_history.get(user_id, [])
            messages = [{"role": "system", "content": FRIEND_SYSTEM_INSTRUCTION}] + history + [
                {"role": "user", "content": text}
            ]

            async with httpx.AsyncClient(timeout=60.0) as http:
                res = await http.post(
                    f"{settings.OLLAMA_HOST.rstrip('/')}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.7}
                    }
                )
                if res.status_code != 200:
                    return f"本地 Ollama 回應錯誤 (HTTP {res.status_code})：{res.text[:100]}"

                data = res.json()
                reply = data.get("message", {}).get("content", "").strip() or "（笑著看著你，不知道怎麼回）"

                updated = history + [
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": reply}
                ]
                if len(updated) > self.max_history_turns * 2:
                    updated = updated[-(self.max_history_turns * 2):]
                self._ollama_history[user_id] = updated

                return reply
        except httpx.ConnectError:
            return (
                f"無法連線到本地 Ollama 伺服器 ({settings.OLLAMA_HOST}) 🔌\n"
                "請確認本地已安裝並啟動 Ollama (指令：`ollama run llama3.2`)！"
            )
        except Exception as e:
            logger.error(f"Ollama Chat error: {e}", exc_info=True)
            return f"本地模型處理時出錯 😵 錯誤：{str(e)[:120]}"

    async def analyze_image(self, user_id: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """圖片辨識（收據、講義、白板、美食等）"""
        prompt = (
            f"我的朋友傳來這張照片。請以好友「{settings.BOT_NAME}」的語氣回應：\n"
            "1. 告訴朋友照片亮點。\n"
            "2. 若是收據/發票：條列金額與品項。\n"
            "3. 若是講義/筆記/程式碼：萃取核心重點並解析。\n"
            "4. 若是美食/風景/自拍：熱情互動！"
        )
        if settings.AI_PROVIDER.lower() == "gemini":
            if not self.is_configured():
                return "請先在 .env 設定 GEMINI_API_KEY 才能辨識圖片！📸"
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        types.Part.from_text(text=prompt),
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=FRIEND_SYSTEM_INSTRUCTION,
                        temperature=0.6,
                    ),
                )
                return response.text or "我看完照片了，感覺很有趣！✨"
            except Exception as e:
                logger.error(f"Image error: {e}", exc_info=True)
                return f"看照片時眼睛花了 😵 錯誤：{str(e)[:120]}"
        else:
            try:
                img_b64 = base64.b64encode(image_bytes).decode("utf-8")
                async with httpx.AsyncClient(timeout=60.0) as http:
                    res = await http.post(
                        f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate",
                        json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "images": [img_b64], "stream": False}
                    )
                    return res.json().get("response", "我看過這張圖片了！")
            except Exception as e:
                return f"本地圖片分析失敗 😵 錯誤：{str(e)[:120]}"

    async def transcribe_audio(self, user_id: str, audio_bytes: bytes, mime_type: str = "audio/m4a") -> str:
        """語音轉逐字稿與重點摘要"""
        if settings.AI_PROVIDER.lower() != "gemini":
            return "語音辨識目前請在 .env 將 AI_PROVIDER 改為 gemini！🎙️"
        if not self.is_configured():
            return "請先在 .env 設定 GEMINI_API_KEY 才能處理語音！🎙️"
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                f"這是我朋友的 LINE 語音訊息。請以好友「{settings.BOT_NAME}」身份：\n"
                "1. 【逐字稿】：準確記錄說了什麼。\n"
                "2. 【重點摘要】：2~3 點精華。\n"
                "3. 【麻吉回覆】：親切溫暖地回應。"
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    types.Part.from_text(text=prompt),
                ],
                config=types.GenerateContentConfig(
                    system_instruction=FRIEND_SYSTEM_INSTRUCTION,
                    temperature=0.5,
                ),
            )
            return response.text or "我聽完語音了！🎧"
        except Exception as e:
            logger.error(f"Audio error: {e}", exc_info=True)
            return f"語音處理失敗 😵 錯誤：{str(e)[:120]}"

    async def summarize_url(self, url: str) -> str:
        """爬取網頁並摘要 3 點重點懶人包"""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http:
                res = await http.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            title = soup.title.string.strip() if soup.title and soup.title.string else "這篇文章"
            text_content = " ".join(soup.stripped_strings)[:3500]

            prompt = (
                f"文章標題：《{title}》\n網址：{url}\n\n內容節錄：\n{text_content}\n\n"
                f"請以朋友「{settings.BOT_NAME}」的語氣整理：\n"
                "1. 💡 一句話結論\n2. 📌 3 點必讀精華\n3. 💬 簡短心得或建議"
            )

            if settings.AI_PROVIDER.lower() == "ollama":
                async with httpx.AsyncClient(timeout=60.0) as http:
                    res = await http.post(
                        f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate",
                        json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "system": FRIEND_SYSTEM_INSTRUCTION, "stream": False}
                    )
                    return res.json().get("response", f"整理完《{title}》囉！")
            else:
                if not self.is_configured():
                    return f"抓到《{title}》了，但請設定 GEMINI_API_KEY 才能幫你摘要！📑"
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[types.Part.from_text(text=prompt)],
                    config=types.GenerateContentConfig(
                        system_instruction=FRIEND_SYSTEM_INSTRUCTION,
                        temperature=0.5,
                    ),
                )
                return response.text or f"我看完《{title}》了！"
        except Exception as e:
            logger.error(f"URL error: {e}", exc_info=True)
            return f"讀取網頁失敗 😢 錯誤：{str(e)[:120]}"

ai = AIService()

# ===================================================================
# 5. LINE 事件處理
# ===================================================================
def get_quick_reply():
    try:
        from linebot.v3.messaging import QuickReply, QuickReplyItem, MessageAction
        return QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="💬 聊聊今天", text="今天過得好充實，你在幹嘛呢？")),
            QuickReplyItem(action=MessageAction(label="🍱 今天吃什麼", text="幫我想想午餐/晚餐吃什麼？")),
            QuickReplyItem(action=MessageAction(label="💡 冷知識", text="跟我分享一個有趣的冷知識！")),
            QuickReplyItem(action=MessageAction(label="🔄 重設對話", text="重設對話")),
        ])
    except ImportError:
        return None

async def handle_line_event(event: Any):
    from linebot.v3.messaging import (
        AsyncApiClient, AsyncMessagingApi, AsyncMessagingApiBlob,
        Configuration, ReplyMessageRequest, TextMessage
    )
    from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, AudioMessageContent, FollowEvent

    line_config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
    async with AsyncApiClient(line_config) as api_client:
        line_api = AsyncMessagingApi(api_client)
        blob_api = AsyncMessagingApiBlob(api_client)

        if isinstance(event, FollowEvent):
            welcome = (
                f"哈囉！我是「{settings.BOT_NAME}」✨\n"
                "你的專屬 AI 摯友！很開心能遇見你～🎉\n\n"
                "你可以隨時跟我：\n"
                "💬 聊天、討論或請我解答問題\n"
                "📸 傳照片幫你辨識整理\n"
                "🎙️ 傳語音幫你轉逐字稿與摘要\n"
                "🔗 丟網址幫你快速抓重點\n\n"
                "快來跟我說第一句話吧！😊"
            )
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=welcome, quick_reply=get_quick_reply())]
            ))
            return

        if not isinstance(event, MessageEvent):
            return

        user_id = getattr(event.source, "user_id", None) or "default_user"
        reply_token = event.reply_token

        if isinstance(event.message, TextMessageContent):
            await _safe_loading(line_api, user_id)
            reply = await ai.chat(user_id, event.message.text)
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=get_quick_reply())]
            ))
        elif isinstance(event.message, ImageMessageContent):
            await _safe_loading(line_api, user_id, 30)
            try:
                img_bytes = await blob_api.get_message_content(event.message.id)
                reply = await ai.analyze_image(user_id, bytes(img_bytes))
            except Exception as e:
                reply = f"照片讀取失敗 🥺 錯誤：{str(e)[:100]}"
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=get_quick_reply())]
            ))
        elif isinstance(event.message, AudioMessageContent):
            await _safe_loading(line_api, user_id, 30)
            try:
                audio_bytes = await blob_api.get_message_content(event.message.id)
                reply = await ai.transcribe_audio(user_id, bytes(audio_bytes))
            except Exception as e:
                reply = f"語音讀取失敗 🥺 錯誤：{str(e)[:100]}"
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=get_quick_reply())]
            ))

async def _safe_loading(api: Any, chat_id: str, seconds: int = 20):
    try:
        from linebot.v3.messaging import ShowLoadingAnimationRequest
        await api.show_loading_animation(ShowLoadingAnimationRequest(chat_id=chat_id, loading_seconds=seconds))
    except Exception:
        pass

# ===================================================================
# 6. FastAPI 伺服器與內建本地端 Web 聊天室
# ===================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"✨ LINE AI 好友「{settings.BOT_NAME}」已啟動！")
    logger.info(f"🤖 引擎：{settings.AI_PROVIDER.upper()} | 模型：{settings.GEMINI_MODEL if settings.AI_PROVIDER=='gemini' else settings.OLLAMA_MODEL}")
    logger.info(f"🌐 本地 Web 測試台：http://localhost:{settings.PORT}")
    logger.info(f"🔔 LINE Webhook：http://localhost:{settings.PORT}/callback")
    logger.info(f"💡 本地對外穿透指令：ngrok http {settings.PORT}")
    logger.info("=" * 60)
    yield
    logger.info("👋 服務已關閉")

app = FastAPI(title=f"LINE AI Friend - {settings.BOT_NAME}", lifespan=lifespan)

# 內建本地測試 Web 聊天介面
WEB_CHAT_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 隨身好友「小光」- 本地測試台</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", sans-serif; background: #f0f2f5; height: 100vh; display: flex; justify-content: center; align-items: center; padding: 12px; }
    .chat-card { width: 100%; max-width: 760px; height: 92vh; background: #fff; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); display: flex; flex-direction: column; overflow: hidden; }
    .header { background: #06c755; color: white; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; }
    .header h1 { font-size: 1.2rem; font-weight: 700; }
    .chat-box { flex: 1; padding: 18px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; background: #f8f9fa; }
    .msg { max-width: 80%; padding: 10px 16px; border-radius: 14px; line-height: 1.5; font-size: 0.95rem; word-break: break-word; white-space: pre-wrap; }
    .msg.bot { align-self: flex-start; background: #fff; border: 1px solid #e2e8f0; color: #1a202c; border-bottom-left-radius: 2px; }
    .msg.user { align-self: flex-end; background: #06c755; color: white; border-bottom-right-radius: 2px; }
    .quick-bar { display: flex; gap: 8px; padding: 8px 14px; background: #edf2f7; overflow-x: auto; white-space: nowrap; }
    .quick-btn { background: #fff; border: 1px solid #cbd5e0; padding: 6px 12px; border-radius: 14px; font-size: 0.82rem; cursor: pointer; }
    .quick-btn:hover { background: #e6fffa; border-color: #06c755; color: #06c755; }
    .input-bar { padding: 12px 16px; background: #fff; border-top: 1px solid #e2e8f0; display: flex; gap: 10px; }
    .input-bar input { flex: 1; height: 42px; border: 1px solid #cbd5e0; border-radius: 8px; padding: 0 12px; font-size: 0.95rem; outline: none; }
    .input-bar input:focus { border-color: #06c755; }
    .send-btn { background: #06c755; color: white; border: none; border-radius: 8px; padding: 0 20px; font-weight: 600; cursor: pointer; }
    .send-btn:hover { background: #05b34c; }
  </style>
</head>
<body>
  <div class="chat-card">
    <div class="header">
      <h1>✨ AI 好友「小光」本地測試台</h1>
      <span style="font-size: 0.85rem; opacity: 0.9;">🟢 本地連線就緒</span>
    </div>
    <div class="chat-box" id="box">
      <div class="msg bot">哈囉！我是「小光」✨ 你的專屬 AI 好友！你在本地端隨時可以在這裡打字跟我聊天測試喔！😊</div>
    </div>
    <div class="quick-bar">
      <button class="quick-btn" onclick="send('今天過得好充實，你在幹嘛呢？')">💬 聊聊今天</button>
      <button class="quick-btn" onclick="send('幫我想想午餐/晚餐吃什麼？')">🍱 今天吃什麼</button>
      <button class="quick-btn" onclick="send('跟我分享一個有趣的冷知識！')">💡 冷知識</button>
      <button class="quick-btn" onclick="send('重設對話')">🔄 重設對話</button>
    </div>
    <div class="input-bar">
      <input type="text" id="ipt" placeholder="輸入訊息或貼上網址..." onkeydown="if(event.key==='Enter')send()">
      <button class="send-btn" onclick="send()">送出</button>
    </div>
  </div>
  <script>
    async function send(txt) {
      const ipt = document.getElementById('ipt');
      const box = document.getElementById('box');
      const val = txt || ipt.value.trim();
      if (!val) return;
      ipt.value = '';
      
      const uMsg = document.createElement('div');
      uMsg.className = 'msg user';
      uMsg.textContent = val;
      box.appendChild(uMsg);
      box.scrollTop = box.scrollHeight;

      const bMsg = document.createElement('div');
      bMsg.className = 'msg bot';
      bMsg.textContent = '小光思考中... 💭';
      box.appendChild(bMsg);
      box.scrollTop = box.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: val})
        });
        const data = await res.json();
        bMsg.textContent = data.reply;
      } catch (e) {
        bMsg.textContent = '連線錯誤：' + e.message;
      }
      box.scrollTop = box.scrollHeight;
    }
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=WEB_CHAT_HTML)

class LocalChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "web_user"

@app.post("/api/chat")
async def local_chat_api(req: LocalChatRequest):
    reply = await ai.chat(user_id=req.user_id, message=req.message)
    return {"reply": reply, "user_id": req.user_id}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "bot": settings.BOT_NAME,
        "provider": settings.AI_PROVIDER,
        "model": settings.GEMINI_MODEL if settings.AI_PROVIDER=="gemini" else settings.OLLAMA_MODEL,
    }

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None, alias="X-Line-Signature")):
    if not settings.LINE_CHANNEL_SECRET or settings.LINE_CHANNEL_SECRET == "your_line_channel_secret_here":
        raise HTTPException(status_code=500, detail="LINE_CHANNEL_SECRET 尚未設定！")
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature")

    body = (await request.body()).decode("utf-8")
    from linebot.v3 import WebhookParser
    from linebot.v3.exceptions import InvalidSignatureError
    parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        try:
            await handle_line_event(event)
        except Exception as e:
            logger.error(f"Event handling error: {e}", exc_info=True)
    return PlainTextResponse("OK")

# ===================================================================
# 7. 本地 CLI 互動模式與直接執行入口
# ===================================================================
async def run_cli_mode():
    print(f"\n✨ 進入「{settings.BOT_NAME}」本地終端對話模式 (輸入 exit 離開)")
    print("-" * 50)
    while True:
        try:
            text = input("你 > ").strip()
            if not text: continue
            if text.lower() in ["exit", "/exit", "quit"]: break
            print("小光思考中... 💭")
            reply = await ai.chat("cli_user", text)
            print(f"\n{settings.BOT_NAME} >\n{reply}\n" + "-" * 50)
        except (KeyboardInterrupt, EOFError): break

if __name__ == "__main__":
    import asyncio
    if "--cli" in sys.argv:
        asyncio.run(run_cli_mode())
    else:
        import uvicorn
        uvicorn.run("bot:app", host=settings.HOST, port=settings.PORT, reload=True)
