<template>
  <form class="card form" @submit.prevent="onSubmit">
    <div class="form-section">
      <p class="section-title"><span class="idx">1</span> Identity</p>
      <label class="label" for="artist">Artist name</label>
      <input id="artist" v-model="artist" type="text" placeholder="e.g. m00nie" />
    </div>

    <div class="form-section">
      <p class="section-title"><span class="idx">2</span> Music inputs</p>

      <label class="label">Audio files</label>
      <FileDropzone v-model="audioFiles" label="MP3 / WAV / FLAC / M4A" accept="audio/*" />

      <label class="label" style="margin-top: 1rem">Lyrics <span class="opt">optional</span></label>
      <textarea
        v-model="lyrics"
        rows="5"
        placeholder="## Track 1 Title&#10;First-verse lyrics here...&#10;&#10;## Track 2 Title&#10;Second track lyrics..."
      />

      <label class="label" style="margin-top: 1rem">Metadata JSON <span class="opt">optional</span></label>
      <textarea
        v-model="metadata"
        rows="3"
        placeholder='{"label": "Independent", "monthly_listeners": 412000}'
      />

      <label class="label" style="margin-top: 1rem">Music notes <span class="opt">optional</span></label>
      <textarea v-model="musicNotes" rows="2" placeholder="Context for the music agent..." />
    </div>

    <div class="form-section">
      <p class="section-title"><span class="idx">3</span> Persona inputs</p>

      <label class="label">Images</label>
      <FileDropzone v-model="imageFiles" label="Press shots, covers, stills" accept="image/*" />

      <label class="label" style="margin-top: 1rem">Captions <span class="opt">one per line, in upload order</span></label>
      <textarea
        v-model="captions"
        rows="3"
        placeholder="Press shot 2024 album cycle&#10;EP cover art&#10;Instagram grid mid-2024"
      />

      <label class="label" style="margin-top: 1rem">Persona notes <span class="opt">optional</span></label>
      <textarea v-model="personaNotes" rows="2" />
    </div>

    <button ref="submitBtn" type="submit" class="btn btn-primary btn-submit" :disabled="running">
      <span v-if="!running">Run analysis</span>
      <span v-else class="running-label">
        <span class="spinner" />
        Analyzing...
      </span>
    </button>
  </form>
</template>

<script setup>
import { ref } from 'vue'
import { animate } from 'animejs'
import FileDropzone from './FileDropzone.vue'

const props = defineProps({
  running: { type: Boolean, default: false },
})
const emit = defineEmits(['submit'])

const artist = ref('')
const audioFiles = ref([])
const lyrics = ref('')
const metadata = ref('')
const musicNotes = ref('')
const imageFiles = ref([])
const captions = ref('')
const personaNotes = ref('')
const submitBtn = ref(null)

function onSubmit() {
  if (!artist.value.trim()) {
    animate(submitBtn.value, {
      translateX: [0, -6, 6, -4, 4, 0],
      duration: 380,
      easing: 'easeInOutSine',
    })
    return
  }

  const fd = new FormData()
  fd.append('artist', artist.value.trim())
  fd.append('lyrics', lyrics.value)
  fd.append('metadata', metadata.value)
  fd.append('music_notes', musicNotes.value)
  fd.append('persona_notes', personaNotes.value)
  fd.append('captions', captions.value)
  audioFiles.value.forEach((f) => fd.append('audio', f))
  imageFiles.value.forEach((f) => fd.append('images', f))

  emit('submit', fd)
}
</script>

<style scoped>
.form {
  padding: 1.6rem;
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.form-section {
  display: flex;
  flex-direction: column;
}

.form-section > .label:first-of-type {
  margin-top: 0.9rem;
}

.opt {
  text-transform: none;
  font-weight: 400;
  color: var(--text-faint);
  letter-spacing: 0;
}

.btn-submit {
  width: 100%;
  padding: 0.85rem;
  font-size: 0.95rem;
}

.running-label {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
}

.spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(10, 11, 15, 0.35);
  border-top-color: rgba(10, 11, 15, 0.85);
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
