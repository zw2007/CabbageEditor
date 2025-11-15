"""
Acoustics Manager - Data-Oriented Programming (DOP) 风格
数据和操作分离，使用纯函数管理 Acoustics 组件资源
"""
from __future__ import annotations
from typing import Optional, List, Dict
from ..components.acoustics import Acoustics
from ..components.geometry import Geometry

# ============================================================================
# 数据存储：模块级字典
# ============================================================================
_acoustics: Dict[str, Acoustics] = {}


# ============================================================================
# 查询操作：纯函数
# ============================================================================
def get(name: str) -> Optional[Acoustics]:
    """获取指定名称的 Acoustics"""
    return _acoustics.get(name)


def has(name: str) -> bool:
    """检查 Acoustics 是否存在"""
    return name in _acoustics


def list_all() -> List[str]:
    """列出所有 Acoustics 名称"""
    return list(_acoustics.keys())


def count() -> int:
    """获取 Acoustics 总数"""
    return len(_acoustics)


# ============================================================================
# 创建操作：修改数据
# ============================================================================
def create(name: str, geometry: Geometry) -> Acoustics:
    """创建新的 Acoustics 组件"""
    if name in _acoustics:
        raise ValueError(f"Acoustics '{name}' already exists")
    acou = Acoustics(geometry)
    _acoustics[name] = acou
    return acou


def register(name: str, acoustics: Acoustics) -> None:
    """注册已存在的 Acoustics"""
    if name in _acoustics:
        raise ValueError(f"Acoustics '{name}' already registered")
    _acoustics[name] = acoustics


def get_or_create(name: str, geometry: Geometry) -> Acoustics:
    """获取或创建 Acoustics（推荐）"""
    existing = get(name)
    if existing is not None:
        return existing
    return create(name, geometry)


# ============================================================================
# 删除操作：修改数据
# ============================================================================
def remove(name: str) -> bool:
    """删除指定名称的 Acoustics"""
    if name in _acoustics:
        del _acoustics[name]
        return True
    return False


def clear() -> None:
    """清空所有 Acoustics"""
    _acoustics.clear()


# ============================================================================
# 批量操作
# ============================================================================
def create_batch(acoustics_configs: Dict[str, Geometry]) -> List[Acoustics]:
    """批量创建 Acoustics

    Args:
        acoustics_configs: {name: geometry} 字典
    """
    results = []
    for name, geo in acoustics_configs.items():
        acou = get_or_create(name, geo)
        results.append(acou)
    return results


def remove_batch(names: List[str]) -> int:
    """批量删除 Acoustics，返回删除的数量"""
    count_deleted = 0
    for name in names:
        if remove(name):
            count_deleted += 1
    return count_deleted


def filter_by_geometry(geometry: Geometry) -> List[Acoustics]:
    """根据 Geometry 筛选 Acoustics"""
    return [acou for acou in _acoustics.values() if hasattr(acou, 'geometry_') and acou.geometry_ == geometry]


def set_all_volume(volume: float) -> None:
    """设置所有 Acoustics 的音量"""
    for acou in _acoustics.values():
        acou.set_volume(volume)


def mute_all() -> None:
    """静音所有 Acoustics"""
    set_all_volume(0.0)


def unmute_all(volume: float = 1.0) -> None:
    """取消静音所有 Acoustics"""
    set_all_volume(volume)


# ============================================================================
# 调试与监控
# ============================================================================
def get_all() -> Dict[str, Acoustics]:
    """获取所有 Acoustics（用于调试）"""
    return _acoustics.copy()


def print_state() -> None:
    """打印当前状态（用于调试）"""
    print(f"[AcousticsManager] Total: {count()}")
    for name in list_all():
        acou = get(name)
        print(f"  - {name}: {acou}")


# ============================================================================
# 向后兼容：类包装器（可选）
# ============================================================================
class AcousticsManager:
    """向后兼容的类包装器，内部调用 DOP 函数"""
    @staticmethod
    def create(name: str, geometry: Geometry) -> Acoustics:
        return create(name, geometry)

    @staticmethod
    def register(name: str, acoustics: Acoustics) -> None:
        return register(name, acoustics)

    @staticmethod
    def get(name: str) -> Optional[Acoustics]:
        return get(name)

    @staticmethod
    def get_or_create(name: str, geometry: Geometry) -> Acoustics:
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

