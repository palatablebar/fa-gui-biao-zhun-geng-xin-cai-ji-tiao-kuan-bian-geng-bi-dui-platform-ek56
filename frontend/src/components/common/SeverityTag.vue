<template>
  <span class="severity" :class="`severity--${severity}`">
    <span class="severity__dot"></span>{{ label ?? SEVERITY_LABELS[severity] }}
  </span>
</template>

<script setup lang="ts">
import { SEVERITY_LABELS } from '../../constants/enums'
import type { Severity } from '../../types/domain'

defineProps<{ severity: Severity; label?: string }>()
</script>

<style scoped>
.severity {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  letter-spacing: 0.1em;
  padding: 2px 7px;
  border: 1px solid currentColor;
  font-family: var(--sans);
}
.severity__dot {
  width: 5px;
  height: 5px;
  background: currentColor;
  transform: rotate(45deg);
}
.severity--major {
  color: var(--seal);
}
.severity--general {
  color: var(--ochre);
}
.severity--editorial {
  color: var(--moss);
}
.severity--unparsed {
  color: var(--ink-faint);
}
</style>
