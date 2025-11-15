"""
Viewport Manager - Data-Oriented Programming (DOP) 风格
数据和操作分离，使用纯函数管理 Viewport 资源
"""
from __future__ import annotations
from typing import Optional, List, Dict
from ..entities.viewport import Viewport

# ============================================================================
# 数据存储：模块级字典
# ============================================================================
_viewports: Dict[str, Viewport] = {}


# ============================================================================
# 查询操作：纯函数
# ============================================================================
def get(name: str) -> Optional[Viewport]:
    """获取指定名称的 Viewport"""
    return _viewports.get(name)


def has(name: str) -> bool:
    """检查 Viewport 是否存在"""
    return name in _viewports


def list_all() -> List[str]:
    """列出所有 Viewport 名称"""
    return list(_viewports.keys())


def count() -> int:
    """获取 Viewport 总数"""
    return len(_viewports)


# ============================================================================
# 创建操作：修改数据
# ============================================================================
def create(name: str, width: int, height: int, light_field: bool = False) -> Viewport:
    """创建新的 Viewport"""
    if name in _viewports:
        raise ValueError(f"Viewport '{name}' already exists")
    vp = Viewport(width, height, light_field, name=name)
    _viewports[name] = vp
    return vp


def register(name: str, viewport: Viewport) -> None:
    """注册已存在的 Viewport"""
    if name in _viewports:
        raise ValueError(f"Viewport '{name}' already registered")
    _viewports[name] = viewport


def get_or_create(name: str, width: int = 1920, height: int = 1080, light_field: bool = False) -> Viewport:
    """获取或创建 Viewport（推荐）"""
    existing = get(name)
    if existing is not None:
        return existing
    return create(name, width, height, light_field)


# ============================================================================
# 删除操作：修改数据
# ============================================================================
def remove(name: str) -> bool:
    """删除指定名称的 Viewport"""
    if name in _viewports:
        del _viewports[name]
        return True
    return False


def clear() -> None:
    """清空所有 Viewport"""
    _viewports.clear()


# ============================================================================
# 批量操作
# ============================================================================
def create_batch(viewport_configs: Dict[str, dict]) -> List[Viewport]:
    """批量创建 Viewport

    Args:
        viewport_configs: {name: {width, height, light_field}} 字典
    """
    results = []
    for name, config in viewport_configs.items():
        vp = get_or_create(
            name,
            config.get('width', 1920),
            config.get('height', 1080),
            config.get('light_field', False)
        )
        results.append(vp)
    return results


def remove_batch(names: List[str]) -> int:
    """批量删除 Viewport，返回删除的数量"""
    count = 0
    for name in names:
        if remove(name):
            count += 1
    return count


def resize_all(width: int, height: int) -> None:
    """调整所有 Viewport 的尺寸"""
    for vp in _viewports.values():
        vp.set_size(width, height)


# ============================================================================
# 调试与监控
# ============================================================================
def get_all() -> Dict[str, Viewport]:
    """获取所有 Viewport（用于调试）"""
    return _viewports.copy()


def print_state() -> None:
    """打印当前状态（用于调试）"""
    print(f"[ViewportManager] Total: {count()}")
    for name in list_all():
        vp = get(name)
        print(f"  - {name}: {vp.width_}x{vp.height_}")


# ============================================================================
# 向后兼容：类包装器（可选）
# ============================================================================
class ViewportManager:
    """向后兼容的类包装器，内部调用 DOP 函数"""

    @staticmethod
    def create(name: str, width: int, height: int, light_field: bool = False) -> Viewport:
        return create(name, width, height, light_field)

    @staticmethod
    def register(name: str, viewport: Viewport) -> None:
        return register(name, viewport)

    @staticmethod
    def get(name: str) -> Optional[Viewport]:
        return get(name)

    @staticmethod
    def get_or_create(name: str, width: int = 1920, height: int = 1080, light_field: bool = False) -> Viewport:
        return get_or_create(name, width, height, light_field)

    @staticmethod
    def remove(name: str) -> bool:
        return remove(name)

    @staticmethod
    def list() -> List[str]:
        return list_all()

    @staticmethod
    def has(name: str) -> bool:
        return has(name)

    @staticmethod
    def clear() -> None:
        return clear()
