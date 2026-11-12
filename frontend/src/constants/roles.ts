import type { UserRole } from '../types/user'

/* 与 backend/src/constants/roles.py 一一对应 */
export const ROLES: UserRole[] = ['admin', 'analyst', 'viewer']

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: '合规总监',
  analyst: '法规分析师',
  viewer: '客户只读',
}

export const ROLE_PERMISSION_HINT: Record<UserRole, string> = {
  admin: '来源配置、发起比对、发布变更、查看审计',
  analyst: '采集新版本、发起比对、确认变更并标注影响行业',
  viewer: '只读已发布变更说明（客户台账）',
}
