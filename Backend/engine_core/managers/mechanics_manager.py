"""
Mechanics Manager - Data-Oriented Programming (DOP) 风格
数据和操作分离，使用纯函数管理 Mechanics 组件资源
"""
from __future__ import annotations
from typing import Optional, List, Dict
from ..components.mechanics import Mechanics
from ..components.geometry import Geometry

# ============================================================================
# 数据存储：模块级字典
# ============================================================================
_mechanics: Dict[str, Mechanics] = {}


# ============================================================================
# 查询操作：纯函数
# ============================================================================
def get(name: str) -> Optional[Mechanics]:
    """获取指定名称的 Mechanics"""
    return _mechanics.get(name)


def has(name: str) -> bool:
    """检查 Mechanics 是否存在"""
    return name in _mechanics


def list_all() -> List[str]:
    """列出所有 Mechanics 名称"""
    return list(_mechanics.keys())


def count() -> int:
    """获取 Mechanics 总数"""
    return len(_mechanics)


# ============================================================================
# 创建操作：修改数据
# ============================================================================
def create(name: str, geometry: Geometry) -> Mechanics:
    """创建新的 Mechanics 组件"""
    if name in _mechanics:
        raise ValueError(f"Mechanics '{name}' already exists")
    mech = Mechanics(geometry)
    _mechanics[name] = mech
    return mech


def register(name: str, mechanics: Mechanics) -> None:
    """注册已存在的 Mechanics"""
    if name in _mechanics:
        raise ValueError(f"Mechanics '{name}' already registered")
    _mechanics[name] = mechanics


def get_or_create(name: str, geometry: Geometry) -> Mechanics:
    """获取或创建 Mechanics（推荐）"""
    existing = get(name)
    if existing is not None:
        return existing
    return create(name, geometry)


# ============================================================================
# 删除操作：修改数据
# ============================================================================
def remove(name: str) -> bool:
    """删除指定名称的 Mechanics"""
    if name in _mechanics:
        del _mechanics[name]
        return True
    return False


def clear() -> None:
    """清空所有 Mechanics"""
    _mechanics.clear()


# ============================================================================
# 批量操作
# ============================================================================
def create_batch(mechanics_configs: Dict[str, Geometry]) -> List[Mechanics]:
    """批量创建 Mechanics

    Args:
        mechanics_configs: {name: geometry} 字典
    """
    results = []
    for name, geo in mechanics_configs.items():
        mech = get_or_create(name, geo)
        results.append(mech)
    return results


def remove_batch(names: List[str]) -> int:
    """批量删除 Mechanics，返回删除的数量"""
    count_deleted = 0
    for name in names:
        if remove(name):
            count_deleted += 1
    return count_deleted


def filter_by_geometry(geometry: Geometry) -> List[Mechanics]:
    """根据 Geometry 筛选 Mechanics"""
    return [mech for mech in _mechanics.values() if hasattr(mech, 'geometry_') and mech.geometry_ == geometry]


# ============================================================================
# 调试与监控
# ============================================================================
def get_all() -> Dict[str, Mechanics]:
    """获取所有 Mechanics（用于调试）"""
    return _mechanics.copy()


def print_state() -> None:
    """打印当前状态（用于调试）"""
    print(f"[MechanicsManager] Total: {count()}")
    for name in list_all():
        mech = get(name)
        print(f"  - {name}: {mech}")


# ============================================================================
# 向后兼容：类包装器（可选）
# ============================================================================
class MechanicsManager:
    """向后兼容的类包装器，内部调用 DOP 函数"""
    @staticmethod
    def create(name: str, geometry: Geometry) -> Mechanics:
        return create(name, geometry)

    @staticmethod
    def register(name: str, mechanics: Mechanics) -> None:
        return register(name, mechanics)

    @staticmethod
    def get(name: str) -> Optional[Mechanics]:
        return get(name)

    @staticmethod
    def get_or_create(name: str, geometry: Geometry) -> Mechanics:
        return get_or_create(name, geometry)

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

