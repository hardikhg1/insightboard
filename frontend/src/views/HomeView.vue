<template>
  <section class="container section">
    <div class="home-header">
      <div>
        <h1 class="page-title">Your Datasets</h1>
        <p class="page-subtitle">
          Upload a CSV file and explore it with interactive charts and filters.
        </p>
      </div>
      <RouterLink to="/upload" class="btn-primary">
        + Upload CSV
      </RouterLink>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-grid">
      <div v-for="n in 4" :key="n" class="skeleton-card card"></div>
    </div>

    <!-- Error state with retry -->
    <div v-else-if="error" class="error-state card">
      <p class="error-state-icon">⚠️</p>
      <p class="error-state-title">Could not load datasets</p>
      <p class="error-state-body">{{ error }}</p>
      <button class="btn-secondary" style="margin-top:var(--space-5)" @click="loadDatasets">
        Try again
      </button>
    </div>

    <!-- Empty state -->
    <div v-else-if="datasets.length === 0" class="empty-state card">
      <p class="empty-icon">📂</p>
      <p class="empty-title">No datasets yet</p>
      <p class="empty-text">Upload a CSV file to get started.</p>
      <RouterLink to="/upload" class="btn-primary" style="margin-top: var(--space-5)">
        Upload your first CSV
      </RouterLink>
    </div>

    <!-- Dataset grid -->
    <TransitionGroup v-else name="card-list" tag="div" class="dataset-grid">
      <RouterLink
        v-for="ds in datasets"
        :key="ds.id"
        :to="`/datasets/${ds.id}`"
        class="dataset-card card"
      >
        <!-- Coloured accent bar at top of card -->
        <div class="ds-accent-bar"></div>
        <div class="ds-icon">📊</div>
        <h2 class="ds-name">{{ ds.name }}</h2>
        <p class="ds-file">{{ ds.original_filename }}</p>
        <div class="ds-stats">
          <span class="badge badge-number">{{ ds.row_count.toLocaleString() }} rows</span>
          <span class="badge badge-text">{{ ds.column_count }} cols</span>
        </div>
        <p class="ds-date">{{ formatDate(ds.uploaded_at) }}</p>
        <div class="ds-arrow">→</div>
      </RouterLink>
    </TransitionGroup>

  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/axios'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const { success: showSuccess } = useToast()

const datasets = ref([])
const loading  = ref(true)
const error    = ref(null)

async function loadDatasets() {
  loading.value = true
  error.value   = null
  try {
    const response = await api.get('/datasets/')
    datasets.value = response.data
  } catch {
    error.value = 'Is the Django server running on port 8000?'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // If we came back from a delete action, show a toast
  if (route.query.deleted) {
    showSuccess(`Dataset deleted successfully.`)
  }
  loadDatasets()
})

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric'
  })
}
</script>

<style scoped>
.section { padding-block: var(--space-10); }

/* Header row */
.home-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-5);
  margin-bottom: var(--space-8);
}

/* ── Skeleton loading ── */
.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-5);
}
.skeleton-card {
  height: 180px;
  background: linear-gradient(
    90deg,
    var(--color-surface) 25%,
    var(--color-surface-2) 50%,
    var(--color-surface) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Error state ── */
.error-state {
  text-align: center;
  padding: var(--space-10);
  max-width: 400px;
}
.error-state-icon  { font-size: 2.5rem; margin-bottom: var(--space-3); }
.error-state-title { font-size: 1.1rem; font-weight: 600; color: var(--color-error); }
.error-state-body  { color: var(--color-text-muted); font-size: 0.9rem; margin-top: var(--space-2); }

/* ── Empty state ── */
.empty-state {
  text-align: center;
  padding: var(--space-12);
}
.empty-icon  { font-size: 3rem; margin-bottom: var(--space-4); }
.empty-title { font-size: 1.2rem; font-weight: 600; margin-bottom: var(--space-2); }
.empty-text  { color: var(--color-text-muted); }

/* ── Dataset grid ── */
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
  position: relative;
  overflow: hidden;
  transition: transform var(--transition-base), box-shadow var(--transition-base),
              border-color var(--transition-base);
}
.dataset-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-glow);
  border-color: var(--accent-from);
}
.dataset-card:hover .ds-arrow { opacity: 1; transform: translateX(0); }

/* Gradient accent bar */
.ds-accent-bar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--accent-gradient);
  opacity: 0;
  transition: opacity var(--transition-base);
}
.dataset-card:hover .ds-accent-bar { opacity: 1; }

.ds-icon  { font-size: 2rem; }
.ds-name  { font-size: 1.05rem; font-weight: 700; }
.ds-file  { font-size: 0.8rem; color: var(--color-text-muted); }
.ds-stats { display: flex; gap: var(--space-2); flex-wrap: wrap; }
.ds-date  { font-size: 0.78rem; color: var(--color-text-muted); margin-top: auto; }

.ds-arrow {
  position: absolute;
  bottom: var(--space-4);
  right: var(--space-5);
  font-size: 1rem;
  color: var(--accent-from);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity var(--transition-base), transform var(--transition-base);
}

/* TransitionGroup animations for the card list */
.card-list-enter-from { opacity: 0; transform: translateY(12px); }
.card-list-enter-active { transition: opacity 300ms ease, transform 300ms ease; }
.card-list-leave-to  { opacity: 0; transform: scale(0.96); }
.card-list-leave-active { transition: opacity 200ms ease, transform 200ms ease; }

/* ── Responsive ── */
@media (max-width: 600px) {
  .home-header { flex-direction: column; }
  .dataset-grid { grid-template-columns: 1fr; }
}
</style>
