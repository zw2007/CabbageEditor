# filepath: e:\project\CabbageEditor\Backend\utils\engine_import.py
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
        'Backend.corona_engine_fallback',
        'backend.corona_engine_fallback',
    ]
    for name in candidates:
        try:
            mod = import_module(name)
            # If module provides a CoronaEngine symbol (fallback file defines class CoronaEngine), return that
            if hasattr(mod, 'CoronaEngine'):
                return getattr(mod, 'CoronaEngine')
            # Otherwise return the module itself (real engine module may expose Scene/Actor at top-level)
            return mod
        except Exception:
            continue
    return None
