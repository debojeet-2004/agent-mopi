from core.agent.agent_loop import AgentLoop


class Orchestrator:
    def __init__(self):
        self.agent = AgentLoop()

    def process(self, user_input: str):
        response = self.agent.run(user_input)
        return response.text
