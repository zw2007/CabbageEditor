"""
Kinematics Manager - Data-Oriented Programming (DOP) 风格
数据和操作分离，使用纯函数管理 Kinematics 组件资源
"""
from __future__ import annotations
from typing import Optional, List, Dict
from ..components.kinematics import Kinematics
from ..components.geometry import Geometry

# ============================================================================
# 数据存储：模块级字典
# ============================================================================
_kinematics: Dict[str, Kinematics] = {}


# ============================================================================
# 查询操作：纯函数
# ============================================================================
def get(name: str) -> Optional[Kinematics]:
    """获取指定名称的 Kinematics"""
    return _kinematics.get(name)


def has(name: str) -> bool:
    """检查 Kinematics 是否存在"""
    return name in _kinematics


def list_all() -> List[str]:
    """列出所有 Kinematics 名称"""
    return list(_kinematics.keys())


def count() -> int:
    """获取 Kinematics 总数"""
    return len(_kinematics)


# ============================================================================
# 创建操作：修改数据
# ============================================================================
def create(name: str, geometry: Geometry) -> Kinematics:
    """创建新的 Kinematics 组件"""
    if name in _kinematics:
        raise ValueError(f"Kinematics '{name}' already exists")
    kine = Kinematics(geometry)
    _kinematics[name] = kine
    return kine


def register(name: str, kinematics: Kinematics) -> None:
    """注册已存在的 Kinematics"""
    if name in _kinematics:
        raise ValueError(f"Kinematics '{name}' already registered")
    _kinematics[name] = kinematics


def get_or_create(name: str, geometry: Geometry) -> Kinematics:
    """获取或创建 Kinematics（推荐）"""
    existing = get(name)
    if existing is not None:
        return existing
    return create(name, geometry)


# ============================================================================
# 删除操作：修改数据
# ============================================================================
def remove(name: str) -> bool:
    """删除指定名称的 Kinematics"""
    if name in _kinematics:
        del _kinematics[name]
        return True
    return False


def clear() -> None:
    """清空所有 Kinematics"""
    _kinematics.clear()


# ============================================================================
# 批量操作
# ============================================================================
def create_batch(kinematics_configs: Dict[str, Geometry]) -> List[Kinematics]:
    """批量创建 Kinematics

    Args:
        kinematics_configs: {name: geometry} 字典
    """
    results = []
    for name, geo in kinematics_configs.items():
        kine = get_or_create(name, geo)
        results.append(kine)
    return results


def remove_batch(names: List[str]) -> int:
    """批量删除 Kinematics，返回删除的数量"""
    count_deleted = 0
    for name in names:
        if remove(name):
            count_deleted += 1
    return count_deleted


def filter_by_geometry(geometry: Geometry) -> List[Kinematics]:
    """根据 Geometry 筛选 Kinematics"""
    return [kine for kine in _kinematics.values() if hasattr(kine, 'geometry_') and kine.geometry_ == geometry]


def play_all(speed: float = 1.0) -> None:
    """播放所有动画"""
    for kine in _kinematics.values():
        kine.play_animation(speed)


def stop_all() -> None:
    """停止所有动画"""
    for kine in _kinematics.values():
        kine.stop_animation()


# ============================================================================
# 调试与监控
# ============================================================================
def get_all() -> Dict[str, Kinematics]:
    """获取所有 Kinematics（用于调试）"""
    return _kinematics.copy()


def print_state() -> None:
    """打印当前状态（用于调试）"""
    print(f"[KinematicsManager] Total: {count()}")
    for name in list_all():
        kine = get(name)
        print(f"  - {name}: {kine}")


# ============================================================================
# 向后兼容：类包装器（可选）
# ============================================================================
class KinematicsManager:
    """向后兼容的类包装器，内部调用 DOP 函数"""
    @staticmethod
    def create(name: str, geometry: Geometry) -> Kinematics:
        return create(name, geometry)

    @staticmethod
    def register(name: str, kinematics: Kinematics) -> None:
        return register(name, kinematics)

    @staticmethod
    def get(name: str) -> Optional[Kinematics]:
        return get(name)

    @staticmethod
    def get_or_create(name: str, geometry: Geometry) -> Kinematics:
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

