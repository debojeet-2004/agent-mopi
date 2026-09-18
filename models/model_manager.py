from models.ollama.client import OllamaClient, ThinkValue

from app.config import MODEL_NAME, STREAM


class ModelManager:
    def __init__(self):
        self.model = MODEL_NAME
        self.client = OllamaClient()

    def chat(
        self,
        messages: list[dict],
        stream: bool = STREAM,
        think: ThinkValue = False,
    ) -> str:
        return self.client.chat(
            model=self.model,
            messages=messages,
            stream=stream,
            think=think,
        )
