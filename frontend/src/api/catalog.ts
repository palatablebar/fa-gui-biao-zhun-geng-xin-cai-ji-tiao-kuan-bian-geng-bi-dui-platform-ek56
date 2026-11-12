import http from './http'
import type { DocumentGroup, DocumentVersion, SourceItem, VersionDetail } from '../types/domain'

export async function fetchSources(): Promise<{ items: SourceItem[] }> {
  const { data } = await http.get('/sources')
  return data
}

export async function updateSource(
  sourceId: string,
  payload: { enabled?: boolean; owner_note?: string },
): Promise<{ source: SourceItem }> {
  const { data } = await http.patch(`/sources/${sourceId}`, payload)
  return data
}

export async function crawlSource(sourceId: string): Promise<{
  created: boolean
  version: DocumentVersion
  clause_count: number
  note: string
}> {
  const { data } = await http.post(`/sources/${sourceId}/crawl`)
  return data
}

export async function fetchDocuments(): Promise<{ items: DocumentGroup[] }> {
  const { data } = await http.get('/documents')
  return data
}

export async function fetchVersion(versionId: string): Promise<{ version: VersionDetail }> {
  const { data } = await http.get(`/documents/${versionId}`)
  return data
}
