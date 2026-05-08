import os
import requests
from dotenv import load_dotenv

load_dotenv()

FASTGPT_API_URL = os.getenv("FASTGPT_API_URL")
FASTGPT_API_KEY = os.getenv("FASTGPT_API_KEY")


def ask_fastgpt(user_text):
    headers = {
        "Authorization": f"Bearer {FASTGPT_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "chatId": "test_user_001",
        "stream": False,
        "detail": False,
        "messages": [
            {
                "role": "user",
                "content": user_text
            }
        ]
    }

    response = requests.post(
        FASTGPT_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    return result.get("choices", [{}])[0].get("message", {}).get("content", "")