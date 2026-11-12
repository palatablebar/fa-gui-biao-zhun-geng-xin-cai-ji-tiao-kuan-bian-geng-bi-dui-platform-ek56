<template>
  <div>
    <PageHeader
      eyebrow="采集与版本 · sources & versions"
      title="文档版本时间线"
      description="三个来源每周巡检一次；采集只落新版本、不覆盖已确认的历史。选中左右版本即可发起条款比对，编号重排不会产生噪声。"
    >
      <template #actions>
        <button class="btn" data-test="refresh-documents" :disabled="catalog.loading" @click="refresh">
          {{ catalog.loading ? '读取中…' : '刷新台账' }}
        </button>
      </template>
    </PageHeader>

    <ErrorNotice :error="catalog.error ? { code: 'LOAD_FAILED', message: catalog.error } : null" @retry="refresh" />
    <ErrorNotice
      v-if="actionError"
      :error="actionError"
      :retryable="false"
      @retry="actionError = null"
    />
    <p v-if="notice" class="notice">{{ notice }}</p>

    <section class="sources" aria-label="采集来源">
      <article
        v-for="source in catalog.sources"
        :key="source.id"
        class="source rise"
        :class="{ 'source--idle': !source.version_count }"
      >
        <header class="source__head">
          <span class="eyebrow">{{ SOURCE_KIND_LABELS[source.kind] ?? source.kind }}</span>
          <StatusSeal :label="source.enabled ? '启用' : '停用'" :tone="source.enabled ? 'moss' : 'ink'" size="sm" />
        </header>
        <h2 class="source__name">{{ source.name }}</h2>
        <p class="source__note">{{ source.owner_note }}</p>
        <dl class="source__meta">
          <div>
            <dt>巡检</dt>
            <dd>{{ source.fetch_cycle }}</dd>
          </div>
          <div>
            <dt>在库版本</dt>
            <dd class="num">{{ source.version_count }}</dd>
          </div>
          <div>
            <dt>上次采集</dt>
            <dd class="num">{{ formatDateTime(source.last_crawled_at) }}</dd>
          </div>
        </dl>
        <div class="source__foot">
          <span class="label">{{ source.version_count ? '可采集' : '暂无入库文档' }}</span>
          <button
            class="btn btn--seal"
            :disabled="!auth.can('sources:crawl') || crawlingId === source.id"
            :title="auth.can('sources:crawl') ? '把来源里发布的新版本拉进台账' : '当前角色无采集权限'"
            :data-test="`crawl-${source.code}`"
            @click="handleCrawl(source)"
          >
            {{ crawlingId === source.id ? '采集…' : '采集新版本' }}
          </button>
        </div>
      </article>
      <EmptyState
        v-if="!catalog.sources.length && !catalog.loading"
        title="来源尚未登记"
        hint="seed 会把三个来源写入 sources 表；如果这里为空，说明 seed 没有执行成功。"
        action-text="重新读取"
        @action="refresh"
      />
    </section>

    <section class="docs" aria-label="法规文档">
      <div v-for="document in catalog.documents" :key="document.document_key" class="doc rise">
        <header class="doc__head">
          <div>
            <div class="eyebrow">{{ document.source }} · {{ document.source_code }}</div>
            <h2 class="doc__title">{{ document.title }}</h2>
            <div class="doc__meta">
              <span class="num">{{ document.document_key }}</span>
              <span>{{ document.issuer }}</span>
              <span>现行 {{ document.current_version || '—' }}</span>
            </div>
          </div>
          <StatusSeal :label="`共 ${document.versions.length} 版`" tone="indigo" size="sm" />
        </header>

        <ol class="timeline">
          <li
            v-for="version in document.versions"
            :key="version.id"
            class="timeline__item"
            :class="[`timeline__item--${version.status}`, { 'is-current': version.status === 'current' }]"
          >
            <div class="timeline__tick"></div>
            <div class="timeline__label serif">{{ version.version_label }}</div>
            <div class="timeline__body">
              <div class="timeline__row">
                <span class="num">{{ version.clause_count }} 条</span>
                <span class="timeline__date">{{ formatDate(version.issued_at) }} 发布</span>
              </div>
              <div class="timeline__row">
                <span class="label">{{ formatDate(version.effective_at) }} 实施</span>
                <StatusSeal
                  :label="DOCUMENT_STATUS_LABELS[version.status]"
                  :tone="version.status === 'current' ? 'moss' : version.status === 'collected' ? 'ochre' : 'ink'"
                  size="sm"
                />
              </div>
            </div>
          </li>
        </ol>

        <div v-if="selection[document.document_key]" class="doc__control">
          <div class="control__field">
            <span class="label">左（旧）</span>
            <select v-model="selection[document.document_key].base" class="field" :data-test="`base-${document.document_key}`">
              <option v-for="version in document.versions" :key="version.id" :value="version.id">
                {{ version.version_label }} · {{ version.clause_count }} 条
              </option>
            </select>
          </div>
          <span class="control__arrow">→</span>
          <div class="control__field">
            <span class="label">右（新）</span>
            <select v-model="selection[document.document_key].target" class="field" :data-test="`target-${document.document_key}`">
              <option v-for="version in document.versions" :key="version.id" :value="version.id">
                {{ version.version_label }} · {{ version.clause_count }} 条
              </option>
            </select>
          </div>
          <button
            class="btn btn--solid control__run"
            :disabled="!auth.can('diffs:run') || runningKey === document.document_key"
            :title="auth.can('diffs:run') ? '切分条款并对齐比对' : '当前角色无比对权限'"
            :data-test="`run-diff-${document.document_key}`"
            @click="handleDiff(document)"
          >
            {{ runningKey === document.document_key ? '比对中…' : '发起比对' }}
          </button>
        </div>

        <div v-if="runsByDocument(document.document_key).length" class="doc__runs">
          <div class="label">最近批次</div>
          <RouterLink
            v-for="run in runsByDocument(document.document_key)"
            :key="run.id"
            :to="`/diffs/${run.id}`"
            class="run-link"
          >
            <span class="run-link__pair serif">{{ run.base_label }} → {{ run.target_label }}</span>
            <span class="run-link__count num">{{ run.change_count }} 条变更</span>
            <SeverityTag v-if="run.severity_counts?.major" severity="major" :label="`重大 ${run.severity_counts.major}`" />
            <StatusSeal :label="RUN_STATUS_LABELS[run.status]" :tone="run.status === 'failed' ? 'seal' : 'indigo'" size="sm" />
          </RouterLink>
        </div>
        <div v-else class="doc__runs doc__runs--empty">
          <span class="label">还没有比对批次</span>
          <span class="doc__hint">选择左右版本后点「发起比对」。</span>
        </div>
      </div>

      <EmptyState
        v-if="!catalog.documents.length && !catalog.loading"
        title="法规台账还没有文档"
        hint="seed 会写入两部法规共 6 个版本；采集新版本后，新版本会以「待比对」状态出现在时间线上。"
        action-text="重新读取"
        @action="refresh"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PageHeader from '../components/common/PageHeader.vue'
import SeverityTag from '../components/common/SeverityTag.vue'
import StatusSeal from '../components/common/StatusSeal.vue'
import { DOCUMENT_STATUS_LABELS, RUN_STATUS_LABELS, SOURCE_KIND_LABELS } from '../constants/enums'
import { useAuthStore } from '../stores/authStore'
import { useCatalogStore } from '../stores/catalogStore'
import { useDiffStore } from '../stores/diffStore'
import type { ApiError } from '../types/api'
import type { DocumentGroup, DiffRun, SourceItem } from '../types/domain'
import { formatDate, formatDateTime } from '../utils/format'

const router = useRouter()
const auth = useAuthStore()
const catalog = useCatalogStore()
const diffStore = useDiffStore()

const crawlingId = ref('')
const runningKey = ref('')
const actionError = ref<ApiError | null>(null)
const notice = ref('')
const selection = reactive<Record<string, { base: string; target: string }>>({})

function ensureSelections() {
  for (const document of catalog.documents) {
    if (selection[document.document_key]) continue
    const sorted = [...document.versions].sort((left, right) => left.version_no - right.version_no)
    const collected = sorted.find((version) => version.status === 'collected')
    const latest = sorted[sorted.length - 1]
    const target = collected ?? latest
    const previous = [...sorted].reverse().find((version) => version.id !== target?.id)
    selection[document.document_key] = {
      base: previous?.id ?? sorted[0]?.id ?? '',
      target: target?.id ?? '',
    }
  }
}

function runsByDocument(documentKey: string): DiffRun[] {
  return diffStore.runs.filter((run) => run.document_key === documentKey).slice(0, 4)
}

async function refresh() {
  await Promise.all([catalog.load(), diffStore.loadRuns()])
  ensureSelections()
}

async function handleCrawl(source: SourceItem) {
  actionError.value = null
  notice.value = ''
  crawlingId.value = source.id
  try {
    const result = await catalog.crawl(source.id)
    notice.value = `已采集 ${result.version.document_key} ${result.version.version_label}：${result.clause_count} 条 · ${result.note}`
    await diffStore.loadRuns()
    ensureSelections()
    const key = result.version.document_key
    if (selection[key]) selection[key].target = result.version.id
  } catch (caught) {
    actionError.value = caught as ApiError
  } finally {
    crawlingId.value = ''
  }
}

async function handleDiff(document: DocumentGroup) {
  actionError.value = null
  notice.value = ''
  const picked = selection[document.document_key]
  if (!picked?.base || !picked?.target) {
    actionError.value = { code: 'SELECTION_EMPTY', message: '请先选择左右两个版本' }
    return
  }
  runningKey.value = document.document_key
  try {
    const run = await diffStore.run(picked.base, picked.target)
    await router.push(`/diffs/${run.id}`)
  } catch (caught) {
    actionError.value = caught as ApiError
  } finally {
    runningKey.value = ''
  }
}

onMounted(refresh)
</script>

<style scoped>
.notice {
  margin-top: 12px;
  font-size: 11.5px;
  color: var(--moss);
  border-left: 2px solid var(--moss);
  padding-left: 9px;
}

.sources {
  display: grid;
  grid-template-columns: 1.35fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 30px;
}
.source {
  border-top: 2px solid var(--ink);
  padding: 12px 0 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.source--idle {
  border-top-color: var(--rule);
}
.source__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.source__name {
  font-family: var(--serif);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
}
.source__note {
  font-size: 11.5px;
  color: var(--ink-soft);
  line-height: 1.7;
  flex: 1;
}
.source__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 18px;
  margin: 0;
  padding-top: 8px;
  border-top: 1px solid var(--rule-soft);
}
.source__meta div {
  display: flex;
  gap: 6px;
  align-items: baseline;
}
.source__meta dt {
  font-size: 9.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.source__meta dd {
  margin: 0;
  font-size: 11px;
}
.source__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 4px;
}
.source__foot .btn {
  font-size: 10.5px;
  padding: 5px 9px;
}

.docs {
  display: flex;
  flex-direction: column;
  gap: 34px;
}
.doc {
  border-top: 1px solid var(--rule);
  padding-top: 16px;
}
.doc__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.doc__title {
  font-family: var(--serif);
  font-size: clamp(17px, 1.8vw, 21px);
  font-weight: 600;
  margin-top: 4px;
}
.doc__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
  margin-top: 6px;
  font-size: 11px;
  color: var(--ink-soft);
}

.timeline {
  list-style: none;
  margin: 18px 0 0;
  padding: 0;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(132px, 1fr);
  gap: 0;
  overflow-x: auto;
  border-top: 1px solid var(--rule-soft);
}
.timeline__item {
  position: relative;
  padding: 16px 14px 12px 0;
  border-right: 1px dotted var(--rule-soft);
  min-width: 132px;
}
.timeline__item:last-child {
  border-right: 0;
}
.timeline__tick {
  position: absolute;
  top: -4px;
  left: 0;
  width: 7px;
  height: 7px;
  background: var(--paper-4);
  transform: rotate(45deg);
}
.timeline__item.is-current .timeline__tick {
  background: var(--seal);
}
.timeline__label {
  font-size: 17px;
  color: var(--ink-soft);
}
.timeline__item.is-current .timeline__label {
  color: var(--seal);
  font-weight: 600;
}
.timeline__body {
  margin-top: 7px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.timeline__row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10.5px;
  color: var(--ink-soft);
  flex-wrap: wrap;
}
.timeline__date {
  color: var(--ink-faint);
  font-size: 10px;
}

.doc__control {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-top: 14px;
  flex-wrap: wrap;
}
.control__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 168px;
}
.control__field .field {
  padding: 6px 8px;
  font-size: 11.5px;
}
.control__arrow {
  color: var(--rule);
  padding-bottom: 8px;
}
.control__run {
  margin-left: auto;
  font-size: 11px;
}

.doc__runs {
  margin-top: 16px;
  border-top: 1px solid var(--rule-soft);
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.doc__runs--empty {
  flex-direction: row;
  gap: 12px;
  align-items: baseline;
}
.doc__hint {
  font-size: 11px;
  color: var(--ink-faint);
}
.run-link {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 6px 0;
  border-bottom: 1px dotted var(--rule-soft);
  color: var(--ink);
  font-size: 11.5px;
}
.run-link:hover {
  text-decoration: none;
  background: var(--paper-2);
}
.run-link__pair {
  font-size: 13px;
  min-width: 96px;
}
.run-link__count {
  color: var(--ink-soft);
}

@media (max-width: 1100px) {
  .sources {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }
}
@media (max-width: 768px) {
  .sources {
    grid-template-columns: minmax(0, 1fr);
  }
  .control__run {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }
}
</style>
