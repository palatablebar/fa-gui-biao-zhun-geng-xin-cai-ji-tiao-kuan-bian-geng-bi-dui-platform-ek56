import http from './http'
import type { ChangeItem, DiffRun } from '../types/domain'

export async function fetchRuns(documentKey?: string): Promise<{ items: DiffRun[] }> {
  const { data } = await http.get('/diffs', { params: documentKey ? { document_key: documentKey } : {} })
  return data
}

export async function createDiff(baseVersionId: string, targetVersionId: string): Promise<{ run: DiffRun }> {
  const { data } = await http.post('/diffs', {
    base_version_id: baseVersionId,
    target_version_id: targetVersionId,
  })
  return data
}

export async function fetchRun(runId: string): Promise<{ run: DiffRun }> {
  const { data } = await http.get(`/diffs/${runId}`)
  return data
}

export async function fetchRunChanges(
  runId: string,
  severity?: string,
): Promise<{ run: DiffRun; items: ChangeItem[]; total: number }> {
  const { data } = await http.get(`/diffs/${runId}/changes`, {
    params: severity ? { severity } : {},
  })
  return data
}
