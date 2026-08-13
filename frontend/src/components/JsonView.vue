<template>
  <div class="json-view">
    <p v-if="value === null || value === undefined" class="placeholder">{{ placeholder }}</p>
    <JsonNode v-else :value="value" :depth="0" />
  </div>
</template>

<script setup>
import JsonNode from './JsonNode.vue'

defineProps({
  value: { default: null },
  placeholder: { type: String, default: 'Pending...' },
})
</script>

<style scoped>
.json-view {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  line-height: 1.65;
}

.placeholder {
  color: var(--text-faint);
  font-style: italic;
  font-family: var(--font-body);
}
</style>
