# config.py
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen3.5:4b"
THINK = False
STREAM = False

# main.py

from core.orchestrator.orchestrator import Orchestrator


def main():
    orchestrator = Orchestrator()

    print("================================")
    print("        My Personal AI")
    print("================================")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "history":
            print("---- Current history ----")
            print(orchestrator.agent.context.get_messages())
            print("--------------------------")
            continue

        response = orchestrator.process(user_input)

        # Only print here when streaming is disabled
        if not STREAM:
            print(f"\nAI: {response}\n")


if __name__ == "__main__":
    main()

# agent_loop.py

from core.agent.context import Context
from core.agent.response import Response
from models.model_manager import ModelManager

from app.config import STREAM, THINK


class AgentLoop:
    def __init__(self):
        self.context = Context()
        self.model_manager = ModelManager()

    def run(self, user_input: str) -> Response:
        self.context.add_user_message(user_input)

        messages = self.context.get_messages()

        answer = self.model_manager.chat(messages, stream=STREAM, think=THINK)

        self.context.add_assistant_message(answer)

        return Response(text=answer, model=self.model_manager.model)


#  context.py

from core.prompts.system_propmt import SYSTEM_PROMPT


class Context:
    def __init__(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict]:
        return self.messages


#  reposense.py
class Response:
    def __init__(self, text: str, model: str):
        self.text = text
        self.model = model
        self.success = True


#  orchestrator.py
from core.agent.agent_loop import AgentLoop


class Orchestrator:
    def __init__(self):
        self.agent = AgentLoop()

    def process(self, user_input: str):
        response = self.agent.run(user_input)
        return response.text


#  system_propmt.py
SYSTEM_PROMPT = """You are Mopi, a personal AI agent 

IDENTITY:
- You help the user manage tasks, answer questions.
- You are running fully locally

RESPONSE STYLE:
- Be concise. No filler, no excessive enthusiasm, no unnecessary emoji.
- Default to short answers. Only elaborate if the user asks for detail.

CURRENT CAPABILITIES:
- Right now you can only chat. You do NOT yet have access to files, apps, or the shell.
- Never claim to have performed an action you cannot actually perform.
- If asked to do something you can't do yet, say so clearly instead of pretending.

SAFETY:
- Never provide instructions for illegal, unsafe, or unethical activities.
- Never perform destructive or irreversible actions (deleting files, overwriting data on your own without the permission of the super admin, 
  running system-level commands) without explicit confirmation from the user first.
"""

#  model_manager.py

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


#  client.py

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
