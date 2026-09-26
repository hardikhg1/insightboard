<template>
  <section class="container section">
    <h1 class="page-title">Upload a CSV</h1>
    <p class="page-subtitle">
      Choose a <code>.csv</code> file — we'll parse it, detect column types,
      and store it for exploration.
    </p>

    <div class="upload-card card">
      <!-- Drop zone -->
      <div
        class="drop-zone"
        :class="{ 'drop-zone--active': isDragging, 'drop-zone--selected': file }"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="onDrop"
        @click="$refs.fileInput.click()"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".csv"
          style="display:none"
          @change="onFileChange"
        />
        <div v-if="!file" class="drop-content">
          <span class="drop-icon">☁️</span>
          <p>Drag &amp; drop a CSV here, or <strong>click to browse</strong></p>
          <p class="drop-hint">Only .csv files are supported</p>
        </div>
        <div v-else class="drop-content">
          <span class="drop-icon">📄</span>
          <p class="file-name">{{ file.name }}</p>
          <p class="drop-hint">{{ (file.size / 1024).toFixed(1) }} KB — click to change</p>
        </div>
      </div>

      <!-- Upload progress bar (visible while uploading) -->
      <div v-if="uploading" class="progress-bar-wrap">
        <div class="progress-bar"></div>
      </div>

      <!-- Submit button -->
      <button
        class="btn-primary upload-btn"
        :disabled="!file || uploading"
        @click="upload"
      >
        <span v-if="uploading" class="btn-spinner"></span>
        <span>{{ uploading ? 'Uploading…' : 'Upload &amp; Analyse' }}</span>
      </button>

      <!-- Inline error (for upload-specific errors) -->
      <div v-if="error" class="error-box" style="margin-top:var(--space-4)">
        {{ error }}
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/axios'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { success: showSuccess, error: showError } = useToast()

const file       = ref(null)
const uploading  = ref(false)
const error      = ref(null)
const isDragging = ref(false)

function onFileChange(e) {
  file.value  = e.target.files[0] || null
  error.value = null
}

function onDrop(e) {
  isDragging.value = false
  const dropped = e.dataTransfer.files[0]
  if (dropped && dropped.name.endsWith('.csv')) {
    file.value  = dropped
    error.value = null
  } else {
    error.value = 'Please drop a .csv file.'
  }
}

async function upload() {
  if (!file.value) return
  error.value     = null
  uploading.value = true

  try {
    const form = new FormData()
    form.append('file', file.value)

    const response = await api.post('/datasets/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    const ds = response.data
    // Show a success toast — it will auto-dismiss in 3.5 s
    showSuccess(`"${ds.name}" uploaded — ${ds.row_count} rows, ${ds.column_count} columns.`)
    file.value = null

    // Auto-navigate to the new dataset's detail page
    router.push(`/datasets/${ds.id}`)

  } catch (err) {
    // The global interceptor already handles 500/network errors.
    // Handle upload-specific errors (400) inline in the card.
    const msg = err.response?.data?.error
    if (err.response?.status === 400 && msg) {
      error.value = msg
    } else if (err.response?.status !== 500 && err.response) {
      error.value = 'Upload failed. Please check the file and try again.'
      showError(error.value)
    }
    // If err.response is undefined (network error), the interceptor handles it
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.section { padding-block: var(--space-10); }

.upload-card { max-width: 560px; }

/* Drop zone */
.drop-zone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-12) var(--space-6);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--transition-base), background var(--transition-base);
}
.drop-zone:hover,
.drop-zone--active {
  border-color: var(--accent-from);
  background: rgba(99, 102, 241, 0.05);
}
.drop-zone--selected {
  border-color: var(--color-success);
  background: rgba(16, 185, 129, 0.05);
}
.drop-content { display: flex; flex-direction: column; align-items: center; gap: var(--space-3); }
.drop-icon    { font-size: 2.5rem; }
.drop-hint    { font-size: 0.8rem; color: var(--color-text-muted); }
.file-name    { font-weight: 600; color: var(--color-success); }

/* Progress bar */
.progress-bar-wrap {
  margin-top: var(--space-4);
  height: 4px;
  background: var(--color-border);
  border-radius: 999px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: var(--accent-gradient);
  border-radius: 999px;
  animation: progress-slide 1.2s ease-in-out infinite;
  width: 40%;
}
@keyframes progress-slide {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(300%); }
}

/* Upload button */
.upload-btn {
  margin-top: var(--space-5);
  width: 100%;
  justify-content: center;
  gap: var(--space-3);
}

/* Spinner inside button */
.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Responsive */
@media (max-width: 600px) {
  .upload-card { max-width: 100%; }
  .drop-zone { padding: var(--space-8) var(--space-4); }
}
</style>
