<template>
  <div class="markdown-body" v-html="rendered" />
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  content: { type: String, default: '' },
  placeholder: { type: String, default: 'Pending...' },
})

const rendered = computed(() => {
  const src = props.content?.trim()
  if (!src) return `<p class="placeholder">${props.placeholder}</p>`
  return DOMPurify.sanitize(marked.parse(src))
})
</script>

<style scoped>
.markdown-body {
  font-size: 0.92rem;
  line-height: 1.65;
  color: var(--text);
}

.markdown-body :deep(.placeholder) {
  color: var(--text-faint);
  font-style: italic;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-family: var(--font-display);
  margin: 1.4rem 0 0.6rem;
  line-height: 1.3;
}

.markdown-body :deep(h1) {
  font-size: 1.4rem;
  margin-top: 0;
}

.markdown-body :deep(h2) {
  font-size: 1.15rem;
  color: var(--accent-2);
}

.markdown-body :deep(h3) {
  font-size: 1rem;
}

.markdown-body :deep(p) {
  margin: 0.7rem 0;
  color: var(--text-muted);
}

.markdown-body :deep(strong) {
  color: var(--text);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.6rem 0;
  padding-left: 1.3rem;
  color: var(--text-muted);
}

.markdown-body :deep(li) {
  margin: 0.3rem 0;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--accent);
  margin: 0.8rem 0;
  padding: 0.2rem 0 0.2rem 1rem;
  color: var(--text-muted);
  background: var(--accent-soft);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.markdown-body :deep(code) {
  font-family: var(--font-mono);
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.1rem 0.35rem;
  font-size: 0.85em;
  color: var(--accent-2);
}

.markdown-body :deep(pre) {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.9rem;
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  border: none;
  background: none;
  padding: 0;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.3rem 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8rem 0;
  font-size: 0.85rem;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border);
  padding: 0.5rem 0.7rem;
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--surface-2);
  color: var(--text);
}
</style>
