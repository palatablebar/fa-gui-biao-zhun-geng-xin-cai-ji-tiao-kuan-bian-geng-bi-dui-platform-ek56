<template>
  <div>
    <PageHeader
      eyebrow="比对与变更 · clause alignment"
      :title="run ? `${run.title || run.document_key} · ${run.base_label} → ${run.target_label}` : '条款比对结果'"
      description="按「第X条」切分后做编号相似 + TF-IDF 余弦 + SimHash 汉明距对齐；编号重排被静默吸收，只有正文变化才进入变更项。"
    >
      <template #actions>
        <RouterLink to="/changes/review" class="btn" data-test="goto-review">去确认变更</RouterLink>
        <button class="btn" :disabled="!canExport || busyExport" data-test="export-md" @click="exportAs('md')">导出 MD</button>
        <button class="btn" :disabled="!canExport || busyExport" data-test="export-csv" @click="exportAs('csv')">导出 CSV</button>
      </template>
    </PageHeader>

    <ErrorNotice :error="error" @retry="reload" />
    <p v-if="notice" class="notice">{{ notice }}</p>

    <div v-if="run?.status === 'queued' || run?.status === 'running'" class="working rise">
      <span class="working__spinner"></span>
      <div>
        <div class="working__title">worker 正在切分与对齐条款…</div>
        <div class="working__hint">批次 {{ run.id.slice(0, 8) }} · 状态 {{ RUN_STATUS_LABELS[run.status] }} · 每 700ms 轮询一次</div>
      </div>
    </div>

    <div v-else-if="run?.status === 'failed'" class="failed">
      <div class="label">比对失败</div>
      <p>{{ run.error_message || '未知错误' }}</p>
      <button class="btn" @click="reload">重试读取</button>
    </div>

    <template v-if="run && run.status === 'succeeded'">
      <section class="stats rise" aria-label="比对统计">
        <div class="stat stat--wide">
          <div class="label">条款规模</div>
          <div class="stat__value num">
            {{ stats.total_old ?? '—' }} <span class="stat__dim">→</span> {{ stats.total_new ?? '—' }}
          </div>
          <div class="stat__foot">旧 → 新（条）</div>
        </div>
        <div class="stat">
          <div class="label">变更项</div>
          <div class="stat__value num">{{ run.change_count }}</div>
          <div class="stat__foot">未变 {{ stats.unchanged ?? 0 }} · 匹配 {{ stats.matched ?? 0 }}</div>
        </div>
        <div class="stat">
          <div class="label">判定分布</div>
          <div class="stat__seals">
            <SeverityTag severity="major" :label="`重大 ${severity.major ?? 0}`" />
            <SeverityTag severity="general" :label="`一般 ${severity.general ?? 0}`" />
            <SeverityTag severity="editorial" :label="`编辑性 ${severity.editorial ?? 0}`" />
          </div>
          <div class="stat__foot">解析问题 {{ severity.unparsed ?? 0 }} 条</div>
        </div>
        <div class="stat">
          <div class="label">编号重排</div>
          <div class="stat__value num">{{ stats.renumbered_pairs ?? 0 }}</div>
          <div class="stat__foot">
            {{ stats.renumber_noise_free ? '0 误报（按正文配对）' : '存在误报' }}
          </div>
        </div>
        <div class="stat">
          <div class="label">相似度分布</div>
          <div class="stat__value num">{{ stats.substantial_modified ?? 0 }}</div>
          <div class="stat__foot">实质修改 / 措辞 {{ stats.wording_modified ?? 0 }}</div>
        </div>
      </section>

      <div class="filters">
        <div class="filters__row">
          <button
            class="chip"
            :class="{ 'chip--on': filter.severity.value === 'all' }"
            data-test="severity-filter-all"
            @click="filter.setSeverity('all')"
          >
            全部 {{ filter.counts.value.all }}
          </button>
          <button
            v-for="level in SEVERITY_ORDER"
            :key="level"
            class="chip"
            :class="{ 'chip--on': filter.severity.value === level }"
            :data-test="`severity-filter-${level}`"
            @click="filter.setSeverity(level)"
          >
            {{ SEVERITY_LABELS[level] }} {{ filter.counts.value[level] }}
          </button>
        </div>
        <div class="filters__row filters__row--right">
          <input v-model="filter.keyword.value" class="field filters__search" placeholder="按条文关键词过滤" />
        </div>
      </div>

      <section class="changes" aria-label="变更条款">
        <ClauseDiffCard v-for="change in filter.filtered.value" :key="change.id" :change="change" data-test="change-card" />
        <EmptyState
          v-if="!filter.filtered.value.length"
          title="没有符合筛选条件的变更"
          hint="把级别筛选切回「全部」，或清空关键词。"
          action-text="清空筛选"
          @action="resetFilter"
        />
      </section>
    </template>

    <EmptyState
      v-else-if="!run && !loading"
      title="批次不存在或已删除"
      hint="回到文档版本时间线，重新选择左右版本发起比对。"
      action-text="回到台账"
      @action="router.push('/documents')"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ClauseDiffCard from '../components/common/ClauseDiffCard.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PageHeader from '../components/common/PageHeader.vue'
import SeverityTag from '../components/common/SeverityTag.vue'
import { SEVERITY_LABELS, SEVERITY_ORDER } from '../constants/enums'
import { downloadExport } from '../api/change'
import { useClauseFilter } from '../hooks/useClauseFilter'
import { useAuthStore } from '../stores/authStore'
import { useDiffStore } from '../stores/diffStore'
import type { ApiError } from '../types/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const diffStore = useDiffStore()

const runId = computed(() => String(route.params.id ?? ''))
const run = computed(() => diffStore.currentRun)
const changes = computed(() => diffStore.changes)
const stats = computed(() => run.value?.stats ?? {})
const severity = computed<Record<string, number>>(() => run.value?.severity_counts ?? {})

const loading = ref(false)
const error = ref<ApiError | null>(null)
const notice = ref('')
const busyExport = ref(false)
const canExport = computed(() => auth.can('changes:export'))

const filter = useClauseFilter(() => changes.value)

function resetFilter() {
  filter.setSeverity('all')
  filter.changeType.value = 'all'
  filter.keyword.value = ''
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const loaded = await diffStore.loadRun(runId.value)
    if (loaded.status === 'queued' || loaded.status === 'running') {
      const finished = await diffStore.pollUntilDone(runId.value)
      if (finished.status === 'queued' || finished.status === 'running') {
        error.value = { code: 'DIFF_TIMEOUT', message: 'worker 60 秒内未完成比对，请检查 worker 容器日志' }
        return
      }
    }
    await diffStore.loadChanges(runId.value)
  } catch (caught) {
    error.value = caught as ApiError
  } finally {
    loading.value = false
  }
}

async function exportAs(format: 'md' | 'csv') {
  busyExport.value = true
  notice.value = ''
  try {
    await downloadExport(runId.value, format)
    notice.value = `已生成 ${format.toUpperCase()} 文件（内容来自后端 /api/diffs/${runId.value}/export）`
  } catch (caught) {
    error.value = caught as ApiError
  } finally {
    busyExport.value = false
  }
}

async function reload() {
  await load()
}

watch(runId, load)
onMounted(load)
</script>

<style scoped>
.notice {
  margin-top: 12px;
  font-size: 11.5px;
  color: var(--moss);
  border-left: 2px solid var(--moss);
  padding-left: 9px;
}
.working {
  display: flex;
  gap: 14px;
  align-items: center;
  border: 1px solid var(--rule);
  background: var(--paper-2);
  padding: 18px 20px;
}
.working__spinner {
  width: 16px;
  height: 16px;
  border: 1px solid var(--rule);
  border-top-color: var(--seal);
  border-radius: 50%;
  animation: spin 900ms linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.working__title {
  font-family: var(--serif);
  font-size: 14px;
}
.working__hint {
  font-size: 11px;
  color: var(--ink-faint);
  margin-top: 3px;
}
.failed {
  border-left: 3px solid var(--seal);
  padding: 12px 16px;
  background: color-mix(in oklch, var(--seal) 5%, var(--paper-2));
  margin-top: 16px;
}
.failed p {
  margin: 6px 0 10px;
  font-size: 12px;
  color: var(--ink-soft);
}

.stats {
  display: grid;
  grid-template-columns: 1.4fr repeat(4, minmax(0, 1fr));
  border-top: 2px solid var(--ink);
  border-bottom: 1px solid var(--rule);
  margin-bottom: 20px;
}
.stat {
  padding: 13px 14px 12px 0;
  border-right: 1px dotted var(--rule-soft);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat:last-child {
  border-right: 0;
}
.stat--wide .stat__value {
  font-size: 26px;
}
.stat__value {
  font-size: 21px;
  font-family: var(--sans);
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 1.1;
}
.stat__dim {
  color: var(--rule);
  font-weight: 400;
}
.stat__foot {
  font-size: 10px;
  color: var(--ink-faint);
}
.stat__seals {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.filters__row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.filters__search {
  width: 240px;
  padding: 5px 9px;
  font-size: 11.5px;
}
.changes {
  margin-top: 4px;
}

@media (max-width: 1100px) {
  .stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 768px) {
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .filters__search {
    width: 100%;
  }
}
</style>
