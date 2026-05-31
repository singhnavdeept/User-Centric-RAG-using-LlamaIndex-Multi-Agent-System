import asyncio
import os
import nest_asyncio
from llama_index.core.agent import ReActAgent as WorkflowReActAgent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

class ReActAgent:
    @classmethod
    def from_tools(cls, tools, llm, system_prompt=None, verbose=False, **kwargs):
        # Instantiate the new WorkflowReActAgent
        workflow_agent = WorkflowReActAgent(
            tools=tools, 
            llm=llm, 
            system_prompt=system_prompt, 
            verbose=verbose
        )
        return cls(workflow_agent)

    class WrapperMemory:
        def __init__(self):
            self.history = []
        def get_all(self):
            return self.history
        def get(self):
            return self.history
        def set(self, history):
            self.history = list(history) if history else []

    def __init__(self, workflow_agent):
        self.agent = workflow_agent
        self.memory = self.WrapperMemory()

    def chat(self, message, chat_history=None):
        nest_asyncio.apply()
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Initialize memory with existing chat history
        if chat_history is not None:
            self.memory.set(chat_history)
        else:
            self.memory.set([])
        
        # Run workflow agent synchronously
        async def _run_agent():
            return await self.agent.run(user_msg=message, chat_history=self.memory.get())
        result = loop.run_until_complete(_run_agent())
        
        # Convert result to string response
        response_str = str(result)
        
        # Append message history
        user_msg = ChatMessage(role=MessageRole.USER, content=message)
        assistant_msg = ChatMessage(role=MessageRole.ASSISTANT, content=response_str)
        self.memory.history.append(user_msg)
        self.memory.history.append(assistant_msg)
        
        return result
