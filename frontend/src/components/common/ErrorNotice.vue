<template>
  <div v-if="message" class="error" role="alert">
    <span class="error__code">{{ error?.code ?? 'ERROR' }}</span>
    <div class="error__body">
      <div class="error__message">{{ message }}</div>
      <div v-if="error?.detail" class="error__detail">{{ error.detail }}</div>
    </div>
    <button v-if="retryable" class="btn btn--quiet error__retry" @click="$emit('retry')">重试</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiError } from '../../types/api'

const props = withDefaults(
  defineProps<{ error?: ApiError | null; fallback?: string; retryable?: boolean }>(),
  { retryable: true },
)
defineEmits<{ retry: [] }>()

const message = computed(() => props.error?.message ?? props.fallback ?? '')
</script>

<style scoped>
.error {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid var(--seal);
  border-left-width: 3px;
  background: color-mix(in oklch, var(--seal) 6%, var(--paper-2));
  padding: 10px 12px;
  margin-top: 12px;
}
.error__code {
  font-family: var(--sans);
  font-size: 9.5px;
  letter-spacing: 0.14em;
  color: var(--seal);
  border: 1px solid var(--seal);
  padding: 2px 5px;
  white-space: nowrap;
}
.error__body {
  flex: 1;
  min-width: 0;
}
.error__message {
  font-size: 12.5px;
}
.error__detail {
  font-size: 10.5px;
  color: var(--ink-faint);
  margin-top: 3px;
  word-break: break-word;
}
.error__retry {
  font-size: 11px;
  padding: 3px 8px;
}
</style>
