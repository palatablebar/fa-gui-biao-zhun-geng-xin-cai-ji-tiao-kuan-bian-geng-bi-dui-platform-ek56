<template>
  <span class="seal" :class="[`seal--${tone}`, `seal--${size}`]">{{ label }}</span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    tone?: 'seal' | 'ink' | 'moss' | 'indigo' | 'ochre'
    size?: 'sm' | 'md'
  }>(),
  { tone: 'ink', size: 'md' },
)
</script>

<style scoped>
.seal {
  display: inline-grid;
  place-items: center;
  font-family: var(--serif);
  letter-spacing: 0.14em;
  border: 1px solid currentColor;
  box-shadow: inset 0 0 0 1px var(--paper-2);
  transform: rotate(-3.2deg);
  white-space: nowrap;
  line-height: 1;
}
.seal--md {
  padding: 6px 9px;
  font-size: 11px;
  font-weight: 600;
}
.seal--sm {
  padding: 4px 6px;
  font-size: 9.5px;
}
.seal--seal {
  color: var(--seal);
  border-width: 2px;
}
.seal--ink {
  color: var(--ink-soft);
}
.seal--moss {
  color: var(--moss);
}
.seal--indigo {
  color: var(--indigo);
}
.seal--ochre {
  color: var(--ochre);
}
</style>
