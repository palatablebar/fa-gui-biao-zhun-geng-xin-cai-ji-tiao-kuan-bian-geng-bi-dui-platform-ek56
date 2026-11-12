import { defineStore } from 'pinia'
import { crawlSource, fetchDocuments, fetchSources } from '../api/catalog'
import type { DocumentGroup, DocumentVersion, SourceItem } from '../types/domain'

interface CatalogState {
  sources: SourceItem[]
  documents: DocumentGroup[]
  loading: boolean
  error: string
  lastCrawled: DocumentVersion | null
}

export const useCatalogStore = defineStore('catalog', {
  state: (): CatalogState => ({
    sources: [],
    documents: [],
    loading: false,
    error: '',
    lastCrawled: null,
  }),
  getters: {
    enabledSources: (state): SourceItem[] => state.sources.filter((source) => source.enabled),
    totalVersions: (state): number =>
      state.documents.reduce((sum, document) => sum + document.versions.length, 0),
    collectedVersions: (state): DocumentVersion[] =>
      state.documents.flatMap((document) =>
        document.versions.filter((version) => version.status === 'collected'),
      ),
  },
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [sources, documents] = await Promise.all([fetchSources(), fetchDocuments()])
        this.sources = sources.items
        this.documents = documents.items
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '加载法规台账失败'
      } finally {
        this.loading = false
      }
    },
    async crawl(sourceId: string) {
      const result = await crawlSource(sourceId)
      this.lastCrawled = result.version
      await this.load()
      return result
    },
  },
})
