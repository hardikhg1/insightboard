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
          <p>Drag & drop a CSV here, or <strong>click to browse</strong></p>
          <p class="drop-hint">Only .csv files are supported</p>
        </div>
        <div v-else class="drop-content">
          <span class="drop-icon">📄</span>
          <p class="file-name">{{ file.name }}</p>
          <p class="drop-hint">{{ (file.size / 1024).toFixed(1) }} KB — click to change</p>
        </div>
      </div>

      <!-- Submit button -->
      <button
        class="btn-primary"
        style="margin-top: var(--space-5); width: 100%; justify-content: center;"
        :disabled="!file || uploading"
        @click="upload"
      >
        <span v-if="uploading">Uploading…</span>
        <span v-else>Upload & Analyse</span>
      </button>

      <!-- Feedback messages -->
      <div v-if="error"   class="error-box"   style="margin-top:var(--space-4)">{{ error }}</div>
      <div v-if="success" class="success-box" style="margin-top:var(--space-4)">
        ✅ {{ success }}
        <RouterLink :to="`/datasets/${uploadedId}`" class="btn-secondary" style="margin-top:var(--space-3); display:inline-flex;">
          View Dataset →
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/axios'

const file       = ref(null)   // the File object selected by the user
const uploading  = ref(false)
const error      = ref(null)
const success    = ref(null)
const uploadedId = ref(null)
const isDragging = ref(false)

function onFileChange(e) {
  file.value  = e.target.files[0] || null
  error.value = null
  success.value = null
}

function onDrop(e) {
  isDragging.value = false
  const dropped = e.dataTransfer.files[0]
  if (dropped && dropped.name.endsWith('.csv')) {
    file.value = dropped
  } else {
    error.value = 'Please drop a .csv file.'
  }
}

async function upload() {
  if (!file.value) return

  error.value   = null
  success.value = null
  uploading.value = true

  try {
    /*
      FormData is how you send a file via HTTP in JavaScript.
      The key name 'file' must match what the Django view reads:
        request.FILES.get('file')
    */
    const form = new FormData()
    form.append('file', file.value)

    const response = await api.post('/datasets/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    uploadedId.value = response.data.id
    success.value = `"${response.data.name}" uploaded — ${response.data.row_count} rows, ${response.data.column_count} columns.`
    file.value = null
  } catch (err) {
    error.value = err.response?.data?.error || 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.section { padding-block: var(--space-10); }

.upload-card {
  max-width: 560px;
}

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
</style>
