from __future__ import annotations

import asyncio
from typing import Callable, Optional

from Backend.application.bootstrap import bootstrap
from Backend.application.services.ai_service import AIApplicationService
from Backend.shared.container import get_container

bootstrap()
container = get_container()


def qa_one_sync(query: str, callback: Optional[Callable[[str], None]] = None) -> str:
    service: AIApplicationService = container.resolve("ai_service")
    return service.ask(query, callback)


async def chat_loop() -> None:
    service: AIApplicationService = container.resolve("ai_service")
    print("Starting chat session. Press Ctrl+C to exit.")
    while True:
        try:
            query = await asyncio.to_thread(input, "\nQuery: ")
            if not query.strip():
                continue
            response = service.ask(query)
            print(f"\n{response}")
        except KeyboardInterrupt:
            print()
            break


def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
