<template>
  <div>
    <PageHeader
      eyebrow="比对与变更 · review & publish"
      title="变更确认与影响标注"
      description="分析师逐条确认算法判级，补上影响行业与台账动作；只有「已确认」的变更才能被合规总监发布。"
    >
      <template #actions>
        <button class="btn" :disabled="loading" data-test="refresh-review" @click="reload">
          {{ loading ? '读取中…' : '刷新队列' }}
        </button>
      </template>
    </PageHeader>

    <ErrorNotice :error="error" @retry="reload" />
    <ErrorNotice v-if="actionError" :error="actionError" :retryable="false" @retry="actionError = null" />
    <p v-if="notice" class="notice">{{ notice }}</p>

    <div class="review">
      <section class="review__queue">
        <div class="queue__head">
          <div class="label">待确认队列</div>
          <div class="num queue__count">{{ pending.length }} 条</div>
          <div class="queue__hint">来自所有已完成的比对批次</div>
        </div>

        <article v-for="change in pending" :key="change.id" class="pending">
          <ClauseDiffCard :change="change">
            <template #actions>
              <div class="confirm">
                <div class="confirm__row">
                  <span class="label">影响行业</span>
                  <button
                    v-for="industry in INDUSTRY_ORDER"
                    :key="industry"
                    class="chip"
                    :class="{ 'chip--on': draftOf(change.id).industries.includes(industry) }"
                    :data-test="`industry-${change.id}-${industry}`"
                    @click="toggleIndustry(change.id, industry)"
                  >
                    {{ INDUSTRY_LABELS[industry] }}
                  </button>
                </div>
                <div class="confirm__row">
                  <span class="label">影响说明</span>
                  <input
                    v-model="draftOf(change.id).note"
                    class="field confirm__note"
                    :data-test="`note-${change.id}`"
                    placeholder="例如：涉及 6 家制药客户在线监测参数，需在 2027-01-01 前更新台账"
                  />
                  <button
                    class="btn btn--seal confirm__button"
                    :disabled="!auth.can('changes:confirm') || busyId === change.id"
                    :title="auth.can('changes:confirm') ? '确认这条变更' : '当前角色无确认权限'"
                    :data-test="`confirm-${change.id}`"
                    @click="confirm(change)"
                  >
                    {{ busyId === change.id ? '确认…' : '确认变更' }}
                  </button>
                </div>
              </div>
            </template>
          </ClauseDiffCard>
        </article>

        <EmptyState
          v-if="!pending.length && !loading"
          title="队列已清空"
          hint="没有待确认的变更：要么本批次都已确认，要么还没跑比对。去文档版本时间线发起一次比对。"
          action-text="去发起比对"
          @action="router.push('/documents')"
        />
      </section>

      <aside class="review__publish">
        <div class="publish rise">
          <div class="eyebrow">publish</div>
          <h2 class="publish__title">发布变更说明</h2>
          <p class="publish__desc">
            发布后，已确认变更出现在客户视图，目标版本成为「现行」，旧版本自动转为历史。
          </p>

          <label class="publish__field">
            <span class="label">选择批次</span>
            <select v-model="publishRunId" class="field" data-test="publish-run">
              <option value="">— 选择已完成的批次 —</option>
              <option v-for="option in publishableRuns" :key="option.id" :value="option.id">
                {{ option.document_key }} {{ option.base_label }} → {{ option.target_label }}（{{ option.change_count }} 条）
              </option>
            </select>
          </label>

          <label class="publish__field">
            <span class="label">发布说明</span>
            <textarea
              v-model="publishNote"
              class="field publish__textarea"
              data-test="publish-note"
              rows="3"
              placeholder="例如：客户台账与培训材料已同步至新口径。"
            ></textarea>
          </label>

          <button
            class="btn btn--solid publish__button"
            data-test="publish-submit"
            :disabled="!auth.can('changes:publish') || !publishRunId || publishing"
            :title="auth.can('changes:publish') ? '发布这个批次的已确认变更' : '仅合规总监可发布'"
            @click="publish"
          >
            {{ publishing ? '发布中…' : '发布到客户视图' }}
          </button>
          <p v-if="!auth.can('changes:publish')" class="publish__denied">
            当前角色（{{ auth.role }}）只能确认，发布需 admin。直接调接口会返回 403。
          </p>

          <div class="publish__rules">
            <div class="label">发布前置条件</div>
            <ul>
              <li>批次状态为 succeeded</li>
              <li>至少 1 条变更已确认并标注影响行业</li>
              <li>发布后不可回滚，只可再出新版本</li>
            </ul>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import ClauseDiffCard from '../components/common/ClauseDiffCard.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PageHeader from '../components/common/PageHeader.vue'
import { INDUSTRY_LABELS, INDUSTRY_ORDER } from '../constants/enums'
import { confirmChange, fetchPendingChanges, publishRun } from '../api/change'
import { useAuthStore } from '../stores/authStore'
import { useDiffStore } from '../stores/diffStore'
import type { ApiError } from '../types/api'
import type { ChangeItem, Industry } from '../types/domain'

const router = useRouter()
const auth = useAuthStore()
const diffStore = useDiffStore()

const pending = ref<ChangeItem[]>([])
const loading = ref(false)
const error = ref<ApiError | null>(null)
const actionError = ref<ApiError | null>(null)
const notice = ref('')
const busyId = ref('')
const publishing = ref(false)
const publishRunId = ref('')
const publishNote = ref('客户台账与培训材料已同步至新版本口径。')

const drafts = reactive<Record<string, { industries: Industry[]; note: string }>>({})

const publishableRuns = computed(() => diffStore.runs.filter((run) => run.status === 'succeeded'))

function draftOf(changeId: string) {
  if (!drafts[changeId]) drafts[changeId] = { industries: [], note: '' }
  return drafts[changeId]
}

function toggleIndustry(changeId: string, industry: Industry) {
  const draft = draftOf(changeId)
  const index = draft.industries.indexOf(industry)
  if (index >= 0) draft.industries.splice(index, 1)
  else draft.industries.push(industry)
}

async function loadPending() {
  const result = await fetchPendingChanges(60)
  pending.value = result.items
  for (const change of result.items) {
    const draft = draftOf(change.id)
    if (!draft.industries.length && !draft.note) {
      draft.industries = [...(change.industries ?? [])]
      draft.note = change.impact_note || ''
    }
  }
  ensurePublishRun(result.items)
}

function ensurePublishRun(items: ChangeItem[] = pending.value) {
  const runIds = new Set(publishableRuns.value.map((run) => run.id))
  if (publishRunId.value && runIds.has(publishRunId.value)) return
  const pendingRun = items.map((item) => item.diff_run_id).find((id) => runIds.has(id))
  publishRunId.value = pendingRun ?? publishableRuns.value[0]?.id ?? ''
}

async function reload() {
  loading.value = true
  error.value = null
  try {
    await Promise.all([loadPending(), diffStore.loadRuns()])
    ensurePublishRun()
  } catch (caught) {
    error.value = caught as ApiError
  } finally {
    loading.value = false
  }
}

async function confirm(change: ChangeItem) {
  actionError.value = null
  notice.value = ''
  busyId.value = change.id
  const draft = draftOf(change.id)
  try {
    await confirmChange(change.id, {
      impact_industries: draft.industries,
      impact_note: draft.note,
    })
    notice.value = `已确认 ${change.clause_label_new || change.clause_label_old}：${draft.industries.map((item) => INDUSTRY_LABELS[item]).join(' / ') || '未标注行业'}`
    await reload()
  } catch (caught) {
    actionError.value = caught as ApiError
  } finally {
    busyId.value = ''
  }
}

async function publish() {
  actionError.value = null
  notice.value = ''
  publishing.value = true
  try {
    const result = await publishRun(publishRunId.value, publishNote.value)
    notice.value = `已发布 ${result.published_changes.length} 条变更说明，客户视图已可见。`
    await reload()
  } catch (caught) {
    actionError.value = caught as ApiError
  } finally {
    publishing.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.notice {
  margin-top: 12px;
  font-size: 11.5px;
  color: var(--moss);
  border-left: 2px solid var(--moss);
  padding-left: 9px;
}
.review {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 322px;
  gap: 30px;
  align-items: start;
}
.queue__head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 8px;
}
.queue__count {
  font-size: 19px;
  font-weight: 600;
}
.queue__hint {
  margin-left: auto;
  font-size: 10.5px;
  color: var(--ink-faint);
}
.pending:first-of-type {
  border-top: 0;
}
.confirm {
  margin-top: 10px;
  border-top: 1px dashed var(--rule);
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.confirm__row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.confirm__note {
  flex: 1;
  min-width: 200px;
  padding: 5px 8px;
  font-size: 11.5px;
}
.confirm__button {
  font-size: 10.5px;
  padding: 5px 10px;
}

.review__publish {
  position: sticky;
  top: 18px;
}
.publish {
  border: 1px solid var(--rule);
  background: var(--paper-2);
  padding: 18px 18px 20px;
  border-top: 3px double var(--rule);
}
.publish__title {
  font-family: var(--serif);
  font-size: 17px;
  margin-top: 5px;
}
.publish__desc {
  margin-top: 6px;
  font-size: 11.5px;
  line-height: 1.7;
  color: var(--ink-soft);
}
.publish__field {
  display: block;
  margin-top: 13px;
}
.publish__field .label {
  display: block;
  margin-bottom: 4px;
}
.publish__textarea {
  resize: vertical;
  font-size: 11.5px;
  line-height: 1.65;
}
.publish__button {
  width: 100%;
  justify-content: center;
  margin-top: 14px;
  padding: 9px;
  font-size: 11px;
}
.publish__denied {
  margin-top: 8px;
  font-size: 10.5px;
  color: var(--seal);
  line-height: 1.6;
}
.publish__rules {
  margin-top: 16px;
  border-top: 1px solid var(--rule-soft);
  padding-top: 10px;
}
.publish__rules ul {
  margin: 6px 0 0;
  padding-left: 16px;
  font-size: 11px;
  color: var(--ink-soft);
  line-height: 1.85;
}
@media (max-width: 1100px) {
  .review {
    grid-template-columns: minmax(0, 1fr);
  }
  .review__publish {
    position: static;
  }
}
</style>
