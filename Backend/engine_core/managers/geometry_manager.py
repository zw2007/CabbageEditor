"""
Geometry Manager - Data-Oriented Programming (DOP) 风格
数据和操作分离，使用纯函数管理 Geometry 资源
"""
from __future__ import annotations
from typing import Optional, List, Dict
from ..components.geometry import Geometry

# ============================================================================
# 数据存储：模块级字典
# ============================================================================
_geometries: Dict[str, Geometry] = {}


# ============================================================================
# 查询操作：纯函数
# ============================================================================
def get(name: str) -> Optional[Geometry]:
    """获取指定名称的 Geometry"""
    return _geometries.get(name)


def has(name: str) -> bool:
    """检查 Geometry 是否存在"""
    return name in _geometries


def list_all() -> List[str]:
    """列出所有 Geometry 名称"""
    return list(_geometries.keys())


def count() -> int:
    """获取 Geometry 总数"""
    return len(_geometries)


# ============================================================================
# 创建操作：修改数据
# ============================================================================
def create(name: str, model_path: str) -> Geometry:
    """创建新的 Geometry"""
    if name in _geometries:
        raise ValueError(f"Geometry '{name}' already exists")
    geo = Geometry(model_path, name=name)
    _geometries[name] = geo
    return geo


def register(name: str, geometry: Geometry) -> None:
    """注册已存在的 Geometry"""
    if name in _geometries:
        raise ValueError(f"Geometry '{name}' already registered")
    _geometries[name] = geometry


def get_or_create(name: str, model_path: str) -> Geometry:
    """获取或创建 Geometry（推荐）"""
    existing = get(name)
    if existing is not None:
        return existing
    return create(name, model_path)


# ============================================================================
# 删除操作：修改数据
# ============================================================================
def remove(name: str) -> bool:
    """删除指定名称的 Geometry"""
    if name in _geometries:
        del _geometries[name]
        return True
    return False


def clear() -> None:
    """清空所有 Geometry"""
    _geometries.clear()


# ============================================================================
# 批量操作
# ============================================================================
def create_batch(geometry_configs: Dict[str, str]) -> List[Geometry]:
    """批量创建 Geometry

    Args:
        geometry_configs: {name: model_path} 字典
    """
    results = []
    for name, path in geometry_configs.items():
        geo = get_or_create(name, path)
        results.append(geo)
    return results


def remove_batch(names: List[str]) -> int:
    """批量删除 Geometry，返回删除的数量"""
    count_deleted = 0
    for name in names:
        if remove(name):
            count_deleted += 1
    return count_deleted


def filter_by_path(path_pattern: str) -> List[Geometry]:
    """根据路径模式筛选 Geometry"""
    return [geo for geo in _geometries.values() if path_pattern in geo.model_path]


def move_all(delta: List[float]) -> None:
    """移动所有 Geometry"""
    for geo in _geometries.values():
        pos = geo.get_position()
        geo.set_position([pos[0] + delta[0], pos[1] + delta[1], pos[2] + delta[2]])


# ============================================================================
# 调试与监控
# ============================================================================
def get_all() -> Dict[str, Geometry]:
    """获取所有 Geometry（用于调试）"""
    return _geometries.copy()


def print_state() -> None:
    """打印当前状态（用于调试）"""
    print(f"[GeometryManager] Total: {count()}")
    for name in list_all():
        geo = get(name)
        print(f"  - {name}: {geo.model_path}, pos={geo.get_position()}")


# ============================================================================
# 向后兼容：类包装器（可选）
# ============================================================================
class GeometryManager:
    """向后兼容的类包装器，内部调用 DOP 函数"""
    @staticmethod
    def create(name: str, model_path: str) -> Geometry:
        return create(name, model_path)

    @staticmethod
    def register(name: str, geometry: Geometry) -> None:
        return register(name, geometry)

    @staticmethod
    def get(name: str) -> Optional[Geometry]:
        return get(name)

    @staticmethod
    def get_or_create(name: str, model_path: str) -> Geometry:
        return get_or_create(name, model_path)

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

