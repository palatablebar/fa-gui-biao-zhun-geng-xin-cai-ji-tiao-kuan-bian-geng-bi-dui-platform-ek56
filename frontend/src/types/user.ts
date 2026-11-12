export type UserRole = 'admin' | 'analyst' | 'viewer'

export interface User {
  id: string
  email: string
  display_name: string
  role: UserRole
  permissions: string[]
  is_active: boolean
}

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: '合规总监',
  analyst: '法规分析师',
  viewer: '客户只读',
}

export const ROLE_SCOPE: Record<UserRole, string> = {
  admin: '来源配置 · 发起比对 · 发布变更',
  analyst: '采集版本 · 发起比对 · 确认变更',
  viewer: '仅查看已发布变更说明',
}
