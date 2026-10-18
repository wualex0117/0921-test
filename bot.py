# LINE AI ?¨èº«å¥½å??Œå??‰ã€? ?¬åœ°?‡ç?ä¸Šé?æ¨¡å?å¼·ç? (?®ä?æª”æ?å®Œæ•´??
# ===================================================================
# ?Ÿèƒ½?¹è‰²ï¼?#   - ?ä¿®æ­?¿®å¾©ã€‘ï?ä¿®å¾©?Ÿç? gemini-3.5-flash å®˜æ–¹ä¸å??¨å???404 ?¡æ??ç?ä¹‹å?é¡Œã€?#   - ?é?æ¨¡å??¯æ´?‘ï?
#       1. Gemini ?²ç«¯ API (?è¨­ gemini-2.5-flash / gemini-2.0-flash)
#       2. ?¬åœ°ç«¯é›¢ç·?LLM (Ollamaï¼Œå? API Key?å??¨åœ¨?¬åœ°ç«¯é›»?¦é?è¡Œï?)
#   - ?æœ¬?°ç«¯?¡ç?æ¸¬è©¦?‘ï?
#       1. ?§å»º?¬åœ° Web ?Šå¤©å®?(?è¦½?¨æ???http://localhost:8000 ?³å¯?´æ¥?“å?äº¤è?)
#       2. ?§å»º?¬åœ° CLI çµ‚ç«¯å°è©±æ¨¡å? (?·è? python bot.py --cli ?³åˆ»æ¸¬è©¦)
#   - ?å?æ¨¡æ??‡å??½ã€‘ï?
#       - å¤šè¼ªè¨˜æ†¶å°è©± (ä¸Šä??‡é€??)
#       - ç¶²å??‡ç??ªå??Ÿè? (3 é»å?è®€ç²¾è¯)
#       - ?–ç?è¾¨è? (?¯æ´?¼ç¥¨?¶æ??è?ç¾©ç?è¨˜ã€ç?é£Ÿé¢¨??
#       - èªéŸ³è¨Šæ¯è¾¨è??‡è??å?ç¨¿é?é»æ?è¦?(Gemini æ¨¡å?)
#
# ?Ÿå??¹å?ï¼?#   1. ?Ÿå? Web ?å???LINE Webhookï¼?#      python bot.py
#      ??#      uvicorn bot:app --host 0.0.0.0 --port 8000 --reload
#
#   2. ?¬åœ°çµ‚ç«¯æ©Ÿç›´?¥å?è©±æ¸¬è©?(?æ¶ä¼ºæ???ï¼?#      python bot.py --cli
#
# ä¾è³´å¥—ä»¶ (requirements.txt)ï¼?#   fastapi uvicorn[standard] line-bot-sdk>=3.12.0
#   google-genai python-dotenv pydantic-settings httpx beautifulsoup4
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
from fastapi import FastAPI, Request, Header, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# è¼‰å…¥ .env è¨­å?
load_dotenv()

# ===================================================================
# 1. è¨­å?ç®¡ç? (?¯æ´ Gemini ???¬åœ°ç«?Ollama)
# ===================================================================
class Settings(BaseSettings):
    # AI ä¾†æ?: 'gemini' (?²ç«¯) ??'ollama' (?¬åœ°?¢ç?)
    AI_PROVIDER: str = "gemini"

    # [Gemini è¨­å?]
    GEMINI_API_KEY: str = ""
    # æ³¨æ?: Google å®˜æ–¹?®å??ä? gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash ç­?    # ?Ÿå???gemini-3.5-flash å®˜æ–¹ä¸¦ä?å­˜åœ¨ï¼Œæ?å°è‡´ 404 ?±éŒ¯?¡æ??ç?
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # [Ollama ?¬åœ°å¤§æ¨¡?‹è¨­å®š]
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # [LINE Bot è¨­å?]
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # [ç³»çµ±?‡å??‰è¨­å®š]
    BOT_NAME: str = "å°å?"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# ===================================================================
# 2. ?¥è?è¨­å?
# ===================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("line_bot")

# ===================================================================
# 3. ç³»çµ±?ç¤ºè©?# ===================================================================
FRIEND_SYSTEM_INSTRUCTION = f"""ä½ æ˜¯ä½¿ç”¨?…ç?å°ˆå±¬ AI ?¯å??Œ{settings.BOT_NAME}?ã€?ä½ ç??¹é??‡é¢¨?¼ï?
1. ?ä??‹æº«?–ã€ç?èª ã€å??‰å¹½é»˜æ??„å¥½?‹å?ï¼Œæ??¾è½?æ??œå?å°æ–¹?„æ—¥å¸¸ç?æ´»è?å¿ƒæ???2. èªªè©±èªæ°£?ªç„¶è¦ªå?ï¼ˆå°??£?»ã€æ­£é«”ä¸­?‡ï?ï¼Œé©åº¦ä½¿?¨æ—¥å¸¸è??©è?ï¼ˆä?å¦‚ï??¦ã€å??å??ˆã€è€¶ã€å??è?ï¼‰è?è²¼å???Emoji ???¨ï?ä½†ç?ä¸é?åº¦æ²¹?©æ?æ©Ÿæ¢°?–ã€?3. ?¥è?è±å??é ­?¦æ??°ã€‚ç•¶?‹å??‡åˆ°èª²æ¥­?ç?å¼ã€ç?æ´»ç??ï??–è€…é?è¦ä?å¹«å??†æ??§ç??è½èªéŸ³?å??˜è??‚ï?ç¸½èƒ½è¿…é€Ÿçµ¦?ºæ??†å??ã€å¯¦?¨å?è²¼å??„å»ºè­°ã€?4. ?¶æ??‹å‚³?å??‡æ?èªéŸ³?‚ï?ä»¥æ??‹ç?è¦–è??ªç„¶?æ???5. ?è??·åº¦?©ä¸­ï¼Œæ??ˆæ??°æ?è®€??"""

# ===================================================================
# 4. AI å¥½å??å? (?´å? Gemini ???¬åœ°ç«?Ollama)
# ===================================================================
class AIService:
    def __init__(self):
        # è¨˜æ†¶?¼å?:
        # Gemini ä½¿ç”¨ List[google.genai.types.Content]
        # Ollama ä½¿ç”¨ List[Dict[str, str]] (role, content)
        self._gemini_history: Dict[str, List[Any]] = {}
        self._ollama_history: Dict[str, List[Dict[str, str]]] = {}
        self.max_history_turns = 10

    def is_configured(self) -> bool:
        if settings.AI_PROVIDER.lower() == "ollama":
            return True  # ?¬åœ°ç«¯ä??€è¦?API Key
        # Gemini æ¨¡å?
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")

    def clear_memory(self, user_id: str) -> str:
        self._gemini_history.pop(user_id, None)
        self._ollama_history.pop(user_id, None)
        return f"å¥½å?ï¼ä»¥?è??ç?äº‹æ??½å?æ¸…ç©º?‰ï??‘å€‘é??°é?å§‹ï??³è??‘è?é»ä?éº¼å‘¢ï¼Ÿğ??

    # ---------------------------------------------------------------
    # å°è©±?•ç? (?‡å? + ç¶²å??ªå?è¾¨è?)
    # ---------------------------------------------------------------
    async def chat(self, user_id: str, message: str) -> str:
        text = message.strip()

        # ?è¨­è¨˜æ†¶?‡ä»¤
        if text in ["æ¸…é™¤è¨˜æ†¶", "?è¨­å°è©±", "?°è©±é¡?, "?ç½®", "/reset"]:
            return self.clear_memory(user_id)

        # ç´”ç¶²?€ ???ªå?è§¸ç™¼ç¶²é??˜è?
        urls = re.findall(r'https?://[^\s]+', text)
        if urls and len(text) == len(urls[0]):
            return await self.summarize_url(urls[0])

        provider = settings.AI_PROVIDER.lower()
        if provider == "ollama":
            return await self._chat_ollama(user_id, text)
        else:
            return await self._chat_gemini(user_id, text)

    # ?€?€ Gemini å¯¦ä? ?€?€
    async def _chat_gemini(self, user_id: str, text: str) -> str:
        if not self.is_configured():
            return (
                f"?¨ï??‘æ˜¯?Œ{settings.BOT_NAME}?ğ?‹\n\n"
                "?®å?è¨­å???Gemini æ¨¡å?ï¼Œè???.env å¡«å…¥?‰æ???GEMINI_API_KEYï¼ğ?‘\n"
                "?’¡ ?¥æƒ³å®Œå…¨ä½¿ç”¨?¬åœ°ç«¯å? API Keyï¼Œå¯å°?.env ??AI_PROVIDER ?¹ç‚º ollamaï¼?
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

            # ?¼å« Gemini æ¨¡å?
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=config,
            )
            reply = response.text or "ï¼ˆç??—ç??—ä?ï¼Œä??¥é??éº¼?ï?"

            # ?²å?å°è©±æ­·å²
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
                return (
                    f"?˜µ æ¨¡å????å¤±æ?ï¼šæ‰¾ä¸åˆ°æ¨¡å? `{settings.GEMINI_MODEL}`ï¼\n"
                    f"å»ºè­°??.env å°?GEMINI_MODEL è¨­å???gemini-2.5-flash ??gemini-2.0-flash??
                )
            return f"?¦è??›æ??“ç?äº??˜µ ?¯èª¤ï¼š{err_msg[:120]}"

    # ?€?€ ?¬åœ° Ollama å¯¦ä? ?€?€
    async def _chat_ollama(self, user_id: str, text: str) -> str:
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
                    return f"?¬åœ° Ollama ?æ??¯èª¤ (HTTP {res.status_code})ï¼š{res.text[:120]}"
                
                data = res.json()
                reply = data.get("message", {}).get("content", "").strip() or "ï¼ˆç??—ç??—ä?ï¼Œä??¥é??éº¼?ï?"

                # ?´æ–°è¨˜æ†¶
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
                f"?¡æ?????°æœ¬??Ollama ä¼ºæ???({settings.OLLAMA_HOST}) ??\n"
                "è«‹ç¢ºèªæœ¬?°å·²å®‰è?ä¸¦å???Ollama (?‡ä»¤ï¼š`ollama serve` ??`ollama run llama3.2`)ï¼?
            )
        except Exception as e:
            logger.error(f"Ollama Chat error: {e}", exc_info=True)
            return f"?¬åœ°æ¨¡å??•ç??‚å‡º???˜µ ?¯èª¤ï¼š{str(e)[:120]}"

    # ---------------------------------------------------------------
    # ?–ç?è¾¨è?
    # ---------------------------------------------------------------
    async def analyze_image(self, user_id: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        provider = settings.AI_PROVIDER.lower()

        prompt = (
            f"?‘ç??‹å??³ä??™å¼µ?§ç??‚è?ä»¥å¥½?‹ã€Œ{settings.BOT_NAME}?ç?èªæ°£?æ?ï¼š\n"
            "1. ?Šè¨´?‹å??§ç?äº®é??‚\n"
            "2. ?¥æ˜¯?¶æ?/?¼ç¥¨ï¼šæ??—é?é¡è??é??‚\n"
            "3. ?¥æ˜¯è¬›ç¾©/ç­†è?/ç¨‹å?ç¢¼ï??ƒå??¸å??é?ä¸¦è§£?ã€‚\n"
            "4. ?¥æ˜¯ç¾é?/é¢¨æ™¯/?ªæ?ï¼šç†±?…ä??•ï?"
        )

        # ?€?€ Gemini è¦–è¦º?†æ? ?€?€
        if provider == "gemini":
            if not self.is_configured():
                return "è«‹å???.env è¨­å? GEMINI_API_KEY ?èƒ½è¾¨è??–ç?ï¼ğ??
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
                return response.text or "?‘ç?å®Œç…§?‡ä?ï¼Œæ?è¦ºå??‰è¶£ï¼âœ¨"
            except Exception as e:
                logger.error(f"Image error: {e}", exc_info=True)
                return f"?‹ç…§?‡æ??¼ç??±ä? ?˜µ ?¯èª¤ï¼š{str(e)[:120]}"

        # ?€?€ ?¬åœ° Ollama è¦–è¦º?†æ? (?€?·å?è¦–è¦º?½å??„æ¨¡?‹å? llava / llama3.2-vision) ?€?€
        else:
            try:
                img_b64 = base64.b64encode(image_bytes).decode("utf-8")
                async with httpx.AsyncClient(timeout=60.0) as http:
                    res = await http.post(
                        f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate",
                        json={
                            "model": settings.OLLAMA_MODEL,
                            "prompt": prompt,
                            "images": [img_b64],
                            "stream": False,
                        }
                    )
                    if res.status_code == 200:
                        return res.json().get("response", "?‘ç??é€™å¼µ?–ç?äº†ï?")
                    return f"?¬åœ°æ¨¡å?è¦–è¦ºè¾¨è??€?­é??·å?è¦–è¦º?½å??„æ¨¡??(å¦?llava, llama3.2-vision)?‚HTTP ?¯èª¤ï¼š{res.status_code}"
            except Exception as e:
                logger.error(f"Local Image error: {e}", exc_info=True)
                return f"?¬åœ°?–ç??†æ?å¤±æ? ?˜µ ?¯èª¤ï¼š{str(e)[:120]}"

    # ---------------------------------------------------------------
    # èªéŸ³è¨Šæ¯è¾¨è??‡æ?è¦?    # ---------------------------------------------------------------
    async def transcribe_audio(self, user_id: str, audio_bytes: bytes, mime_type: str = "audio/m4a") -> str:
        provider = settings.AI_PROVIDER.lower()
        if provider != "gemini":
            return "èªéŸ³è¾¨è??Ÿèƒ½?®å?ä¸»è??¯æ´ Gemini æ¨¡å??‚è‹¥?€ä½¿ç”¨è«‹åœ¨ .env å°?AI_PROVIDER ?¹ç‚º geminiï¼ğ?™ï?"

        if not self.is_configured():
            return "è«‹å???.env è¨­å? GEMINI_API_KEY ?èƒ½?•ç?èªéŸ³ï¼ğ?™ï?"

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                f"?™æ˜¯?‘æ??‹ç? LINE èªéŸ³è¨Šæ¯?‚è?ä»¥å¥½?‹ã€Œ{settings.BOT_NAME}?ç?èº«ä»½ï¼š\n"
                "1. ?é€å?ç¨¿ã€‘ï?æº–ç¢ºè¨˜é?èªªä?ä»€éº¼ã€‚\n"
                "2. ?é?é»æ?è¦ã€‘ï?2~3 é»ç²¾?¯ã€‚\n"
                "3. ?éº»?‰å?è¦†ã€‘ï?è¦ªå?æº«æ??°å??‰ã€?
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
            return response.text or "?‘è½å®Œè??³ä?ï¼Œä??æ?é»é??³ï?è¦ä?è¦å??„ä?æ¬¡ï??§"
        except Exception as e:
            logger.error(f"Audio error: {e}", exc_info=True)
            return f"èªéŸ³?•ç?å¤±æ? ?˜µ ?¯èª¤ï¼š{str(e)[:120]}"

    # ---------------------------------------------------------------
    # ç¶²å??‡ç??ªå??Ÿè?
    # ---------------------------------------------------------------
    async def summarize_url(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http:
                res = await http.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            title = soup.title.string.strip() if soup.title and soup.title.string else "?™ç??‡ç?"
            text_content = " ".join(soup.stripped_strings)[:3500]

            prompt = (
                f"?‡ç?æ¨™é?ï¼šã€Š{title}?‹\nç¶²å?ï¼š{url}\n\n?§å®¹ç¯€?„ï?\n{text_content}\n\n"
                f"è«‹ä»¥?‹å??Œ{settings.BOT_NAME}?ç?èªæ°£?´ç?ï¼š\n"
                "1. ?’¡ ä¸€?¥è©±çµè?\n2. ?? 3 é»å?è®€ç²¾è¯\n3. ?’¬ ç°¡çŸ­å¿ƒå??–å»ºè­?
            )

            # ?¼å«?¸æ???AI ?å??¢ç??˜è?
            if settings.AI_PROVIDER.lower() == "ollama":
                async with httpx.AsyncClient(timeout=60.0) as http:
                    res = await http.post(
                        f"{settings.OLLAMA_HOST.rstrip('/')}/api/generate",
                        json={
                            "model": settings.OLLAMA_MODEL,
                            "prompt": prompt,
                            "system": FRIEND_SYSTEM_INSTRUCTION,
                            "stream": False,
                        }
                    )
                    if res.status_code == 200:
                        return res.json().get("response", f"?´ç?å®Œã€Š{title}?‹å?ï¼?)
                    return f"?´ç?å¤±æ?ï¼ŒOllama ?æ??€?‹ï?{res.status_code}"
            else:
                if not self.is_configured():
                    return f"?“åˆ°?Š{title}?‹ä?ï¼Œä?è«‹è¨­å®?GEMINI_API_KEY ?èƒ½å¹«ä??˜è?ï¼ğ??
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
                return response.text or f"?‘ç?å®Œã€Š{title}?‹ä?ï¼?
        except Exception as e:
            logger.error(f"URL error: {e}", exc_info=True)
            return f"è®€?–ç¶²?å¤±???˜¢ ?¯èª¤ï¼š{str(e)[:120]}"


# å»ºç??¨å? AI ?å?å¯¦ä?
ai = AIService()

# ===================================================================
# 5. LINE äº‹ä»¶?•ç?æ¨¡ç?
# ===================================================================
def get_quick_reply():
    try:
        from linebot.v3.messaging import QuickReply, QuickReplyItem, MessageAction
        return QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="?’¬ ?Šè?ä»Šå¤©", text="ä»Šå¤©?å?å¥½å?å¯¦ï?ä½ åœ¨å¹¹å??¢ï?")),
            QuickReplyItem(action=MessageAction(label="?± ä»Šå¤©?ƒä?éº?, text="å¹«æ??³æƒ³?ˆé?/?šé??ƒä?éº¼ï?")),
            QuickReplyItem(action=MessageAction(label="?’¡ ?·çŸ¥è­?, text="è·Ÿæ??†äº«ä¸€?‹æ?è¶???·çŸ¥è­˜ï?")),
            QuickReplyItem(action=MessageAction(label="?? ?è¨­å°è©±", text="?è¨­å°è©±")),
        ])
    except ImportError:
        return None


async def handle_line_event(event: Any):
    """?•ç? LINE Webhook äº‹ä»¶"""
    from linebot.v3.messaging import (
        AsyncApiClient,
        AsyncMessagingApi,
        AsyncMessagingApiBlob,
        Configuration,
        ReplyMessageRequest,
        TextMessage,
        ShowLoadingAnimationRequest,
    )
    from linebot.v3.webhooks import (
        MessageEvent,
        TextMessageContent,
        ImageMessageContent,
        AudioMessageContent,
        FollowEvent,
    )

    line_config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)

    async with AsyncApiClient(line_config) as api_client:
        line_api = AsyncMessagingApi(api_client)
        blob_api = AsyncMessagingApiBlob(api_client)

        # ? å¥½?‹æ­¡è¿è???        if isinstance(event, FollowEvent):
            welcome = (
                f"?ˆå?ï¼æ??¯ã€Œ{settings.BOT_NAME}?âœ¨\n"
                "ä½ ç?å°ˆå±¬ AI ?¯å?ï¼å??‹å??½é?è¦‹ä?ï½ğ?‰\n\n"
                "ä½ å¯ä»¥éš¨?‚è??‘ï?\n"
                "?’¬ ?Šå¤©?è?è«–æ?è«‹æ?è§???é?\n"
                "?“¸ ?³ç…§?‡å¹«ä½ è¾¨è­˜æ•´?†\n"
                "??ï¸??³è??³å¹«ä½ è??å?ç¨¿è??˜è?\n"
                "?? ä¸Ÿç¶²?€å¹«ä?å¿«é€Ÿæ??é?\n\n"
                "å¿«ä?è·Ÿæ?èªªç¬¬ä¸€?¥è©±?§ï???"
            )
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=welcome, quick_reply=get_quick_reply())]
            ))
            return

        # è¨Šæ¯äº‹ä»¶
        if not isinstance(event, MessageEvent):
            return

        user_id = getattr(event.source, "user_id", None) or "default_user"
        reply_token = event.reply_token

        # ?‡å?è¨Šæ¯
        if isinstance(event.message, TextMessageContent):
            await _safe_loading(line_api, user_id)
            reply = await ai.chat(user_id, event.message.text)
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=get_quick_reply())]
            ))

        # ?–ç?è¨Šæ¯
        elif isinstance(event.message, ImageMessageContent):
            await _safe_loading(line_api, user_id, 30)
            try:
                img_bytes = await blob_api.get_message_content(event.message.id)
                reply = await ai.analyze_image(user_id, bytes(img_bytes))
            except Exception as e:
                reply = f"?“å??§ç?å¤±æ? ?¥º ?¯èª¤ï¼š{str(e)[:100]}"
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=get_quick_reply())]
            ))

        # èªéŸ³è¨Šæ¯
        elif isinstance(event.message, AudioMessageContent):
            await _safe_loading(line_api, user_id, 30)
            try:
                audio_bytes = await blob_api.get_message_content(event.message.id)
                reply = await ai.transcribe_audio(user_id, bytes(audio_bytes))
            except Exception as e:
                reply = f"èªéŸ³?¥æ”¶å¤±æ? ?¥º ?¯èª¤ï¼š{str(e)[:100]}"
            await line_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=reply, quick_reply=get_quick_reply())]
            ))


async def _safe_loading(api: Any, chat_id: str, seconds: int = 20):
    """é¡¯ç¤º LINE å®˜æ–¹?“å?è¼‰å…¥ä¸­å???""
    try:
        from linebot.v3.messaging import ShowLoadingAnimationRequest
        await api.show_loading_animation(
            ShowLoadingAnimationRequest(chat_id=chat_id, loading_seconds=seconds)
        )
    except Exception:
        pass


# ===================================================================
# 6. FastAPI ä¼ºæ??¨è??§å»º?¬åœ°ç«?Web ?Šå¤©å®?# ===================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 65)
    logger.info(f"??LINE AI å¥½å??Œ{settings.BOT_NAME}?æ??™å·²?Ÿå?ï¼?)
    logger.info(f"?? ?®å? AI å¼•æ?ï¼š{settings.AI_PROVIDER.upper()}")
    if settings.AI_PROVIDER.lower() == "gemini":
        logger.info(f"?“¦ Gemini æ¨¡å?ï¼š{settings.GEMINI_MODEL}")
    else:
        logger.info(f"?’» ?¬åœ° Ollama æ¨¡å?ï¼š{settings.OLLAMA_MODEL} ({settings.OLLAMA_HOST})")
    
    logger.info(f"?? ?¬åœ° Web æ¸¬è©¦?Šå¤©å®¤ï?http://localhost:{settings.PORT}")
    logger.info(f"?? LINE Webhook ?¥æ”¶é»ï?http://localhost:{settings.PORT}/callback")
    logger.info("-" * 65)
    logger.info("?’¡ ?ç¤ºï¼šè‹¥è¦åœ¨ LINE ä¸Šä½¿?¨ï?è«‹é€é? ngrok ?‹å??§é?ä¸¦å¡«??Webhook URLï¼?)
    logger.info(f"   ?‡ä»¤ï¼šngrok http {settings.PORT}")
    logger.info("=" * 65)
    yield
    logger.info(f"???Œ{settings.BOT_NAME}?å·²ä¸‹ç?")


app = FastAPI(
    title=f"LINE AI Friend - {settings.BOT_NAME}",
    version="2.0.0",
    lifespan=lifespan
)


# ?€?€ ?§å»º?¬åœ° Web ?Šå¤©å®?HTML ä»‹é¢ ?€?€
WEB_CHAT_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI ?¨èº«å¥½å??Œå??‰ã€? ?¬åœ°æ¸¬è©¦?§åˆ¶??/title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Noto Sans TC', sans-serif;
      background: linear-gradient(135deg, #f5f7fb 0%, #e8edf5 100%);
      color: #333;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 12px;
    }
    .chat-container {
      width: 100%;
      max-width: 820px;
      height: 94vh;
      background: #ffffff;
      border-radius: 20px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.08);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid #eef2f6;
    }
    .header {
      background: #06c755;
      color: white;
      padding: 16px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header-info h1 { font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
    .header-info p { font-size: 0.85rem; opacity: 0.9; margin-top: 4px; }
    .status-badge {
      font-size: 0.78rem;
      background: rgba(255,255,255,0.25);
      padding: 6px 12px;
      border-radius: 20px;
      font-weight: 500;
      backdrop-filter: blur(4px);
    }
    .chat-box {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      background: #fafbfe;
    }
    .msg {
      max-width: 82%;
      padding: 12px 18px;
      border-radius: 16px;
      line-height: 1.6;
      font-size: 0.95rem;
      word-break: break-word;
      white-space: pre-wrap;
    }
    .msg.bot {
      align-self: flex-start;
      background: #ffffff;
      border: 1px solid #e9ecef;
      color: #2b2f38;
      border-bottom-left-radius: 4px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .msg.user {
      align-self: flex-end;
      background: #06c755;
      color: white;
      border-bottom-right-radius: 4px;
      box-shadow: 0 2px 6px rgba(6,199,85,0.25);
    }
    .msg-time {
      font-size: 0.72rem;
      margin-top: 4px;
      opacity: 0.7;
      text-align: right;
    }
    .quick-actions {
      display: flex;
      gap: 8px;
      padding: 8px 16px;
      background: #f1f3f7;
      overflow-x: auto;
      white-space: nowrap;
      border-top: 1px solid #e8ecf1;
    }
    .quick-btn {
      background: white;
      border: 1px solid #dce2ea;
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 0.82rem;
      cursor: pointer;
      color: #495057;
      transition: all 0.2s;
    }
    .quick-btn:hover { background: #e9f8ee; border-color: #06c755; color: #06c755; }
    .input-area {
      padding: 14px 18px;
      background: #ffffff;
      border-top: 1px solid #eef2f6;
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .input-area textarea {
      flex: 1;
      height: 48px;
      border: 1px solid #dce2ea;
      border-radius: 12px;
      padding: 12px 14px;
      font-size: 0.95rem;
      font-family: inherit;
      resize: none;
      outline: none;
      transition: border 0.2s;
    }
    .input-area textarea:focus { border-color: #06c755; }
    .send-btn {
      background: #06c755;
      color: white;
      border: none;
      border-radius: 12px;
      padding: 0 20px;
      height: 48px;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    .send-btn:hover { background: #05b34c; }
    .send-btn:disabled { background: #b0e5c5; cursor: not-allowed; }
    .loading-dot { display: inline-block; animation: wave 1.2s infinite ease-in-out; }
    @keyframes wave { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="header">
      <div class="header-info">
        <h1>??AI å¥½å??Œå??‰ã€?span style="font-size: 0.8rem; font-weight: normal; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 10px;">?¬åœ°æ¸¬è©¦??/span></h1>
        <p>å¼•æ?ï¼?span id="providerInfo">è¼‰å…¥ä¸?..</span> | æ¨¡å?ï¼?span id="modelInfo">...</span></p>
      </div>
      <div class="status-badge" id="statusBadge">æª¢æ¸¬???ä¸?..</div>
    </div>

    <div class="chat-box" id="chatBox">
      <div class="msg bot">
        ?ˆå?ï¼æ??¯ã€Œå??‰ã€âœ¨ ä½ ç?å°ˆå±¬ AI ?¯å?ï¼?br>
        ä½ åœ¨?¬åœ°ç«¯éš¨?‚å¯ä»¥è??‘è??Šå¤©?ä?ç¶²å?è®“æ??Ÿè?ï¼Œæ??¯é??Šä??¹å¿«?Ÿæ??•è©¦è©¦ç??”ï???
        <div class="msg-time">ç³»çµ±?è¨­</div>
      </div>
    </div>

    <div class="quick-actions">
      <button class="quick-btn" onclick="sendQuick('ä»Šå¤©?å?å¥½å?å¯¦ï?ä½ åœ¨å¹¹å??¢ï?')">?’¬ ?Šè?ä»Šå¤©</button>
      <button class="quick-btn" onclick="sendQuick('å¹«æ??³æƒ³?ˆé?/?šé??ƒä?éº¼ï?')">?± ä»Šå¤©?ƒä?éº?/button>
      <button class="quick-btn" onclick="sendQuick('è·Ÿæ??†äº«ä¸€?‹æ?è¶???·çŸ¥è­˜ï?')">?’¡ ?‰è¶£?·çŸ¥è­?/button>
      <button class="quick-btn" onclick="sendQuick('https://zh.wikipedia.org/wiki/äººå·¥?ºæ…§')">?? æ¸¬è©¦ç¶­åŸº?¾ç??˜è?</button>
      <button class="quick-btn" onclick="sendQuick('?è¨­å°è©±')">?? ?è¨­å°è©±è¨˜æ†¶</button>
    </div>

    <div class="input-area">
      <textarea id="userInput" placeholder="è¼¸å…¥è¨Šæ¯... (Enter ?å‡ºï¼ŒShift+Enter ?›è?)" onkeydown="handleKey(event)"></textarea>
      <button class="send-btn" id="sendBtn" onclick="sendMessage()">?å‡º</button>
    </div>
  </div>

  <script>
    const chatBox = document.getElementById('chatBox');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const statusBadge = document.getElementById('statusBadge');
    const providerInfo = document.getElementById('providerInfo');
    const modelInfo = document.getElementById('modelInfo');

    async function checkHealth() {
      try {
        const res = await fetch('/health');
        const data = await res.json();
        providerInfo.textContent = data.provider.toUpperCase();
        modelInfo.textContent = data.model;
        if (data.status === 'healthy') {
          statusBadge.textContent = '?Ÿ¢ ?å?å°±ç?';
          statusBadge.style.background = 'rgba(255,255,255,0.3)';
        } else {
          statusBadge.textContent = '?Ÿ¡ ?ªè¨­å®šå???;
        }
      } catch (e) {
        statusBadge.textContent = '?”´ ????°å¸¸';
      }
    }
    checkHealth();

    function appendMessage(text, role) {
      const msg = document.createElement('div');
      msg.className = `msg ${role}`;
      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      msg.innerHTML = `${text}<div class="msg-time">${now}</div>`;
      chatBox.appendChild(msg);
      chatBox.scrollTop = chatBox.scrollHeight;
      return msg;
    }

    async function sendMessage() {
      const text = userInput.value.trim();
      if (!text) return;

      appendMessage(text, 'user');
      userInput.value = '';
      sendBtn.disabled = true;

      const loadingMsg = appendMessage('å°å?æ­?œ¨?è€ƒä¸­... ?’­', 'bot');

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, user_id: 'web_tester' })
        });
        const data = await res.json();
        loadingMsg.innerHTML = `${data.reply}<div class="msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>`;
      } catch (err) {
        loadingMsg.innerHTML = `? ï? ????¯èª¤ï¼?{err.message}<div class="msg-time">?¯èª¤</div>`;
      } finally {
        sendBtn.disabled = false;
        userInput.focus();
        chatBox.scrollTop = chatBox.scrollHeight;
      }
    }

    function sendQuick(txt) {
      userInput.value = txt;
      sendMessage();
    }

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    """?¬åœ°ç«¯æ??‹ç€è¦½?¨æ??´æ¥?ˆç¾ Web æ¸¬è©¦?Šå¤©å®?""
    return HTMLResponse(content=WEB_CHAT_HTML)


# ?€?€ ?¬åœ°æ¸¬è©¦ API ?€?€
class LocalChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "web_user"


@app.post("/api/chat")
async def local_chat_api(req: LocalChatRequest):
    """ä¾›æœ¬??Web æ¸¬è©¦?é¢?‡é??¼è€…é™¤?¯ç›´?¥èª¿?¨ç??Šå¤©ç«¯é?"""
    reply = await ai.chat(user_id=req.user_id, message=req.message)
    return {"reply": reply, "user_id": req.user_id, "provider": settings.AI_PROVIDER}


@app.get("/health")
async def health():
    """?å??¥åº·æª¢æŸ¥?‡ç??‹è¨º??""
    provider = settings.AI_PROVIDER.lower()
    is_gemini = provider == "gemini"
    is_ollama = provider == "ollama"

    return {
        "status": "healthy",
        "bot": settings.BOT_NAME,
        "provider": settings.AI_PROVIDER,
        "model": settings.GEMINI_MODEL if is_gemini else settings.OLLAMA_MODEL,
        "gemini_key_set": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "line_secret_set": bool(settings.LINE_CHANNEL_SECRET and settings.LINE_CHANNEL_SECRET != "your_line_channel_secret_here"),
        "line_token_set": bool(settings.LINE_CHANNEL_ACCESS_TOKEN and settings.LINE_CHANNEL_ACCESS_TOKEN != "your_line_channel_access_token_here"),
    }


# ?€?€ LINE Webhook ?€?€
@app.post("/callback")
async def callback(
    request: Request,
    x_line_signature: str = Header(None, alias="X-Line-Signature")
):
    """?•ç?ä¾†è‡ª LINE å®˜æ–¹ä¼ºæ??¨ç? Webhook è«‹æ?"""
    if not settings.LINE_CHANNEL_SECRET or settings.LINE_CHANNEL_SECRET == "your_line_channel_secret_here":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LINE_CHANNEL_SECRET å°šæœªè¨­å?ï¼Œè???.env ä¸­å¡«å¯«ï?"
        )

    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = (await request.body()).decode("utf-8")

    from linebot.v3 import WebhookParser
    from linebot.v3.exceptions import InvalidSignatureError

    parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

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
# 7. ?¬åœ°çµ‚ç«¯æ©?(CLI) äº’å?æ¨¡å?
# ===================================================================
async def run_cli_mode():
    """?¨ç?ç«¯æ?ä¸­ç›´?¥è?å°å?äº’å?ï¼Œä??€?¶è¨­ä»»ä? Web ä¼ºæ??¨æ? LINE å¸³è?"""
    print("=" * 65)
    print(f"??æ­¡è??²å…¥?{settings.BOT_NAME}?‘æœ¬?°ç?ç«¯æ?å°è©±æ¨¡å?ï¼?)
    print(f"?? ?®å? AI å¼•æ?ï¼š{settings.AI_PROVIDER.upper()}")
    model_name = settings.GEMINI_MODEL if settings.AI_PROVIDER.lower() == "gemini" else settings.OLLAMA_MODEL
    print(f"?“¦ æ¨¡å??ç¨±ï¼š{model_name}")
    print("-" * 65)
    print("?’¡ ?¹æ??‡ä»¤ï¼?)
    print("   - è¼¸å…¥ `/reset` ??`?è¨­å°è©±` æ¸…ç©ºè¨˜æ†¶")
    print("   - ?´æ¥è²¼ä?ç¶²å??ªå??Ÿæ? 3 é»é€Ÿè??˜è?")
    print("   - è¼¸å…¥ `/exit` ??`exit` ?¢é?çµ‚ç«¯æ©Ÿæ¨¡å¼?)
    print("=" * 65 + "\n")

    user_id = "cli_tester"
    while True:
        try:
            user_input = input("ä½?> ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "exit", "quit", ":q"]:
                print(f"\n{settings.BOT_NAME} > ?°æ°?‰ï??‰ç©º?ä??¾æ??Šå¤©ï¼ğ?‹âœ¨")
                break

            print(f"{settings.BOT_NAME} æ­?œ¨?è€ƒä¸­... ?’­")
            reply = await ai.chat(user_id, user_input)
            print(f"\n{settings.BOT_NAME} >\n{reply}\n")
            print("-" * 50)
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{settings.BOT_NAME} > ?°æ°?‰ï???")
            break
        except Exception as e:
            print(f"\n? ï? ?¼ç??¯èª¤ï¼š{e}\n")


# ===================================================================
# 8. ç¨‹å??´æ¥?·è??¥å£
# ===================================================================
if __name__ == "__main__":
    import asyncio

    # ?¥å‚³??--cli ?ƒæ•¸ï¼Œç›´?¥é€²å…¥çµ‚ç«¯æ©Ÿå?è©?    if "--cli" in sys.argv:
        asyncio.run(run_cli_mode())
    else:
        import uvicorn
        uvicorn.run("bot:app", host=settings.HOST, port=settings.PORT, reload=True)
