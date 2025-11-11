"""Robust loader for the CoronaEngine module.
Tries multiple import paths so modules can be imported both as package (Backend.*) and as top-level scripts.
Returns the module object or the CoronaEngine class from the fallback module, or None.
"""
from importlib import import_module
from types import ModuleType
from typing import Optional


def load_corona_engine() -> Optional[object]:
    candidates = [
        'CoronaEngine',
        'corona_engine_fallback',
        'Backend.tools.corona_engine_fallback',
        'Backend.corona_engine_fallback',
        'backend.corona_engine_fallback',
    ]
    for name in candidates:
        try:
            mod = import_module(name)

            if hasattr(mod, 'CoronaEngine'):
                return getattr(mod, 'CoronaEngine')

            return mod
        except Exception:
            continue
    return None
