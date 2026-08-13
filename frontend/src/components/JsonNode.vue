<template>
  <span v-if="value === null" class="jv-null">null</span>
  <span v-else-if="typeof value === 'boolean'" class="jv-bool">{{ value }}</span>
  <span v-else-if="typeof value === 'number'" class="jv-num">{{ value }}</span>
  <span v-else-if="typeof value === 'string'" class="jv-str">"{{ value }}"</span>

  <span v-else-if="Array.isArray(value)" class="jv-branch">
    <button class="jv-toggle" @click="open = !open">
      <span class="jv-chevron" :class="{ 'is-open': open }">▸</span>
      <span class="jv-bracket">[</span>
      <span v-if="!open" class="jv-summary">{{ value.length }} item{{ value.length === 1 ? '' : 's' }}</span>
      <span v-if="!open" class="jv-bracket">]</span>
    </button>
    <div v-if="open" class="jv-children">
      <div v-for="(item, i) in value" :key="i" class="jv-row">
        <span class="jv-key jv-key-idx">{{ i }}</span>
        <JsonNode :value="item" :depth="depth + 1" />
      </div>
    </div>
    <span v-if="open" class="jv-bracket jv-bracket-close">]</span>
  </span>

  <span v-else-if="typeof value === 'object'" class="jv-branch">
    <button class="jv-toggle" @click="open = !open">
      <span class="jv-chevron" :class="{ 'is-open': open }">▸</span>
      <span class="jv-bracket">{</span>
      <span v-if="!open" class="jv-summary">{{ Object.keys(value).length }} key{{ Object.keys(value).length === 1 ? '' : 's' }}</span>
      <span v-if="!open" class="jv-bracket">}</span>
    </button>
    <div v-if="open" class="jv-children">
      <div v-for="key in Object.keys(value)" :key="key" class="jv-row">
        <span class="jv-key">{{ key }}</span>
        <span class="jv-colon">:</span>
        <JsonNode :value="value[key]" :depth="depth + 1" />
      </div>
    </div>
    <span v-if="open" class="jv-bracket jv-bracket-close">}</span>
  </span>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  value: { default: null },
  depth: { type: Number, default: 0 },
})

const open = ref(props.depth < 1)
</script>

<style scoped>
.jv-null {
  color: var(--text-faint);
}
.jv-bool {
  color: var(--accent-2);
}
.jv-num {
  color: #f5b74f;
}
.jv-str {
  color: #3ddc97;
}

.jv-toggle {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 0;
  font-family: var(--font-mono);
  font-size: inherit;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.jv-chevron {
  display: inline-block;
  color: var(--text-faint);
  transition: transform 0.15s ease;
  font-size: 0.7em;
}

.jv-chevron.is-open {
  transform: rotate(90deg);
}

.jv-bracket {
  color: var(--text-faint);
}

.jv-summary {
  color: var(--text-faint);
  font-style: italic;
  margin: 0 0.2rem;
}

.jv-children {
  margin-left: 1.1rem;
  border-left: 1px solid var(--border);
  padding-left: 0.8rem;
}

.jv-row {
  padding: 0.08rem 0;
}

.jv-key {
  color: var(--accent);
}

.jv-key-idx {
  color: var(--text-faint);
}

.jv-colon {
  color: var(--text-faint);
  margin: 0 0.35rem 0 0.1rem;
}

.jv-bracket-close {
  display: block;
}
</style>
