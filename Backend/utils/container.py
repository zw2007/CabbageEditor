from __future__ import annotations

"""
Lightweight dependency container.

The goal is not to introduce a heavy DI framework, but to provide centralised
construction for core/application/infrastructure services so the new layered
architecture stays testable.
"""

from typing import Any, Callable, Dict


class ServiceContainer:
    def __init__(self) -> None:
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}

    def register(self, key: str, factory: Callable[[], Any], *, singleton: bool = True) -> None:
        if key in self._factories:
            return
        if singleton:
            def _singleton_factory() -> Any:
                if key not in self._instances:
                    self._instances[key] = factory()
                return self._instances[key]

            self._factories[key] = _singleton_factory
        else:
            self._factories[key] = factory

    def resolve(self, key: str) -> Any:
        if key not in self._factories:
            raise KeyError(f"Service '{key}' is not registered")
        return self._factories[key]()

    def clear(self) -> None:
        self._instances.clear()
        self._factories.clear()
        self._metadata.clear()

    def set_flag(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def get_flag(self, key: str, default=None) -> Any:
        return self._metadata.get(key, default)


GLOBAL_CONTAINER = ServiceContainer()


def get_container() -> ServiceContainer:
    return GLOBAL_CONTAINER


__all__ = ["ServiceContainer", "get_container"]
