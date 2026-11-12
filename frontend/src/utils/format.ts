import type { Severity } from '../types/domain'

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (input: number) => String(input).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (input: number) => String(input).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function formatDecimal(value: number, digits = 3): string {
  return value.toFixed(digits)
}

export function severityTone(severity: Severity): string {
  switch (severity) {
    case 'major':
      return 'seal'
    case 'general':
      return 'ochre'
    case 'editorial':
      return 'moss'
    default:
      return 'ink'
  }
}

export function ratioPercent(value: number): string {
  return `${Math.round(value * 1000) / 10}%`
}

export function shortHash(hash: string): string {
  return hash ? hash.slice(0, 10) : '—'
}

const KEYWORD_GROUP_LABELS: Record<string, string> = {
  mandatory: '强制义务',
  penalty: '罚则',
  deadline: '期限',
  qualification: '资质准入',
  repeal: '废止',
  scope: '适用范围',
  record: '记录留档',
}

/** 把后端 `side:group:word` 关键词签名渲染成可读 chip：新增记 ＋，仅旧版有记 －。 */
export function keywordChips(raw: string[]): string[] {
  const merged = new Map<string, { group: string; word: string; side: string }>()
  for (const item of raw) {
    const [side, group, word] = item.split(':')
    if (!group || !word) continue
    const key = `${group}|${word}`
    const existing = merged.get(key)
    if (!existing) merged.set(key, { group, word, side })
    else if (side === 'new') existing.side = 'new'
  }
  const chips: string[] = []
  for (const { group, word, side } of merged.values()) {
    const mark = side === 'new' ? '＋' : '－'
    chips.push(`${mark}${KEYWORD_GROUP_LABELS[group] ?? group}·${word}`)
    if (chips.length >= 6) break
  }
  return chips
}
