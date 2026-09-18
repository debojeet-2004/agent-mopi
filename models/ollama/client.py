import json
from typing import Literal, TypeAlias

import httpx

from app.config import OLLAMA_BASE_URL

ThinkValue: TypeAlias = bool | Literal["low", "medium", "high", "max"]


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
        think: ThinkValue = False,
    ):

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "think": think,
            "keep_alive": "30m",
        }

        # Non-streaming response
        if not stream:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=None,
            )

            response.raise_for_status()

            return response.json()["message"]["content"]

        # Streaming response
        answer = ""

        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=None,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                data = json.loads(line)

                content = data.get("message", {}).get("content", "")

                if content:
                    print(content, end="", flush=True)
                    answer += content

                if data.get("done"):
                    break

        print()

        return answer
