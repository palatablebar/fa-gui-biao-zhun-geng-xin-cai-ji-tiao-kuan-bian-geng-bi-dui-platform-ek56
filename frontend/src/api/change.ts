import http from './http'
import type { ChangeItem, Industry, PublishedGroup, PublishResult } from '../types/domain'

export async function fetchPendingChanges(limit = 50): Promise<{ items: ChangeItem[]; total: number }> {
  const { data } = await http.get('/changes/pending', { params: { limit } })
  return data
}

export async function confirmChange(
  changeId: string,
  payload: { impact_industries: Industry[]; impact_note: string },
): Promise<{ change: ChangeItem }> {
  const { data } = await http.post(`/changes/${changeId}/confirm`, payload)
  return data
}

export async function publishRun(runId: string, publishNote: string): Promise<PublishResult> {
  const { data } = await http.post(`/diffs/${runId}/publish`, { publish_note: publishNote })
  return data
}

export async function fetchPublicChanges(): Promise<{ items: PublishedGroup[]; total: number }> {
  const { data } = await http.get('/public/changes')
  return data
}

export async function downloadExport(runId: string, format: 'md' | 'csv'): Promise<void> {
  const response = await http.get(`/diffs/${runId}/export`, { params: { format }, responseType: 'blob' })
  const blob = new Blob([response.data], {
    type: format === 'md' ? 'text/markdown;charset=utf-8' : 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `lawdelta-changes-${runId.slice(0, 8)}.${format}`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
