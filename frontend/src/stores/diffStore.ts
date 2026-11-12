import { defineStore } from 'pinia'
import { createDiff, fetchRun, fetchRunChanges, fetchRuns } from '../api/diff'
import type { ChangeItem, DiffRun } from '../types/domain'

interface DiffState {
  runs: DiffRun[]
  currentRun: DiffRun | null
  changes: ChangeItem[]
  loading: boolean
  error: string
}

export const useDiffStore = defineStore('diff', {
  state: (): DiffState => ({
    runs: [],
    currentRun: null,
    changes: [],
    loading: false,
    error: '',
  }),
  getters: {
    severityCounts: (state): Record<string, number> => state.currentRun?.severity_counts ?? {},
    confirmedCount: (state): number => state.changes.filter((change) => change.confirmed).length,
    publishedCount: (state): number => state.changes.filter((change) => change.published).length,
  },
  actions: {
    async loadRuns(documentKey?: string) {
      try {
        const result = await fetchRuns(documentKey)
        this.runs = result.items
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '加载比对批次失败'
      }
    },
    async run(baseVersionId: string, targetVersionId: string) {
      const result = await createDiff(baseVersionId, targetVersionId)
      this.currentRun = result.run
      return result.run
    },
    async loadRun(runId: string) {
      const result = await fetchRun(runId)
      this.currentRun = result.run
      return result.run
    },
    async loadChanges(runId: string) {
      const result = await fetchRunChanges(runId)
      this.currentRun = result.run
      this.changes = result.items
      return result
    },
    async pollUntilDone(runId: string, timeoutMs = 60000): Promise<DiffRun> {
      const started = Date.now()
      let last = (await this.loadRun(runId)) as DiffRun
      while (last.status === 'queued' || last.status === 'running') {
        if (Date.now() - started > timeoutMs) return last
        await new Promise((resolve) => setTimeout(resolve, 700))
        last = await this.loadRun(runId)
      }
      return last
    },
  },
})
