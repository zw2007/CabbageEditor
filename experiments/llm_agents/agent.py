import asyncio
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Union

from autogen_core import TopicId, RoutedAgent, FunctionCall, DefaultTopicId, MessageContext, message_handler, \
    SingleThreadedAgentRuntime, default_subscription
from autogen_core.models import AssistantMessage, ChatCompletionClient, LLMMessage, SystemMessage, UserMessage
from autogen_core.tool_agent import ToolAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

                                
_original_del_proactor = asyncio.proactor_events._ProactorBasePipeTransport.__del__
_original_del_subprocess = asyncio.base_subprocess.BaseSubprocessTransport.__del__

@dataclass
class CodeWritingTask:
    task: str

@dataclass
class CodeWritingResult:
    task: str
    code: str
    review: str

@dataclass
class CodeReviewTask:
    session_id: str
    code_writing_task: str
    code_writing_scratchpad: str
    code: str

@dataclass
class CodeReviewResult:
    review: str
    session_id: str
    approved: bool

@default_subscription                               
class CodeGenerator(RoutedAgent):
    """An agent that performs code writing tasks."""

    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A code writing agent.")
        self._system_messages: List[LLMMessage] = [
            SystemMessage(
                content="""You are a proficient coder. You write code to solve problems.
                Work with the reviewer to improve your code.
                Always put all finished code in a single Markdown code block.
                For example:
                ```python
                def hello_world():
                    print("Hello, World!")
                ```

                Respond using the following format:

                Thoughts: <Your comments>
                Code: <Your code>
                """,
            )
        ]
        self._model_client = model_client
        self._session_memory: Dict[str, List[CodeWritingTask | CodeReviewTask | CodeReviewResult]] = {}   
                                                               
    @message_handler
    async def handle_code_writing_task(self, message: CodeWritingTask, ctx: MessageContext) -> None:
                                                                         
        session_id = str(uuid.uuid4())
        self._session_memory.setdefault(session_id, []).append(message)                        
                                                            
        response = await self._model_client.create(
            self._system_messages + [UserMessage(content=message.task, source=self.metadata["type"])],
            cancellation_token=ctx.cancellation_token,
        )
        assert isinstance(response.content, str)
                                                   
        code_block = self._extract_code_block(response.content)
        if code_block is None:
            raise ValueError("Code block not found.")
                                    
        code_review_task = CodeReviewTask(
            session_id=session_id,
            code_writing_task=message.task,
            code_writing_scratchpad=response.content,
            code=code_block,
        )
                                                           
        self._session_memory[session_id].append(code_review_task)
                                     
        await self.publish_message(code_review_task, topic_id=TopicId("default", self.id.key))

    @message_handler
    async def handle_code_review_result(self, message: CodeReviewResult, ctx: MessageContext) -> None:
                                                        
        self._session_memory[message.session_id].append(message)
                                                    
                                                                     
        review_request = next(
            m for m in reversed(self._session_memory[message.session_id]) if isinstance(m, CodeReviewTask)
        )
        assert review_request is not None
                                                                                 
        if message.approved:

                                       
            escaped_code = json.dumps(review_request.code)

                                              
            await self.publish_message(
                FunctionCall(
                    id=message.session_id,
                    arguments = f'{{"code":{escaped_code}}}',
                    name="execute_blender_code",
                ),
                topic_id=TopicId("default", self.id.key),
            )

            print("Code Writing Result:")
            print("-" * 80)
            print(f"Task:\n{review_request.code_writing_task}")
            print("-" * 80)
            print(f"Code:\n{review_request.code}")
            print("-" * 80)
            print(f"Review:\n{message.review}")
            print("-" * 80)
        else:                                   
                                                                 
            messages: List[LLMMessage] = [*self._system_messages]              
            for m in self._session_memory[message.session_id]:
                if isinstance(m, CodeReviewResult):
                    messages.append(UserMessage(content=m.review, source="Reviewer"))
                elif isinstance(m, CodeReviewTask):
                    messages.append(AssistantMessage(content=m.code_writing_scratchpad, source="Coder"))
                elif isinstance(m, CodeWritingTask):
                    messages.append(UserMessage(content=m.task, source="User"))
                else:
                    raise ValueError(f"Unexpected message type: {m}")
                                                                
            response = await self._model_client.create(messages, cancellation_token=ctx.cancellation_token)
            assert isinstance(response.content, str)
                                                       
            code_block = self._extract_code_block(response.content)
            if code_block is None:
                raise ValueError("Code block not found.")
                                            
            code_review_task = CodeReviewTask(
                session_id=message.session_id,
                code_writing_task=review_request.code_writing_task,
                code_writing_scratchpad=response.content,
                code=code_block,
            )
                                                               
            self._session_memory[message.session_id].append(code_review_task)
                                             
            await self.publish_message(code_review_task, topic_id=TopicId("default", self.id.key))

    def _extract_code_block(self, markdown_text: str) -> Union[str, None]:
        pattern = r"```(\w+)\n(.*?)\n```"
                                                     
        match = re.search(pattern, markdown_text, re.DOTALL)
                                                                 
        if match:
            return match.group(2)
        return None
@default_subscription
class CodeReviewer(RoutedAgent):
    """An agent that performs code review tasks."""

    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A code reviewer agent.")
        self._system_messages: List[LLMMessage] = [
            SystemMessage(
                content="""You are a code reviewer. You focus on correctness, efficiency and safety of the code.
                    Respond using the following JSON format:
                    {
                        "correctness": "<Your comments>",
                        "efficiency": "<Your comments>",
                        "safety": "<Your comments>",
                        "approval": "<APPROVE or REVISE>",
                        "suggested_changes": "<Your comments>"
                    }
                    """,
            )
        ]
        self._session_memory: Dict[str, List[CodeReviewTask | CodeReviewResult]] = {}
        self._model_client = model_client

    @message_handler
    async def handle_code_review_task(self, message: CodeReviewTask, ctx: MessageContext) -> None:
                                                
                                                    
        previous_feedback = ""
        if message.session_id in self._session_memory:
            previous_review = next(
                (m for m in reversed(self._session_memory[message.session_id]) if isinstance(m, CodeReviewResult)),
                None,
            )
            if previous_review is not None:
                previous_feedback = previous_review.review
                                                                         
        self._session_memory.setdefault(message.session_id, []).append(message)
        prompt = f"""The problem statement is: {message.code_writing_task}
                    The code is:
                    ```
                    {message.code}
                    ```

                    Previous feedback:
                    {previous_feedback}

                    Please review the code. If previous feedback was provided, see if it was addressed.
                    """
                                                            
        response = await self._model_client.create(
            self._system_messages + [UserMessage(content=prompt, source=self.metadata["type"])],
            cancellation_token=ctx.cancellation_token,
            json_output=True,
        )
        assert isinstance(response.content, str)
                                                                                                                 
                                  
        review = json.loads(response.content)
                                    
        review_text = "Code review:\n" + "\n".join([f"{k}: {v}" for k, v in review.items()])
        approved = review["approval"].lower().strip() == "approve"
        result = CodeReviewResult(
            review=review_text,
            session_id=message.session_id,
            approved=approved,
        )
                                                        
        self._session_memory[message.session_id].append(result)
                                    
        await self.publish_message(result, topic_id=TopicId("default", self.id.key))

@default_subscription                               
class Blender_excute_Agent(ToolAgent):
    """You are a helpful assistant. You can use various tools via MCP."""

    def __init__(self,  tools) -> None:
        super().__init__("You can use various tools via MCP.",tools)

async def main():

    runtime = SingleThreadedAgentRuntime()
    model_client = OpenAIChatCompletionClient(
        model= "deepseek-chat",
        base_url= "https://api.deepseek.com/v1",
        api_key= "sk-4299e9946c664f45b2be44b350148dfa",
        model_info= {
            "vision": False,
            "function_calling": True,
            "family": "unknown",
            "json_output": True,
        }
    )
    await CodeReviewer.register(runtime, "CodeReviewer", lambda: CodeReviewer(model_client=model_client))
    await CodeGenerator.register(runtime, "CodeGenerator", lambda: CodeGenerator(model_client=model_client))

    desktop = str(Path.home())
    server_params = StdioServerParams(
        command="cmd", args=["/c", "uvx", "blender-mcp", desktop]
    )
                                                
                           
    tools = await mcp_server_tools(server_params)
    await Blender_excute_Agent.register(runtime, "Blender_excute_Agent", lambda: Blender_excute_Agent(tools))

    runtime.start()
    await runtime.publish_message(
        message=CodeWritingTask(task="帮我在blender中创建一个猴头模型，并且猴头上有一个球体"),
        topic_id=DefaultTopicId(),
    )

                                          
    await runtime.stop_when_idle()
    await asyncio.sleep(3)
            
    loop.stop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
                                 
        loop.run_until_complete(asyncio.sleep(0.1))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())               
        loop.close()
