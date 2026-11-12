<template>
  <div>
    <PageHeader
      eyebrow="客户视图 · published notes"
      title="已发布变更说明"
      description="客户合规台账只读视图：仅展示合规总监已发布的变更，含算法判级、影响行业与台账动作说明。"
    >
      <template #actions>
        <button class="btn" data-test="refresh-published" :disabled="loading" @click="load">
          {{ loading ? '读取中…' : '刷新' }}
        </button>
      </template>
    </PageHeader>

    <ErrorNotice :error="error" @retry="load" />
    <p v-if="notice" class="notice">{{ notice }}</p>

    <section v-for="group in groups" :key="group.diff_run_id" class="note rise">
      <header class="note__head">
        <div>
          <div class="eyebrow">{{ group.document_key }} · {{ group.issuer }}</div>
          <h2 class="note__title">{{ group.title }}</h2>
          <div class="note__transition">
            <span class="serif note__version">{{ group.base_label }}</span>
            <span class="note__arrow">→</span>
            <span class="serif note__version note__version--current">{{ group.target_label }}</span>
            <span class="note__effective">
              发布于 {{ formatDateTime(group.published_at) }}
              <template v-if="group.effective_at"> · {{ formatDate(group.effective_at) }} 实施</template>
            </span>
          </div>
        </div>
        <div class="note__stamps">
          <StatusSeal label="已发布" tone="seal" />
          <div class="note__counts">
            <span class="num">{{ group.changes.length }}</span>
            <span class="label">条变更</span>
          </div>
        </div>
      </header>

      <blockquote v-if="group.publish_note" class="note__publish">
        {{ group.publish_note }}
      </blockquote>

      <div class="note__summary">
        <SeverityTag severity="major" :label="`重大 ${group.severity_counts.major ?? 0}`" />
        <SeverityTag severity="general" :label="`一般 ${group.severity_counts.general ?? 0}`" />
        <SeverityTag severity="editorial" :label="`编辑性 ${group.severity_counts.editorial ?? 0}`" />
        <div class="note__exports">
          <button
            class="btn btn--quiet"
            :disabled="!auth.can('changes:export') || exportingId === group.diff_run_id"
            data-test="published-export-md"
            @click="exportAs(group.diff_run_id, 'md')"
          >
            导出 MD
          </button>
          <button
            class="btn btn--quiet"
            :disabled="!auth.can('changes:export') || exportingId === group.diff_run_id"
            data-test="published-export-csv"
            @click="exportAs(group.diff_run_id, 'csv')"
          >
            导出 CSV
          </button>
        </div>
      </div>

      <div class="note__changes">
        <ClauseDiffCard v-for="change in group.changes" :key="change.id" :change="change" compact />
      </div>
    </section>

    <EmptyState
      v-if="!groups.length && !loading"
      title="客户视图还没有发布说明"
      hint="流程是：采集新版本 → 比对 → 确认至少 2 条变更并标注影响行业 → 合规总监发布。发布后这里才会出现内容。"
      action-text="回文档版本时间线"
      @action="router.push('/documents')"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ClauseDiffCard from '../components/common/ClauseDiffCard.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PageHeader from '../components/common/PageHeader.vue'
import SeverityTag from '../components/common/SeverityTag.vue'
import StatusSeal from '../components/common/StatusSeal.vue'
import { downloadExport, fetchPublicChanges } from '../api/change'
import { useAuthStore } from '../stores/authStore'
import type { ApiError } from '../types/api'
import type { PublishedGroup } from '../types/domain'
import { formatDate, formatDateTime } from '../utils/format'

const router = useRouter()
const auth = useAuthStore()

const groups = ref<PublishedGroup[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)
const notice = ref('')
const exportingId = ref('')

async function load() {
  loading.value = true
  error.value = null
  try {
    const result = await fetchPublicChanges()
    groups.value = result.items
  } catch (caught) {
    error.value = caught as ApiError
  } finally {
    loading.value = false
  }
}

async function exportAs(runId: string, format: 'md' | 'csv') {
  exportingId.value = runId
  notice.value = ''
  try {
    await downloadExport(runId, format)
    notice.value = `已导出 ${format.toUpperCase()} 变更说明（批次 ${runId.slice(0, 8)}）`
  } catch (caught) {
    error.value = caught as ApiError
  } finally {
    exportingId.value = ''
  }
}

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
.note {
  border-top: 1px solid var(--rule);
  padding-top: 18px;
  margin-bottom: 34px;
}
.note__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}
.note__title {
  font-family: var(--serif);
  font-size: clamp(19px, 2vw, 25px);
  font-weight: 600;
  margin-top: 5px;
  line-height: 1.25;
}
.note__transition {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: 9px;
  flex-wrap: wrap;
}
.note__version {
  font-size: 17px;
  color: var(--ink-soft);
}
.note__version--current {
  color: var(--seal);
  font-weight: 600;
}
.note__arrow {
  color: var(--rule);
}
.note__effective {
  font-size: 10.5px;
  color: var(--ink-faint);
  margin-left: 6px;
}
.note__stamps {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  flex-shrink: 0;
}
.note__counts {
  text-align: right;
}
.note__counts .num {
  display: block;
  font-size: 24px;
  font-weight: 600;
  line-height: 1;
}
.note__publish {
  margin: 14px 0 0;
  padding: 10px 14px;
  border-left: 3px solid var(--seal);
  background: color-mix(in oklch, var(--paper-3) 45%, var(--paper-2));
  font-family: var(--serif);
  font-size: 12.5px;
  line-height: 1.8;
}
.note__summary {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
  padding-bottom: 6px;
}
.note__exports {
  margin-left: auto;
  display: flex;
  gap: 4px;
}
.note__exports .btn {
  font-size: 10.5px;
  padding: 4px 8px;
}
.note__changes {
  margin-top: 4px;
}
@media (max-width: 768px) {
  .note__head {
    flex-direction: column;
    gap: 10px;
  }
  .note__exports {
    margin-left: 0;
  }
}
</style>
