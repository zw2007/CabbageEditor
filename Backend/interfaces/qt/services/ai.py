from __future__ import annotations
import json
import time
from PySide6.QtCore import QObject, Signal, Slot, QThread

from Backend.application.bootstrap import bootstrap
from Backend.application.services.ai_service import AIApplicationService
from Backend.shared.container import get_container

bootstrap()


def _format_exception(exc: BaseException) -> str:
    if isinstance(exc, BaseExceptionGroup):
        parts = [_format_exception(sub) for sub in exc.exceptions]
        return "; ".join(filter(None, parts))
    return str(exc) or exc.__class__.__name__


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
        except BaseException as exc:
            error_payload = json.dumps(
                {
                    "type": "error",
                    "content": _format_exception(exc),
                    "status": "error",
                    "timestamp": int(time.time()),
                }
            )
            self.result_ready.emit(error_payload)


class AIService(QObject):
    ai_response = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        container = get_container()
        self.ai_service: AIApplicationService = container.resolve("ai_service")
        self._workers: set[WorkerThread] = set()

    @Slot(str)
    def send_message_to_ai(self, ai_message: str) -> None:
        def ai_work() -> str:
            try:
                msg_data = json.loads(ai_message)
                query = msg_data.get("message", "")
                return self.ai_service.ask(query)
            except BaseException as exc:
                return json.dumps(
                    {
                        "type": "error",
                        "content": _format_exception(exc),
                        "status": "error",
                        "timestamp": int(time.time()),
                    }
                )

        worker = WorkerThread(ai_work, parent=self)
        worker.result_ready.connect(self.ai_response.emit)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda: self._workers.discard(worker))
        self._workers.add(worker)
        worker.start()
