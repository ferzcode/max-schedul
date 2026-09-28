import os
import json
import aiohttp
from dotenv import load_dotenv

load_dotenv()


async def ask(question: str, context: str = "") -> str:
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    iam_token = os.getenv("YANDEX_IAM_TOKEN")

    if not iam_token:
        return "IAM-токен не задан в .env"

    system_text = (
        "Ты — помощник студентов ИРНИТУ по расписанию. "
        "Отвечай кратко и по делу на русском языке. "
        "Используй ТОЛЬКО данные из расписания ниже. "
        "Время окончания пары уже указано (начало–конец), не вычисляй его сам. "
        "Если данных нет — честно скажи об этом."
    )
    if context:
        system_text += f"\n\n=== РАСПИСАНИЕ ===\n{context}\n=== КОНЕЦ РАСПИСАНИЯ ==="

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 700,
        },
        "messages": [
            {"role": "system", "text": system_text},
            {"role": "user", "text": question},
        ],
    }

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as r:
                text = await r.text()
                if r.status == 200:
                    data = json.loads(text)
                    return data["result"]["alternatives"][0]["message"]["text"]
                return f"Ошибка API ({r.status}): {text[:300]}"
    except Exception as e:
        return f"Ошибка запроса: {e}"