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
