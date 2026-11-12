export type SourceKind = 'national_standard' | 'regulatory' | 'local_env'
export type DocumentStatus = 'current' | 'superseded' | 'collected'
export type DiffRunStatus = 'queued' | 'running' | 'succeeded' | 'failed'
export type ChangeType = 'added' | 'removed' | 'modified' | 'unchanged'
export type Severity = 'major' | 'general' | 'editorial' | 'unparsed'
export type Industry = 'manufacturing' | 'medical' | 'environmental'

export interface SourceItem {
  id: string
  code: string
  name: string
  kind: SourceKind
  base_url: string
  fetch_cycle: string
  owner_note: string
  enabled: boolean
  version_count: number
  last_crawled_at: string | null
  next_issue_hint: string | null
}

export interface DocumentVersion {
  id: string
  document_key: string
  title: string
  issuer: string
  source_id: string
  version_label: string
  version_no: number
  status: DocumentStatus
  issued_at: string | null
  effective_at: string | null
  clause_count: number
  content_hash: string
  collected_at: string | null
}

export interface Clause {
  index: number
  label: string
  number: number | null
  text: string
  sub_items: string[]
  char_count: number
}

export interface DocumentGroup {
  document_key: string
  title: string
  issuer: string
  source: string
  source_code: string
  source_id: string
  versions: DocumentVersion[]
  current_version: string
}

export interface VersionDetail extends DocumentVersion {
  clauses: Clause[]
  parse_issues: { reason: string; detail: string; clause_label: string }[]
  raw_text: string
  diff_history: {
    id: string
    base_label: string
    target_label: string
    status: DiffRunStatus
    change_count: number
    created_at: string | null
  }[]
}

export interface DiffStats {
  total_old?: number
  total_new?: number
  matched?: number
  unchanged?: number
  modified?: number
  substantial_modified?: number
  wording_modified?: number
  added?: number
  removed?: number
  renumbered_pairs?: number
  renumber_noise_free?: boolean
  change_count?: number
  base_label?: string
  target_label?: string
  base_clause_count?: number
  target_clause_count?: number
  unparsed_old?: number
  unparsed_new?: number
  severity?: Record<string, number>
  algorithm_version?: string
  dispatch?: string
}

export interface DiffRun {
  id: string
  document_key: string
  title: string
  base_version_id: string
  target_version_id: string
  base_label: string
  target_label: string
  status: DiffRunStatus
  algorithm_version: string
  stats: DiffStats
  severity_counts: Record<string, number>
  change_count: number
  error_message: string
  created_at: string | null
  started_at: string | null
  finished_at: string | null
  published_at: string | null
  publish_note: string
}

export interface ChangeItem {
  id: string
  diff_run_id: string
  change_type: ChangeType
  change_type_label: string
  severity: Severity
  severity_label: string
  clause_no_old: number | null
  clause_no_new: number | null
  clause_label_old: string
  clause_label_new: string
  old_text: string
  new_text: string
  similarity: number
  edit_ratio: number
  keywords: string[]
  industries: Industry[]
  reason: string
  confirmed: boolean
  confirmed_at: string | null
  impact_industries: Industry[]
  impact_note: string
  published: boolean
  published_at: string | null
  publish_note: string
}

export interface PublishedGroup {
  diff_run_id: string
  document_key: string
  title: string
  issuer: string
  base_label: string
  target_label: string
  published_at: string | null
  publish_note: string
  effective_at: string | null
  changes: ChangeItem[]
  severity_counts: Record<string, number>
}
