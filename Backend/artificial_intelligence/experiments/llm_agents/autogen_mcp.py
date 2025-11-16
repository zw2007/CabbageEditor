import asyncio
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

      
model_client = OpenAIChatCompletionClient(
    model="deepseek-ai/DeepSeek-V3",
    api_key="sk-txlrveamjgduydqvpfqbfvgqoqtjkbarnikcoeaeddxzzmjo",
    base_url="https://api.siliconflow.cn/v1",
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": False,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
    },
)


async def main() -> None:
               
    desktop = str(Path.home())
    server_params = StdioServerParams(
        command="cmd", args=["/c", "uvx", "blender-mcp", desktop]
    )
                                                

                           
    tools = await mcp_server_tools(server_params)

                   
    agent = AssistantAgent(
        name="blender_agent",
        model_client=model_client,
        tools=tools,
        system_message="You are a helpful assistant. You can use various tools via MCP.",
        reflect_on_tool_use=True,
        model_client_stream=True,                                                  
    )

              
    await Console(agent.run_stream(task="在blender中创建一个猴头"))
    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
