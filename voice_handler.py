import os
import json
import aiohttp
from dotenv import load_dotenv

load_dotenv()

STT_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"


async def recognize_audio(audio_bytes: bytes) -> str:
    api_key = os.getenv("YANDEX_API_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    if not api_key or not folder_id:
        return ""
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "x-folder-id": folder_id,
        "Content-Type": "application/octet-stream",
    }
    params = {
        "topic": "general",
        "lang": "ru-RU",
        "format": "oggopus",
        "sampleRateHertz": "48000",
    }
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(STT_URL, headers=headers, params=params, data=audio_bytes) as r:
                text = await r.text()
                if r.status == 200:
                    return json.loads(text).get("result", "")
                print(f"STT error ({r.status}): {text[:300]}")
                return ""
    except Exception as e:
        print(f"STT request failed: {e}")
        return ""


async def download_audio(url: str) -> bytes:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    return await r.read()
                print(f"Download error ({r.status})")
                return b""
    except Exception as e:
        print(f"Download failed: {e}")
        return b""
