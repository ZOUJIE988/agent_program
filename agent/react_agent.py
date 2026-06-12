from utils.config import *
from agent.base_agent import Base_Agent
from tools.base_tool import react_tool,react_handlers
from utils.prompt_config import *


class ReactAgent:
    def __init__(self,tools=None, handlers=None):
        self.system_prompt = react_system_prompt
        self.base_agent = Base_Agent(
            tools=tools or [],
            handlers=handlers or {}
        )

    def run(self,query:str,
            system_prompt: str = "",
            user_id: str = "default",
            session_id: str = None,
            ):
        final_system_prompt = f"{system_prompt}\n\n{self.system_prompt}" if system_prompt else self.system_prompt
        return self.base_agent.run_with_tools(
            query=query,
            system_prompt=final_system_prompt,
            session_id=session_id,
            user_id=user_id,
            use_cache=True,
            use_session=True,
            use_long_memory=True
        )

react_agent=ReactAgent(tools=react_tool,handlers=react_handlers)