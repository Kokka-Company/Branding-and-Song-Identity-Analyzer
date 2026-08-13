<template>
  <div class="card stepper-card">
    <ol class="stepper">
      <li
        v-for="(stage, i) in stages"
        :key="stage.key"
        class="step"
        :class="`is-${stage.status}`"
      >
        <div class="step-dot-wrap">
          <span class="step-dot" :ref="(el) => setDotRef(el, i)">
            <svg v-if="stage.status === 'done'" width="10" height="10" viewBox="0 0 12 12" fill="none">
              <path d="M1.5 6.5l3 3 6-7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <svg v-else-if="stage.status === 'error'" width="10" height="10" viewBox="0 0 12 12" fill="none">
              <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </span>
          <span v-if="i < stages.length - 1" class="step-line">
            <span class="step-line-fill" :ref="(el) => setLineRef(el, i)" />
          </span>
        </div>
        <span class="step-label">{{ stage.label }}</span>
      </li>
    </ol>
    <p class="stepper-message" :class="{ 'is-error': !!error }">{{ error || message }}</p>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { animate } from 'animejs'

const props = defineProps({
  stages: { type: Array, required: true },
  message: { type: String, default: '' },
  error: { type: String, default: null },
})

const dotRefs = []
const lineRefs = []
function setDotRef(el, i) {
  if (el) dotRefs[i] = el
}
function setLineRef(el, i) {
  if (el) lineRefs[i] = el
}

watch(
  () => props.stages.map((s) => s.status),
  (statuses, prev = []) => {
    statuses.forEach((status, i) => {
      if (status === prev[i]) return
      const dot = dotRefs[i]
      if (dot) {
        if (status === 'running') {
          animate(dot, { scale: [1, 1.25, 1], duration: 500, easing: 'easeOutQuad' })
        } else if (status === 'done') {
          animate(dot, { scale: [1, 1.35, 1], duration: 420, easing: 'easeOutBack' })
        } else if (status === 'error') {
          animate(dot, { translateX: [0, -4, 4, -3, 3, 0], duration: 400, easing: 'easeInOutSine' })
        }
      }
      const line = lineRefs[i]
      if (line && status === 'done') {
        animate(line, { width: ['0%', '100%'], duration: 500, easing: 'easeInOutQuad' })
      }
    })
  },
  { deep: true },
)
</script>

<style scoped>
.stepper-card {
  padding: 1.4rem 1.6rem 1.2rem;
}

.stepper {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  gap: 0.55rem;
  position: relative;
}

.step-dot-wrap {
  display: flex;
  align-items: center;
  width: 100%;
}

.step-dot {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid var(--border-strong);
  background: var(--bg-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: transparent;
  transition: border-color 0.2s ease, background 0.2s ease, color 0.2s ease;
  z-index: 1;
  margin-left: -11px;
}

.step:first-child .step-dot {
  margin-left: 0;
}

.step.is-running .step-dot {
  border-color: var(--accent);
  background: var(--accent-soft);
  box-shadow: 0 0 0 4px var(--accent-soft);
}

.step.is-done .step-dot {
  border-color: var(--success);
  background: var(--success);
  color: #06251a;
}

.step.is-error .step-dot {
  border-color: var(--danger);
  background: var(--danger);
  color: #2a0a0a;
}

.step.is-skipped .step-dot {
  border-color: var(--border);
  background: transparent;
  opacity: 0.5;
}

.step-line {
  flex: 1;
  height: 2px;
  background: var(--border);
  margin: 0 2px;
  overflow: hidden;
  border-radius: 2px;
}

.step-line-fill {
  display: block;
  height: 100%;
  width: 0%;
  background: var(--success);
}

.step-label {
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text-faint);
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  transition: color 0.2s ease;
  padding: 0 0.2rem;
}

.step.is-running .step-label,
.step.is-done .step-label {
  color: var(--text);
}

.step.is-error .step-label {
  color: var(--danger);
}

.stepper-message {
  margin-top: 1.1rem;
  padding-top: 0.9rem;
  border-top: 1px solid var(--border);
  font-size: 0.84rem;
  color: var(--text-muted);
}

.stepper-message.is-error {
  color: var(--danger);
}

@media (max-width: 720px) {
  .step-label {
    display: none;
  }
}
</style>
