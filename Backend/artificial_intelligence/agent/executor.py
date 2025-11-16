from __future__ import annotations

from typing import Any, Dict, List

from Backend.artificial_intelligence.agent.factory import create_default_agent


def run_agent(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    agent = create_default_agent()
    return agent.invoke({"messages": messages})


__all__ = ["run_agent"]
