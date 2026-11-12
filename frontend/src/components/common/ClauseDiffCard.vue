<template>
  <article class="clause" :class="[`clause--${change.severity}`, { 'clause--compact': compact }]">
    <div class="clause__marks">
      <span class="clause-mark">{{ change.clause_label_old || '—' }}</span>
      <span class="clause__arrow">→</span>
      <span class="clause-mark">{{ change.clause_label_new || '—' }}</span>
    </div>

    <div class="clause__text">
      <div class="clause__col clause__col--old">
        <div class="label">原条文</div>
        <p class="clause__body serif">{{ change.old_text || '（原版本无此条）' }}</p>
      </div>
      <div class="clause__col clause__col--new">
        <div class="label">新条文</div>
        <p class="clause__body serif">{{ change.new_text || '（本版本已删除）' }}</p>
      </div>
    </div>

    <footer class="clause__foot">
      <div class="clause__tags">
        <SeverityTag :severity="change.severity" />
        <span class="clause__type">{{ change.change_type_label }}</span>
        <span class="clause__metric num">相似度 {{ change.similarity.toFixed(3) }}</span>
        <span class="clause__metric num">编辑幅度 {{ change.edit_ratio.toFixed(3) }}</span>
        <span v-if="change.confirmed" class="clause__confirmed">已确认</span>
        <span v-if="change.published" class="clause__confirmed clause__confirmed--published">已发布</span>
      </div>
      <p class="clause__reason">{{ change.reason }}</p>
      <div v-if="chips.length" class="clause__keywords">
        <span v-for="chip in chips" :key="chip" class="chip">{{ chip }}</span>
      </div>
      <p v-if="change.impact_note" class="clause__impact">
        <span class="label">影响标注</span>
        <span class="clause__impact-text">{{ change.impact_note }}</span>
        <span v-if="change.impact_industries.length" class="clause__industries">
          {{ change.impact_industries.map((item) => INDUSTRY_LABELS[item]).join(' · ') }}
        </span>
      </p>
      <slot name="actions" />
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { INDUSTRY_LABELS } from '../../constants/enums'
import type { ChangeItem } from '../../types/domain'
import { keywordChips } from '../../utils/format'
import SeverityTag from './SeverityTag.vue'

const props = withDefaults(defineProps<{ change: ChangeItem; compact?: boolean }>(), { compact: false })
const chips = computed(() => keywordChips(props.change.keywords ?? []))
</script>

<style scoped>
.clause {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr);
  gap: 18px;
  padding: 16px 0 18px;
  border-top: 1px solid var(--rule-soft);
  position: relative;
}
.clause--major::before {
  content: '';
  position: absolute;
  left: -14px;
  top: 18px;
  bottom: 18px;
  width: 2px;
  background: var(--seal);
}
.clause__marks {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
  padding-top: 3px;
}
.clause__arrow {
  color: var(--rule);
  font-size: 11px;
}
.clause__text {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
}
.clause__col {
  padding: 10px 12px;
  background: var(--paper-2);
  border: 1px solid var(--rule-soft);
}
.clause__col--old {
  color: var(--ink-soft);
}
.clause__col--new {
  background: color-mix(in oklch, var(--paper-3) 55%, var(--paper-2));
  border-color: var(--rule);
}
.clause__body {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.85;
  text-indent: 0;
  word-break: break-word;
}
.clause__foot {
  grid-column: 2;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.clause__tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  font-size: 10.5px;
  color: var(--ink-soft);
}
.clause__type {
  letter-spacing: 0.08em;
}
.clause__metric {
  color: var(--ink-faint);
  font-size: 10px;
}
.clause__confirmed {
  color: var(--indigo);
  border-bottom: 1px solid var(--indigo);
  font-size: 10px;
}
.clause__confirmed--published {
  color: var(--moss);
  border-bottom-color: var(--moss);
}
.clause__reason {
  font-size: 11.5px;
  color: var(--ink-soft);
  line-height: 1.7;
}
.clause__keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.clause__impact {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: baseline;
  font-size: 11.5px;
  border-left: 1px solid var(--seal);
  padding-left: 9px;
}
.clause__impact-text {
  color: var(--ink);
}
.clause__industries {
  color: var(--seal);
  font-size: 10px;
  letter-spacing: 0.08em;
}
.clause--compact {
  grid-template-columns: 76px minmax(0, 1fr);
}
@media (max-width: 900px) {
  .clause {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }
  .clause__foot {
    grid-column: 1;
  }
  .clause__text {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
