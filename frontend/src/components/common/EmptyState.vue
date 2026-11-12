<template>
  <div class="empty rise">
    <div class="empty__rule"></div>
    <div class="empty__mark">空</div>
    <div>
      <div class="empty__title">{{ title }}</div>
      <p class="empty__hint">{{ hint }}</p>
      <button v-if="actionText" class="btn btn--quiet empty__action" @click="$emit('action')">
        {{ actionText }} →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; hint: string; actionText?: string }>()
defineEmits<{ action: [] }>()
</script>

<style scoped>
.empty {
  display: grid;
  grid-template-columns: 3px auto minmax(0, 1fr);
  gap: 16px;
  align-items: start;
  padding: 22px 4px 26px;
  border-bottom: 1px solid var(--rule-soft);
}
.empty__rule {
  align-self: stretch;
  border-left: 1px solid var(--rule);
}
.empty__mark {
  font-family: var(--serif);
  font-size: 34px;
  color: var(--paper-4);
  line-height: 1;
}
.empty__title {
  font-family: var(--serif);
  font-size: 14px;
  margin-bottom: 5px;
}
.empty__hint {
  font-size: 12px;
  color: var(--ink-soft);
  max-width: 60ch;
  line-height: 1.7;
}
.empty__action {
  margin-top: 10px;
  padding-left: 0;
  font-size: 11.5px;
}
</style>
