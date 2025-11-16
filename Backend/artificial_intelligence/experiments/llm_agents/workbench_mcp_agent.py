import json
import warnings
from dataclasses import dataclass
from typing import List

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import AgentId, SingleThreadedAgentRuntime
from autogen_core import (
    FunctionCall,
    MessageContext,
    RoutedAgent,
    message_handler,
)
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import ToolResult, Workbench
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench
from autogen_ext.tools.mcp import StdioServerParams

warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed transport")

@dataclass
class Message:
    content: str


class WorkbenchAgent(RoutedAgent):
    def __init__(
        self, model_client: ChatCompletionClient, model_context: ChatCompletionContext, workbench: Workbench
    ) -> None:
        super().__init__("An agent with a workbench")
        self._system_messages: List[LLMMessage] = [SystemMessage(content="You are a helpful AI assistant.")]
        self._model_client = model_client
        self._model_context = model_context
        self._workbench = workbench

    @message_handler
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
                                                    
        await self._model_context.add_message(UserMessage(content=message.content, source="user"))
        print("---------User Message-----------")
        print(message.content)

                                                 
        create_result = await self._model_client.create(
            messages=self._system_messages + (await self._model_context.get_messages()),
            tools=(await self._workbench.list_tools()),
            cancellation_token=ctx.cancellation_token,
        )

                             
        while isinstance(create_result.content, list) and all(
            isinstance(call, FunctionCall) for call in create_result.content
        ):
            print("---------Function Calls-----------")
            for call in create_result.content:
                print(call)

                                                          
            await self._model_context.add_message(AssistantMessage(content=create_result.content, source="assistant"))

                                                 
            print("---------Function Call Results-----------")
            results: List[ToolResult] = []
            for call in create_result.content:
                result = await self._workbench.call_tool(
                    call.name, arguments=json.loads(call.arguments), cancellation_token=ctx.cancellation_token
                )
                results.append(result)
                print(result)

                                                                      
            await self._model_context.add_message(
                FunctionExecutionResultMessage(
                    content=[
                        FunctionExecutionResult(
                            call_id=call.id,
                            content=result.to_text(),
                            is_error=result.is_error,
                            name=result.name,
                        )
                        for call, result in zip(create_result.content, results, strict=False)
                    ]
                )
            )

                                                                                                     
            create_result = await self._model_client.create(
                messages=self._system_messages + (await self._model_context.get_messages()),
                tools=(await self._workbench.list_tools()),
                cancellation_token=ctx.cancellation_token,
            )

                                                     
        assert isinstance(create_result.content, str)

        print("---------Final Response-----------")
        print(create_result.content)

                                                         
        await self._model_context.add_message(AssistantMessage(content=create_result.content, source="assistant"))

                                         
        return Message(content=create_result.content)


class AiAgent(RoutedAgent):
    """An agent that answer the question from user."""

    def __init__(self, model_client: ChatCompletionClient, name:str) -> None:
        super().__init__("A AI agent.")
        self._delegate = AssistantAgent(name, model_client=model_client)

    @message_handler
    async def handle_code_writing_task(self, message: Message, ctx: MessageContext) -> None:
                                                                      
        response = await self._delegate.on_messages(
            [TextMessage(content=message.content, source="user")], ctx.cancellation_token
        )
        print(f"{response.chat_message.content}")


                                                                          
async def main_wrapper_async():
    global runtime
               
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-4299e9946c664f45b2be44b350148dfa",
        model_info={
            "vision": False,
            "function_calling": True,
            "family": "unknown",
            "json_output": True,
        }
    )

    runtime = SingleThreadedAgentRuntime()
    await AiAgent.register(
        runtime,
        "AiAgent",
        lambda: AiAgent(model_client=model_client, name="Aiagent"),
    )

    content = "帮我在blender中建个猴头"

                                    
    blender_server_command = StdioServerParams(
        mode="stdio",                                   
        command="blender-mcp",
        args=["--host", "127.0.0.1", "--port", "9876"]
    )

    runtime.start()

    async with McpWorkbench(blender_server_command) as workbench:
        await WorkbenchAgent.register(
            runtime=runtime,
            type="BlenderAgent",
            factory=lambda: WorkbenchAgent(
                model_client=model_client,
                model_context=BufferedChatCompletionContext(buffer_size=10),
                workbench=workbench,
            ),
        )
        await runtime.send_message(
            Message(content=content),
            recipient=AgentId("BlenderAgent", "default"),
        )

                                 
    await runtime.stop()


def main_wrapper():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_wrapper_async())
    except Exception as e:
        print(f"运行出错：{e}")
    finally:
        try:
                                                       
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception as cleanup_err:
            print(f"事件循环清理出错：{cleanup_err}")
        loop.close()


runtime = None        
                                    
if __name__ == "__main__":
                              
                                                 
                                                                                                
                                                                      
                          
    main_wrapper()
