from __future__ import annotations
import json
import time
from PySide6.QtCore import QObject, Signal, Slot, QThread
from Backend.mcp_client import qa_one_sync


class WorkerThread(QThread):
    result_ready = Signal(object)

    def __init__(self, func, *args, parent: QObject | None = None, **kwargs):
        super().__init__(parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            result = self.func(*self.args, **self.kwargs)
            self.result_ready.emit(result)
        except Exception as e:
            # 保持静默，避免线程异常打断 UI；必要时可加日志
            pass


class AIService(QObject):
    ai_response = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._workers: set[WorkerThread] = set()

    @Slot(str)
    def send_message_to_ai(self, ai_message: str) -> None:
        def ai_work() -> str:
            try:
                msg_data = json.loads(ai_message)
                query = msg_data.get("message", "")
                response_text = qa_one_sync(query=query)
                final_response = {
                    "type": "ai_response",
                    "content": response_text,
                    "status": "success",
                    "timestamp": int(time.time()),
                }
                return json.dumps(final_response)
            except Exception as e:
                error_response = {
                    "type": "error",
                    "content": str(e),
                    "status": "error",
                    "timestamp": int(time.time()),
                }
                return json.dumps(error_response)

        worker = WorkerThread(ai_work, parent=self)
        worker.result_ready.connect(self.ai_response.emit)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda: self._workers.discard(worker))
        self._workers.add(worker)
        worker.start()
