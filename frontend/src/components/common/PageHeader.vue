<template>
  <header class="page-header rise">
    <div class="page-header__main">
      <div class="eyebrow">{{ eyebrow }}</div>
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="description" class="page-header__desc">{{ description }}</p>
    </div>
    <div class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{ eyebrow: string; title: string; description?: string }>()
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--rule);
  margin-bottom: 22px;
}
.page-header__title {
  font-family: var(--serif);
  font-size: clamp(21px, 2.3vw, 29px);
  font-weight: 600;
  line-height: 1.18;
  margin-top: 6px;
  letter-spacing: 0.01em;
}
.page-header__desc {
  margin-top: 7px;
  max-width: 62ch;
  font-size: 12px;
  color: var(--ink-soft);
  line-height: 1.7;
}
.page-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  padding-bottom: 3px;
}
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
