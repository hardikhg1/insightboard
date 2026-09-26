<template>
  <section class="container section">
    <h1 class="page-title">Your Datasets</h1>
    <p class="page-subtitle">
      Upload a CSV file and explore it with interactive charts and filters.
    </p>

    <!-- Loading state -->
    <div v-if="loading" class="spinner"></div>

    <!-- Error state -->
    <div v-else-if="error" class="error-box">{{ error }}</div>

    <!-- Empty state -->
    <div v-else-if="datasets.length === 0" class="empty-state card">
      <p class="empty-icon">📂</p>
      <p class="empty-title">No datasets yet</p>
      <p class="empty-text">Upload a CSV file to get started.</p>
      <RouterLink to="/upload" class="btn-primary" style="margin-top: var(--space-5)">
        Upload CSV
      </RouterLink>
    </div>

    <!-- Dataset grid -->
    <div v-else class="dataset-grid">
      <RouterLink
        v-for="ds in datasets"
        :key="ds.id"
        :to="`/datasets/${ds.id}`"
        class="dataset-card card"
      >
        <div class="ds-icon">📊</div>
        <h2 class="ds-name">{{ ds.name }}</h2>
        <p class="ds-file">{{ ds.original_filename }}</p>
        <div class="ds-stats">
          <span class="badge badge-number">{{ ds.row_count }} rows</span>
          <span class="badge badge-text">{{ ds.column_count }} cols</span>
        </div>
        <p class="ds-date">{{ formatDate(ds.uploaded_at) }}</p>
      </RouterLink>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/axios'

/*
  ref() creates a reactive variable. When it changes, Vue automatically
  re-renders any part of the template that uses it.
*/
const datasets = ref([])
const loading  = ref(true)
const error    = ref(null)

/*
  onMounted() runs once after the component is inserted into the DOM.
  It's the right place to fetch initial data.
*/
onMounted(async () => {
  try {
    const response = await api.get('/datasets/')
    datasets.value = response.data
  } catch (err) {
    error.value = 'Could not load datasets. Is the backend running?'
  } finally {
    loading.value = false
  }
})

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric'
  })
}
</script>

<style scoped>
.section {
  padding-block: var(--space-10);
}

.empty-state {
  text-align: center;
  padding: var(--space-12);
}

.empty-icon  { font-size: 3rem; margin-bottom: var(--space-4); }
.empty-title { font-size: 1.2rem; font-weight: 600; margin-bottom: var(--space-2); }
.empty-text  { color: var(--color-text-muted); }

.dataset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-5);
}

.dataset-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  text-decoration: none;
  color: var(--color-text);
  cursor: pointer;
  transition: transform var(--transition-base), box-shadow var(--transition-base),
              border-color var(--transition-base);
}

.dataset-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-glow);
  border-color: var(--accent-from);
}

.ds-icon  { font-size: 2rem; }
.ds-name  { font-size: 1.1rem; font-weight: 700; }
.ds-file  { font-size: 0.8rem; color: var(--color-text-muted); }
.ds-stats { display: flex; gap: var(--space-2); flex-wrap: wrap; }
.ds-date  { font-size: 0.78rem; color: var(--color-text-muted); margin-top: auto; }
</style>
