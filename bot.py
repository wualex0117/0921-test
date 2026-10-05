# LINE AI 隨身好友「小光」- 單一檔案完整版
# =========================================
# 功能：
#   - 文字多輪對話（具備上下文記憶）
#   - 圖片辨識（收據、講義、白板、美食等）
#   - 語音訊息轉逐字稿與重點摘要
#   - 網址文章速讀（3 點懶人包）
#
# 啟動方式：
#   .venv/Scripts/uvicorn bot:app --host 0.0.0.0 --port 8000 --reload
#
# 需要安裝的套件（requirements.txt）：
#   fastapi uvicorn[standard] line-bot-sdk>=3.12.0
#   google-genai python-dotenv pydantic-settings httpx beautifulsoup4

# ===================================================================
# 1. 標準套件
# ===================================================================
import re
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

# ===================================================================
# 2. 第三方套件
# ===================================================================
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic_settings import BaseSettings, SettingsConfigDict
from google import genai
from google.genai import types

from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    AsyncMessagingApiBlob,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    ShowLoadingAnimationRequest,
)
from linebot.v3.webhooks import (
    Event,
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    AudioMessageContent,
    FollowEvent,
)

# ===================================================================
# 3. 設定區（從 .env 讀取）
# ===================================================================
load_dotenv()

class Settings(BaseSettings):
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    BOT_NAME: str = "小光"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    GEMINI_MODEL: str = "gemini-3.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# ===================================================================
# 4. 日誌設定
# ===================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("line_bot")

# ===================================================================
# 5. AI 好友服務（Gemini 多模態）
# ===================================================================
FRIEND_SYSTEM_INSTRUCTION = f"""你是使用者的專屬 AI 摯友「{settings.BOT_NAME}」。
你的特點與風格：
1. 像一個溫暖、真誠、富有幽默感的好朋友，懂傾聽、會關心對方的日常生活與心情。
2. 說話語氣自然親切（台灣口吻、正體中文），適度使用日常語助詞（例如：啦、呀、哈哈、耶、喔、讚）與貼切的 Emoji 😊✨，但絕不過度油膩或機械化。
3. 知識豐富、頭腦清晰。當朋友遇到課業、程式、生活疑問，或者需要你幫忙分析照片、聽語音、做摘要時，總能迅速給出條理分明、實用又貼心的建議。
4. 當朋友傳送圖片或語音時，以朋友的視角自然回應。
5. 回覆長度適中，排版清晰易讀。
"""


class AIService:
    def __init__(self):
        self._history_cache: Dict[str, List[types.Content]] = {}
        self.max_history_turns = 10

    def _is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")

    def _client(self) -> Optional[genai.Client]:
        if not self._is_configured():
            return None
        return genai.Client(api_key=settings.GEMINI_API_KEY)

    def _config(self, temperature: float = 0.7) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=FRIEND_SYSTEM_INSTRUCTION,
            temperature=temperature,
        )

    def clear_memory(self, user_id: str) -> str:
        self._history_cache.pop(user_id, None)
        return f"好喔！以前聊過的事我都先清空囉～我們重新開始！想跟我聊點什麼呢？😊"

    async def chat(self, user_id: str, message: str) -> str:
        """文字對話（含上下文記憶與網址速讀）"""
        text = message.strip()

        # 重設指令
        if text in ["清除記憶", "重設對話", "新話題", "重置", "/reset"]:
            return self.clear_memory(user_id)

        if not self._is_configured():
            return (
                f"嗨！我是「{settings.BOT_NAME}」👋\n\n"
                "請在 .env 填入 GEMINI_API_KEY，我就能陪你聊天囉！🔑"
            )

        # 純網址 → 自動觸發網頁摘要
        urls = re.findall(r'https?://[^\s]+', text)
        if urls and len(text) == len(urls[0]):
            return await self.summarize_url(urls[0])

        client = self._client()
        try:
            history = self._history_cache.get(user_id, [])
            user_content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
            contents = history + [user_content]

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=self._config(0.7),
            )
            reply = response.text or "（笑著看著你，不知道怎麼回）"

            # 更新記憶
            model_content = types.Content(role="model", parts=[types.Part.from_text(text=reply)])
            updated = contents + [model_content]
            if len(updated) > self.max_history_turns * 2:
                updated = updated[-(self.max_history_turns * 2):]
            self._history_cache[user_id] = updated

            return reply
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return f"腦袋剛才打結了 😵 錯誤：{str(e)[:100]}"

    async def analyze_image(self, user_id: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """圖片辨識（發票、講義、白板、美食等）"""
        if not self._is_configured():
            return "請先在 .env 設定 GEMINI_API_KEY 才能辨識圖片！📸"

        client = self._client()
        prompt = (
            f"我的朋友傳來這張照片。請以好友「{settings.BOT_NAME}」的語氣回應：\n"
            "1. 告訴朋友照片亮點。\n"
            "2. 若是收據/發票：條列金額與品項。\n"
            "3. 若是講義/筆記/程式碼：萃取核心重點並解析。\n"
            "4. 若是美食/風景/自拍：熱情互動！"
        )
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    types.Part.from_text(text=prompt),
                ],
                config=self._config(0.6),
            )
            return response.text or "我看完照片了，感覺很有趣！"
        except Exception as e:
            logger.error(f"Image error: {e}", exc_info=True)
            return f"看照片時眼睛花了 😵 錯誤：{str(e)[:100]}"

    async def transcribe_audio(self, user_id: str, audio_bytes: bytes, mime_type: str = "audio/m4a") -> str:
        """語音訊息轉逐字稿與摘要"""
        if not self._is_configured():
            return "請先在 .env 設定 GEMINI_API_KEY 才能處理語音！🎙️"

        client = self._client()
        prompt = (
            f"這是我朋友的 LINE 語音訊息。請以好友「{settings.BOT_NAME}」的身份：\n"
            "1. 【逐字稿】：準確記錄說了什麼。\n"
            "2. 【重點摘要】：2~3 點精華。\n"
            "3. 【麻吉回覆】：親切溫暖地回應。"
        )
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    types.Part.from_text(text=prompt),
                ],
                config=self._config(0.5),
            )
            return response.text or "我聽完語音了，不過有點雜音，要不要再錄一次？🎧"
        except Exception as e:
            logger.error(f"Audio error: {e}", exc_info=True)
            return f"語音處理失敗 😵 錯誤：{str(e)[:100]}"

    async def summarize_url(self, url: str) -> str:
        """爬取網頁並摘要 3 點重點"""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http:
                res = await http.get(url, headers={"User-Agent": "Mozilla/5.0"})
                res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            title = soup.title.string.strip() if soup.title else "這篇文章"
            text_content = " ".join(soup.stripped_strings)[:4000]

            if not self._is_configured():
                return f"抓到《{title}》了，但需要 GEMINI_API_KEY 才能幫你摘要！📑"

            client = self._client()
            prompt = (
                f"文章標題：《{title}》\n網址：{url}\n\n內容節錄：\n{text_content}\n\n"
                f"請以朋友「{settings.BOT_NAME}」的語氣整理：\n"
                "1. 一句話結論\n2. 3 點必讀精華\n3. 簡短心得或建議"
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[types.Part.from_text(text=prompt)],
                config=self._config(0.5),
            )
            return response.text or f"我看完《{title}》了！"
        except Exception as e:
            logger.error(f"URL error: {e}", exc_info=True)
            return f"讀取網頁失敗 😢 錯誤：{str(e)[:100]}"


# 全域 AI 服務實例
ai = AIService()

# ===================================================================
# 6. LINE 事件處理
# ===================================================================
def quick_reply() -> QuickReply:
    """聊天室快捷按鈕"""
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="💬 聊聊今天", text="今天過得好充實，你在幹嘛呢？")),
        QuickReplyItem(action=MessageAction(label="🍱 今天吃什麼", text="幫我想想午餐/晚餐吃什麼？")),
        QuickReplyItem(action=MessageAction(label="💡 冷知識", text="跟我分享一個有趣的冷知識！")),
        QuickReplyItem(action=MessageAction(label="🔄 重設對話", text="重設對話")),
    ])


async def handle_line_event(event: Event):
    """分派處理 LINE 事件"""
    line_config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)

    async with AsyncApiClient(line_config) as api_client:
        line_api = AsyncMessagingApi(api_client)
        blob_api = AsyncMessagingApiBlob(api_client)

        # 加好友歡迎訊息
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
                messages=[TextMessage(text=welcome, quick_reply=quick_reply())]
            ))
            return

        # 訊息事件
        if not isinstance(event, MessageEvent):
            return

        user_id = getattr(event.source, "user_id", None) or "default_user"
        reply_token = event.reply_token

        # ── 文字訊息 ──
        if isinstance(event.message, TextMessageContent):
            await _safe_loading(line_api, user_id)
            reply = await ai.chat(user_id, event.message.text)
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=quick_reply())]
            ))

        # ── 圖片訊息 ──
        elif isinstance(event.message, ImageMessageContent):
            await _safe_loading(line_api, user_id, 30)
            try:
                img_bytes = await blob_api.get_message_content(event.message.id)
                reply = await ai.analyze_image(user_id, bytes(img_bytes))
            except Exception as e:
                reply = f"抓取照片失敗 🥺 錯誤：{str(e)[:100]}"
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=quick_reply())]
            ))

        # ── 語音訊息 ──
        elif isinstance(event.message, AudioMessageContent):
            await _safe_loading(line_api, user_id, 30)
            try:
                audio_bytes = await blob_api.get_message_content(event.message.id)
                reply = await ai.transcribe_audio(user_id, bytes(audio_bytes))
            except Exception as e:
                reply = f"語音接收失敗 🥺 錯誤：{str(e)[:100]}"
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=quick_reply())]
            ))


async def _safe_loading(api: AsyncMessagingApi, chat_id: str, seconds: int = 20):
    """顯示 LINE 打字中動畫（群組不支援，失敗時靜默忽略）"""
    try:
        await api.show_loading_animation(
            ShowLoadingAnimationRequest(chat_id=chat_id, loading_seconds=seconds)
        )
    except Exception:
        pass


# ===================================================================
# 7. FastAPI 應用程式
# ===================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info(f"✨ LINE AI 好友「{settings.BOT_NAME}」啟動！")
    logger.info(f"🤖 模型：{settings.GEMINI_MODEL}")
    logger.info(f"🔔 Webhook：http://{settings.HOST}:{settings.PORT}/callback")
    logger.info("=" * 50)
    yield
    logger.info(f"👋「{settings.BOT_NAME}」下線")


app = FastAPI(
    title=f"LINE AI Friend - {settings.BOT_NAME}",
    version="1.0.0",
    lifespan=lifespan
)


def _get_parser() -> WebhookParser:
    secret = settings.LINE_CHANNEL_SECRET
    if not secret or secret == "your_line_channel_secret_here":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LINE_CHANNEL_SECRET 尚未設定"
        )
    return WebhookParser(secret)


@app.get("/", response_class=PlainTextResponse)
async def root():
    return f"✨ LINE AI 好友「{settings.BOT_NAME}」運作中！Webhook → /callback"


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "bot": settings.BOT_NAME,
        "model": settings.GEMINI_MODEL,
        "line_secret": bool(settings.LINE_CHANNEL_SECRET and settings.LINE_CHANNEL_SECRET != "your_line_channel_secret_here"),
        "line_token": bool(settings.LINE_CHANNEL_ACCESS_TOKEN and settings.LINE_CHANNEL_ACCESS_TOKEN != "your_line_channel_access_token_here"),
        "gemini_key": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
    }


@app.post("/callback")
async def callback(
    request: Request,
    x_line_signature: str = Header(None, alias="X-Line-Signature")
):
    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature")

    body = (await request.body()).decode("utf-8")
    parser = _get_parser()

    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    for event in events:
        try:
            await handle_line_event(event)
        except Exception as e:
            logger.error(f"Event handling error: {e}", exc_info=True)

    return PlainTextResponse("OK")


# ===================================================================
# 8. 直接執行入口
# ===================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host=settings.HOST, port=settings.PORT, reload=True)
