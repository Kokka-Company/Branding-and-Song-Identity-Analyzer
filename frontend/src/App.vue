<template>
  <div class="app-shell">
    <header ref="headerEl" class="hero">
      <div class="hero-inner">
        <span class="hero-kicker">Artist Intelligence</span>
        <h1 class="hero-title">Brand &amp; Sonic Identity Analyzer</h1>
        <p class="hero-sub">
          Upload audio and visual media to generate a seven-stage brand intelligence
          analysis — sonic identity, persona, cultural positioning, and a synthesized
          final dossier.
        </p>
      </div>
    </header>

    <main class="layout">
      <AnalyzerForm :running="running" @submit="onRunAnalysis" />

      <section class="results-col">
        <ProgressStepper :stages="stages" :message="message" :error="error" />
        <ResultsPanel
          :report="state.report"
          :alignment="state.alignment"
          :music-narr="state.music_narr"
          :persona-narr="state.persona_narr"
          :audio="state.audio"
          :music-json="state.music_json"
          :persona-json="state.persona_json"
          :downloads="state.downloads"
          :artist-slug="state.artist_slug"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { animate, stagger } from 'animejs'
import AnalyzerForm from './components/AnalyzerForm.vue'
import ProgressStepper from './components/ProgressStepper.vue'
import ResultsPanel from './components/ResultsPanel.vue'
import { runAnalysis } from './api.js'

const STAGE_DEFS = [
  { key: 'audio', label: 'Audio Features' },
  { key: 'music_analysis', label: 'Music Analysis' },
  { key: 'persona_analysis', label: 'Persona Analysis' },
  { key: 'music_narrative', label: 'Music Narrative' },
  { key: 'persona_narrative', label: 'Persona Narrative' },
  { key: 'brand_alignment', label: 'Brand Alignment' },
  { key: 'final_report', label: 'Final Report' },
]

const headerEl = ref(null)
const running = ref(false)
const message = ref('Fill in the form and click "Run analysis" to begin.')
const error = ref(null)
const stages = ref(STAGE_DEFS.map((s) => ({ ...s, status: 'pending' })))

const state = reactive({
  artist_slug: '',
  audio: null,
  music_json: null,
  persona_json: null,
  music_narr: '',
  persona_narr: '',
  alignment: '',
  report: '',
  downloads: [],
})

function resetState() {
  stages.value = STAGE_DEFS.map((s) => ({ ...s, status: 'pending' }))
  error.value = null
  message.value = 'Starting pipeline...'
  Object.assign(state, {
    artist_slug: '',
    audio: null,
    music_json: null,
    persona_json: null,
    music_narr: '',
    persona_narr: '',
    alignment: '',
    report: '',
    downloads: [],
  })
}

async function onRunAnalysis(formData) {
  if (running.value) return
  running.value = true
  resetState()

  try {
    await runAnalysis(formData, (frame) => {
      stages.value = frame.stages
      message.value = frame.message
      error.value = frame.error
      Object.assign(state, {
        artist_slug: frame.artist_slug,
        audio: frame.audio,
        music_json: frame.music_json,
        persona_json: frame.persona_json,
        music_narr: frame.music_narr,
        persona_narr: frame.persona_narr,
        alignment: frame.alignment,
        report: frame.report,
        downloads: frame.downloads,
      })
    })
  } catch (e) {
    error.value = e.message || 'The analysis run failed unexpectedly.'
    message.value = error.value
  } finally {
    running.value = false
  }
}

onMounted(() => {
  animate(headerEl.value, {
    opacity: [0, 1],
    translateY: [-14, 0],
    duration: 600,
    easing: 'easeOutQuad',
  })
  animate('.hero-kicker, .hero-title, .hero-sub', {
    opacity: [0, 1],
    translateY: [10, 0],
    delay: stagger(90),
    duration: 500,
    easing: 'easeOutQuad',
  })
})
</script>

<style scoped>
.app-shell {
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 1.5rem 4rem;
}

.hero {
  padding: 3.2rem 0 2.4rem;
}

.hero-inner {
  max-width: 720px;
}

.hero-kicker {
  display: inline-block;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-2);
  margin-bottom: 0.8rem;
}

.hero-title {
  font-size: clamp(1.8rem, 3.4vw, 2.6rem);
  background: var(--gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 0.9rem;
}

.hero-sub {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--text-muted);
  max-width: 560px;
}

.layout {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 1.6rem;
  align-items: start;
}

.results-col {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  min-width: 0;
}

@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
