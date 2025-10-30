import asyncio, json, anyio

from typing import Optional
from contextlib import AsyncExitStack, asynccontextmanager

from openai import OpenAI

from mcp import ClientSession
from mcp.server.fastmcp import FastMCP


@asynccontextmanager
async def create_internal_mcp_connection(app: FastMCP):
    """
    在单个进程内部创建一个 MCP 客户端-服务器连接。
    它使用内存流进行通信，并将 FastMCP 服务器作为一个后台异步任务运行。
    """

    client_to_server_writer, client_to_server_reader = anyio.create_memory_object_stream(0)
    server_to_client_writer, server_to_client_reader = anyio.create_memory_object_stream(0)

    async def run_server_task():

        server_read_stream = client_to_server_reader
        server_write_stream = server_to_client_writer

        print("--- Internal MCP Server task started. ---")
        await app._mcp_server.run(
            server_read_stream,
            server_write_stream,
            app._mcp_server.create_initialization_options(),
        )
        print("--- Internal MCP Server task finished. ---")

    async with anyio.create_task_group() as tg:

        tg.start_soon(run_server_task)

        client_read_stream = server_to_client_reader
        client_write_stream = client_to_server_writer

        try:
            yield client_read_stream, client_write_stream
        finally:

            print("--- Client session ending, cancelling server task... ---")
            tg.cancel_scope.cancel()


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = OpenAI(
            api_key="sk-txlrveamjgduydqvpfqbfvgqoqtjkbarnikcoeaeddxzzmjo",
            base_url="https://api.siliconflow.cn/v1",
        )

    async def connect_to_server(self, app: FastMCP):
        print("--- Creating internal MCP connection... ---")

        transport = await self.exit_stack.enter_async_context(
            create_internal_mcp_connection(app)
        )
        read_stream, write_stream = transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        print("--- Client session created, initializing... ---")
        await self.session.initialize()
        print("--- MCP connection initialized successfully! ---")

    async def process_query(self, query: str) -> str:

        system_prompt = (
            "You are a helpful assistant."
            "You have the function of online search. "
            "Please MUST call web_search tool to search the Internet content before answering."
            "Please do not lose the user's question information when searching,"
            "and try to maintain the completeness of the question content as much as possible."
            "When there is a date related question in the user's question,"
            "please use the search function directly to search and PROHIBIT inserting specific time."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        response = await self.session.list_tools()

        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]

        response = self.client.chat.completions.create(
            model="Qwen/Qwen3-14B", messages=messages, tools=available_tools
        )

        content = response.choices[0]
        if content.finish_reason == "tool_calls":
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            result = await self.session.call_tool(tool_name, tool_args)
            print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")

            messages.append(content.message.model_dump())
            messages.append(
                {
                    "role": "tool",
                    "content": result.content[0].text,
                    "tool_call_id": tool_call.id,
                }
            )

            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=messages,
            )
            return response.choices[0].message.content

        return content.message.content

    async def chat_loop(self):
        """
        启动一个简洁的交互式聊天循环。
        按 Ctrl+C 退出。
        """

        print("\nStarting chat session. Press Ctrl+C to exit.")

        while True:
            try:

                query = await anyio.to_thread.run_sync(input, "\nQuery: ")

                if not query.strip():
                    continue

                response = await self.process_query(query)
                print(f"\n{response}")

            except KeyboardInterrupt:

                print()
                break
            except Exception:
                import traceback

                print("\nAn error occurred:")
                traceback.print_exc()

        print("Goodbye!")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


def qa_one_sync(query: str, callback=None) -> str:
    """
    一个同步的(非 async)单轮问-答方法。

    它在内部启动一个临时的事件循环来运行所有异步的客户端操作，
    并阻塞式地等待最终结果返回。

    Args:
        query (str): 要发送给模型的查询。
        callback (Callable, optional): 一个可选的同步回调函数，它将接收最终响应作为参数。

    Returns:
        str: 模型的最终文本响应。
    """

    async def _async_wrapper():
        from .transform_server import app as server_app

        client = MCPClient()
        try:
            print(f"\nQuery: {query}")

            await client.connect_to_server(server_app)

            response = await client.process_query(query)

            print(f"\n{response}")

            if callback:
                callback(response)

            return response
        finally:
            await client.cleanup()

    try:
        return asyncio.run(_async_wrapper())
    except RuntimeError as e:

        print(f"错误：无法启动新的事件循环，可能已经有一个正在运行。错误信息: {e}")
        print("在这种情况下，您需要从一个异步上下文中调用原始的 async qa_one 方法。")
        return "执行异步操作失败。"


async def main():
    from .transform_server import app as server_app
    client = MCPClient()
    try:

        await client.connect_to_server(server_app)
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
