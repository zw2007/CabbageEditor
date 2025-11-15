from __future__ import annotations
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QObject, Signal, Slot, QTimer

from Backend.utils.bootstrap import bootstrap
from Backend.artificial_intelligence.api import handle_user_message
from Backend.utils.logging import get_logger

bootstrap()
logger = get_logger(__name__)


def _format_exception(exc: BaseException) -> str:
    if isinstance(exc, BaseExceptionGroup):
        parts = [_format_exception(sub) for sub in exc.exceptions]
        return "; ".join(filter(None, parts))
    return str(exc) or exc.__class__.__name__



class AIService(QObject):
    ai_response = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # LangChain agent 在后台线程里运行，避免阻塞 UI 事件循环
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="AI_")
        # 创建一个新的事件循环用于协程
        self._loop = asyncio.new_event_loop()
        # 跟踪活动的任务
        self._active_tasks: set[asyncio.Task] = set()

        # 使用 QTimer 定期处理事件循环，确保协程能运行
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_event_loop)
        self._timer.start(10)  # 每 10ms 处理一次事件循环

    def _process_event_loop(self) -> None:
        """处理 asyncio 事件循环（由 QTimer 定期调用）"""
        try:
            # 运行所有准备好的回调，但不阻塞
            self._loop.call_soon(self._loop.stop)
            self._loop.run_forever()
        except Exception as e:
            logger.exception("事件循环处理错误")

    @Slot(str)
    def send_message_to_ai(self, ai_message: str) -> None:
        """发送消息到 AI（使用协程异步处理）"""
        # 创建协程任务
        task = self._loop.create_task(self._process_ai_message(ai_message))
        self._active_tasks.add(task)
        # 任务完成后从集合中移除
        task.add_done_callback(self._active_tasks.discard)

    async def _process_ai_message(self, ai_message: str) -> None:
        """协程：处理 AI 消息"""
        try:
            msg_data = json.loads(ai_message)
            query = msg_data.get("message", "")

            # 在线程池中执行阻塞的 AI 调用
            result = await self._loop.run_in_executor(self._executor, handle_user_message, query)

            # 发送响应信号
            self.ai_response.emit(result)

        except BaseException as exc:
            error_payload = json.dumps(
                {
                    "type": "error",
                    "content": _format_exception(exc),
                    "status": "error",
                    "timestamp": int(time.time()),
                }
            )
            self.ai_response.emit(error_payload)

    def cleanup(self):
        """清理资源（在 service 销毁前调用）"""
        # 停止定时器
        if self._timer.isActive():
            self._timer.stop()

        # 取消所有活动的任务
        for task in list(self._active_tasks):
            if not task.done():
                task.cancel()

        # 等待所有任务完成或取消
        if self._active_tasks:
            try:
                self._loop.run_until_complete(
                    asyncio.gather(*self._active_tasks, return_exceptions=True)
                )
            except Exception:
                pass

        self._active_tasks.clear()

        # 关闭线程池
        self._executor.shutdown(wait=True, cancel_futures=True)

        # 关闭事件循环
        try:
            self._loop.close()
        except Exception:
            pass
