from __future__ import annotations

from langchain.tools import tool


@tool
def search(query: str) -> str:
    """简易搜索工具，直接回显查询字符串。"""
    print("执行搜索工具")
    return f"搜索结果（模拟）：{query}"


@tool
def get_weather(location: str) -> str:
    """简易天气工具，返回占位天气。"""
    print("执行天气工具")
    return f"{location} 当前天气：晴，22°C（模拟数据）"


def load_builtin_tools():
    return [search, get_weather]


__all__ = ["load_builtin_tools"]
