<template>
  <div>
    <div
      ref="zoneEl"
      class="dropzone"
      :class="{ 'is-dragging': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
      @click="inputEl?.click()"
    >
      <input
        ref="inputEl"
        type="file"
        :accept="accept"
        multiple
        hidden
        @change="onChange"
      />
      <svg class="dz-icon" width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path
          d="M12 16V4M12 4L7 9M12 4l5 5M5 20h14"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <div class="dz-text">
        <strong>{{ label }}</strong>
        <span>Drag &amp; drop, or click to browse</span>
      </div>
    </div>

    <transition-group
      v-if="files.length"
      name="file-list"
      tag="ul"
      class="file-list"
    >
      <li v-for="(file, i) in files" :key="file.name + file.size" class="file-item">
        <span class="file-name">{{ file.name }}</span>
        <span class="file-size">{{ formatSize(file.size) }}</span>
        <button type="button" class="file-remove" @click.stop="removeFile(i)" aria-label="Remove file">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
          </svg>
        </button>
      </li>
    </transition-group>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { animate, stagger } from 'animejs'

const props = defineProps({
  label: { type: String, required: true },
  accept: { type: String, default: '' },
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const zoneEl = ref(null)
const inputEl = ref(null)
const isDragging = ref(false)
const files = ref([...props.modelValue])

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function addFiles(list) {
  const incoming = Array.from(list)
  if (!incoming.length) return
  files.value = [...files.value, ...incoming]
  emit('update:modelValue', files.value)
  nextTick(() => {
    animate('.file-item', {
      opacity: [0, 1],
      translateY: [-6, 0],
      delay: stagger(40),
      duration: 260,
      easing: 'easeOutQuad',
    })
  })
}

function onDrop(e) {
  isDragging.value = false
  addFiles(e.dataTransfer.files)
}

function onChange(e) {
  addFiles(e.target.files)
  e.target.value = ''
}

function removeFile(i) {
  files.value = files.value.filter((_, idx) => idx !== i)
  emit('update:modelValue', files.value)
}

watch(isDragging, (dragging) => {
  if (!zoneEl.value) return
  animate(zoneEl.value, {
    scale: dragging ? 1.015 : 1,
    duration: 180,
    easing: 'easeOutQuad',
  })
})
</script>

<style scoped>
.dropzone {
  border: 1.5px dashed var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--bg-soft);
  padding: 1.1rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.dropzone:hover {
  border-color: var(--accent);
  background: rgba(139, 123, 255, 0.05);
}

.dropzone.is-dragging {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.dz-icon {
  color: var(--accent);
  flex-shrink: 0;
}

.dz-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.dz-text strong {
  font-size: 0.88rem;
  color: var(--text);
}

.dz-text span {
  font-size: 0.76rem;
  color: var(--text-faint);
}

.file-list {
  list-style: none;
  margin: 0.6rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.4rem 0.6rem;
  font-size: 0.78rem;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text);
}

.file-size {
  color: var(--text-faint);
  font-family: var(--font-mono);
  font-size: 0.7rem;
}

.file-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--text-faint);
  cursor: pointer;
}

.file-remove:hover {
  background: var(--danger-soft);
  color: var(--danger);
}

.file-list-move {
  transition: transform 0.2s ease;
}
</style>
