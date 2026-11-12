"""RBAC 角色常量。

前后端必须一致：users.role / src/constants/roles.py / frontend/src/constants/roles.ts。
角色：admin 合规总监｜analyst 法规分析师｜viewer 客户（只读已发布）。
"""
from __future__ import annotations

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"

ALL_ROLES: tuple[str, ...] = (ROLE_ADMIN, ROLE_ANALYST, ROLE_VIEWER)

# 能力矩阵：action -> 允许的角色
PERMISSIONS: dict[str, tuple[str, ...]] = {
    "sources:read": ALL_ROLES,
    "sources:write": (ROLE_ADMIN,),
    "sources:crawl": (ROLE_ADMIN, ROLE_ANALYST),
    "documents:read": ALL_ROLES,
    "diffs:read": ALL_ROLES,
    "diffs:run": (ROLE_ADMIN, ROLE_ANALYST),
    "changes:read": ALL_ROLES,
    "changes:confirm": (ROLE_ADMIN, ROLE_ANALYST),
    "changes:publish": (ROLE_ADMIN,),
    "changes:export": (ROLE_ADMIN, ROLE_ANALYST),
    "public:read": ALL_ROLES,
    "audit:read": (ROLE_ADMIN,),
}

ROLE_LABELS: dict[str, str] = {
    ROLE_ADMIN: "合规总监",
    ROLE_ANALYST: "法规分析师",
    ROLE_VIEWER: "客户只读",
}


def role_can(role: str, action: str) -> bool:
    return role in PERMISSIONS.get(action, ())


def role_permissions(role: str) -> list[str]:
    return [action for action, roles in PERMISSIONS.items() if role in roles]
