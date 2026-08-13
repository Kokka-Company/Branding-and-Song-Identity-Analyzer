<template>
  <div class="card results">
    <div class="tabs" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: activeTab === tab.key }"
        role="tab"
        @click="selectTab(tab.key)"
      >
        {{ tab.label }}
        <span v-if="tab.badge" class="tab-badge" :class="`badge-${tab.badge}`" />
      </button>
    </div>

    <div ref="panelEl" class="tab-panel">
      <MarkdownView v-if="activeTab === 'report'" :content="report" placeholder="The final dossier will appear here once the last stage completes." />
      <MarkdownView v-else-if="activeTab === 'alignment'" :content="alignment" />
      <MarkdownView v-else-if="activeTab === 'music_narr'" :content="musicNarr" />
      <MarkdownView v-else-if="activeTab === 'persona_narr'" :content="personaNarr" />
      <JsonView v-else-if="activeTab === 'audio'" :value="audio" />
      <JsonView v-else-if="activeTab === 'music_json'" :value="musicJson" />
      <JsonView v-else-if="activeTab === 'persona_json'" :value="personaJson" />
    </div>

    <div v-if="downloads.length" class="downloads">
      <span class="downloads-label">Artifacts</span>
      <a
        v-for="file in downloads"
        :key="file"
        class="download-chip"
        :href="downloadUrl(artistSlug, file)"
        target="_blank"
        rel="noopener"
      >
        {{ file }}
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { animate } from 'animejs'
import MarkdownView from './MarkdownView.vue'
import JsonView from './JsonView.vue'
import { downloadUrl } from '../api.js'

const props = defineProps({
  report: { type: String, default: '' },
  alignment: { type: String, default: '' },
  musicNarr: { type: String, default: '' },
  personaNarr: { type: String, default: '' },
  audio: { default: null },
  musicJson: { default: null },
  personaJson: { default: null },
  downloads: { type: Array, default: () => [] },
  artistSlug: { type: String, default: '' },
})

const activeTab = ref('report')
const panelEl = ref(null)

const tabs = computed(() => [
  { key: 'report', label: 'Final Dossier', badge: props.report ? 'ready' : null },
  { key: 'alignment', label: 'Brand Alignment', badge: props.alignment ? 'ready' : null },
  { key: 'music_narr', label: 'Music Narrative', badge: props.musicNarr ? 'ready' : null },
  { key: 'persona_narr', label: 'Persona Narrative', badge: props.personaNarr ? 'ready' : null },
  { key: 'audio', label: 'Audio Features', badge: props.audio ? 'ready' : null },
  { key: 'music_json', label: 'Music Analysis JSON', badge: props.musicJson ? 'ready' : null },
  { key: 'persona_json', label: 'Persona Analysis JSON', badge: props.personaJson ? 'ready' : null },
])

function selectTab(key) {
  if (key === activeTab.value) return
  activeTab.value = key
  nextTick(() => {
    if (!panelEl.value) return
    animate(panelEl.value, {
      opacity: [0, 1],
      translateY: [8, 0],
      duration: 260,
      easing: 'easeOutQuad',
    })
  })
}
</script>

<style scoped>
.results {
  display: flex;
  flex-direction: column;
  min-height: 420px;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem;
  padding: 0.6rem 0.6rem 0;
  border-bottom: 1px solid var(--border);
}

.tab {
  position: relative;
  background: none;
  border: none;
  color: var(--text-faint);
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.6rem 0.85rem;
  cursor: pointer;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: color 0.15s ease, background 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.tab:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.03);
}

.tab.active {
  color: var(--text);
  background: var(--bg-soft);
}

.tab.active::after {
  content: '';
  position: absolute;
  left: 0.4rem;
  right: 0.4rem;
  bottom: -1px;
  height: 2px;
  background: var(--gradient);
  border-radius: 2px;
}

.tab-badge {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.badge-ready {
  background: var(--success);
  box-shadow: 0 0 0 3px var(--success-soft);
}

.tab-panel {
  padding: 1.5rem 1.7rem;
  overflow-y: auto;
  flex: 1;
  max-height: 560px;
}

.downloads {
  border-top: 1px solid var(--border);
  padding: 0.9rem 1.4rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.downloads-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
  margin-right: 0.3rem;
}

.download-chip {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--accent-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.3rem 0.7rem;
  transition: border-color 0.15s ease, color 0.15s ease;
}

.download-chip:hover {
  border-color: var(--accent-2);
  color: var(--text);
}
</style>
