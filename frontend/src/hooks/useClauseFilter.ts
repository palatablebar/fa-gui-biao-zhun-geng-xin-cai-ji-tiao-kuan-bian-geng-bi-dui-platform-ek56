import { computed, ref } from 'vue'
import type { ChangeItem, ChangeType, Severity } from '../types/domain'
import { SEVERITY_ORDER } from '../constants/enums'

/** 条款变更筛选：级别 + 变更类型 + 关键词文本。比对结果页与确认页共用。 */
export function useClauseFilter(source: () => ChangeItem[]) {
  const severity = ref<Severity | 'all'>('all')
  const changeType = ref<ChangeType | 'all'>('all')
  const keyword = ref('')
  const onlyPending = ref(false)

  const counts = computed<Record<string, number>>(() => {
    const result: Record<string, number> = { all: source().length }
    for (const level of SEVERITY_ORDER) {
      result[level] = source().filter((change) => change.severity === level).length
    }
    return result
  })

  const filtered = computed<ChangeItem[]>(() => {
    const needle = keyword.value.trim()
    return source().filter((change) => {
      if (severity.value !== 'all' && change.severity !== severity.value) return false
      if (changeType.value !== 'all' && change.change_type !== changeType.value) return false
      if (onlyPending.value && change.confirmed) return false
      if (!needle) return true
      return (
        change.old_text.includes(needle) ||
        change.new_text.includes(needle) ||
        change.reason.includes(needle) ||
        change.clause_label_new.includes(needle)
      )
    })
  })

  function setSeverity(value: Severity | 'all') {
    severity.value = value
  }

  return { severity, changeType, keyword, onlyPending, counts, filtered, setSeverity }
}
