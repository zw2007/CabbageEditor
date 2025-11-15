"""
Optics Manager - Data-Oriented Programming (DOP) 风格
数据和操作分离，使用纯函数管理 Optics 组件资源
"""
from __future__ import annotations
from typing import Optional, List, Dict
from ..components.optics import Optics
from ..components.geometry import Geometry

# ============================================================================
# 数据存储：模块级字典
# ============================================================================
_optics: Dict[str, Optics] = {}


# ============================================================================
# 查询操作：纯函数
# ============================================================================
def get(name: str) -> Optional[Optics]:
    """获取指定名称的 Optics"""
    return _optics.get(name)


def has(name: str) -> bool:
    """检查 Optics 是否存在"""
    return name in _optics


def list_all() -> List[str]:
    """列出所有 Optics 名称"""
    return list(_optics.keys())


def count() -> int:
    """获取 Optics 总数"""
    return len(_optics)


# ============================================================================
# 创建操作：修改数据
# ============================================================================
def create(name: str, geometry: Geometry) -> Optics:
    """创建新的 Optics 组件"""
    if name in _optics:
        raise ValueError(f"Optics '{name}' already exists")
    optics = Optics(geometry)
    _optics[name] = optics
    return optics


def register(name: str, optics: Optics) -> None:
    """注册已存在的 Optics"""
    if name in _optics:
        raise ValueError(f"Optics '{name}' already registered")
    _optics[name] = optics


def get_or_create(name: str, geometry: Geometry) -> Optics:
    """获取或创建 Optics（推荐）"""
    existing = get(name)
    if existing is not None:
        return existing
    return create(name, geometry)


# ============================================================================
# 删除操作：修改数据
# ============================================================================
def remove(name: str) -> bool:
    """删除指定名称的 Optics"""
    if name in _optics:
        del _optics[name]
        return True
    return False


def clear() -> None:
    """清空所有 Optics"""
    _optics.clear()


# ============================================================================
# 批量操作
# ============================================================================
def create_batch(optics_configs: Dict[str, Geometry]) -> List[Optics]:
    """批量创建 Optics

    Args:
        optics_configs: {name: geometry} 字典
    """
    results = []
    for name, geo in optics_configs.items():
        opt = get_or_create(name, geo)
        results.append(opt)
    return results


def remove_batch(names: List[str]) -> int:
    """批量删除 Optics，返回删除的数量"""
    count_deleted = 0
    for name in names:
        if remove(name):
            count_deleted += 1
    return count_deleted


def filter_by_geometry(geometry: Geometry) -> List[Optics]:
    """根据 Geometry 筛选 Optics"""
    return [opt for opt in _optics.values() if hasattr(opt, 'geometry_') and opt.geometry_ == geometry]


# ============================================================================
# 调试与监控
# ============================================================================
def get_all() -> Dict[str, Optics]:
    """获取所有 Optics（用于调试）"""
    return _optics.copy()


def print_state() -> None:
    """打印当前状态（用于调试）"""
    print(f"[OpticsManager] Total: {count()}")
    for name in list_all():
        opt = get(name)
        print(f"  - {name}: {opt}")


# ============================================================================
# 向后兼容：类包装器（可选）
# ============================================================================
class OpticsManager:
    """向后兼容的类包装器，内部调用 DOP 函数"""
    @staticmethod
    def create(name: str, geometry: Geometry) -> Optics:
        return create(name, geometry)

    @staticmethod
    def register(name: str, optics: Optics) -> None:
        return register(name, optics)

    @staticmethod
    def get(name: str) -> Optional[Optics]:
        return get(name)

    @staticmethod
    def get_or_create(name: str, geometry: Geometry) -> Optics:
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

