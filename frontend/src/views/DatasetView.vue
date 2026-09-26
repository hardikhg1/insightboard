<template>
  <section class="container section">

    <!-- Loading -->
    <div v-if="loading" class="spinner"></div>

    <!-- Error -->
    <div v-else-if="error" class="error-box">{{ error }}</div>

    <!-- Content -->
    <template v-else-if="dataset">

      <!-- ── Page Header ────────────────────────────────────────── -->
      <div class="ds-header">
        <div>
          <h1 class="page-title">{{ dataset.name }}</h1>
          <p class="page-subtitle">{{ dataset.original_filename }}</p>
        </div>
        <div class="ds-meta-group">
          <div class="ds-meta-badges">
            <span class="badge badge-number">{{ dataset.row_count }} rows</span>
            <span class="badge badge-text">{{ dataset.column_count }} cols</span>
          </div>
          <button class="btn-secondary btn-delete" @click="confirmDelete">
            🗑 Delete
          </button>
        </div>
      </div>

      <!-- ── Column Info Strip ──────────────────────────────────── -->
      <div class="column-strip card">
        <p class="strip-label">Columns</p>
        <div class="column-pills">
          <span
            v-for="col in dataset.columns"
            :key="col.id"
            class="badge"
            :class="`badge-${col.data_type}`"
            :title="col.data_type"
          >
            {{ col.name }}
          </span>
        </div>
      </div>

      <!-- ── Data Table ─────────────────────────────────────────── -->
      <div class="section-heading">
        <h2 class="section-title">Data Table</h2>
        <p class="section-sub">Click any column header to sort. Use the filter bar to search rows.</p>
      </div>

      <DataTable
        :columns="dataset.columns"
        :dataset-id="dataset.id"
      />

      <!-- ── Charts placeholder (Step 9) ───────────────────────── -->
      <div class="section-heading" style="margin-top: var(--space-10)">
        <h2 class="section-title">Visualisations</h2>
        <p class="section-sub">📈 Chart.js charts will be added in Step 9.</p>
      </div>
      <div class="card chart-placeholder">
        <span class="chart-placeholder-icon">📊</span>
        <p>Charts coming in Step 9</p>
      </div>

    </template>

    <!-- ── Delete confirmation modal ────────────────────────────── -->
    <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
      <div class="modal card">
        <h2 class="modal-title">Delete dataset?</h2>
        <p class="modal-body">
          This will permanently delete <strong>{{ dataset?.name }}</strong>
          and all its rows and columns. This cannot be undone.
        </p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDeleteModal = false">Cancel</button>
          <button class="btn-delete-confirm" :disabled="deleting" @click="deleteDataset">
            {{ deleting ? 'Deleting…' : 'Yes, delete' }}
          </button>
        </div>
      </div>
    </div>

  </section>
</template>

<script setup>
/**
 * DatasetView — the dataset detail page.
 *
 * It fetches the dataset metadata (name, columns, row/col count) from
 * GET /api/datasets/<id>/ and passes columns + id down to <DataTable>.
 *
 * <DataTable> is responsible for its own rows API call — the parent
 * doesn't need to know about rows at all. This is a good example of
 * "separation of concerns" in Vue component design.
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/axios'
import DataTable from '@/components/DataTable.vue'

const route   = useRoute()
const router  = useRouter()

const dataset        = ref(null)
const loading        = ref(true)
const error          = ref(null)
const showDeleteModal = ref(false)
const deleting       = ref(false)

// Fetch dataset metadata on mount
onMounted(async () => {
  try {
    const response = await api.get(`/datasets/${route.params.id}/`)
    dataset.value = response.data
  } catch {
    error.value = 'Could not load dataset. It may have been deleted.'
  } finally {
    loading.value = false
  }
})

function confirmDelete() {
  showDeleteModal.value = true
}

async function deleteDataset() {
  deleting.value = true
  try {
    await api.delete(`/datasets/${route.params.id}/`)
    // Navigate back to the home page after successful delete
    router.push('/')
  } catch {
    showDeleteModal.value = false
    error.value = 'Delete failed. Please try again.'
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.section { padding-block: var(--space-10); }

/* ── Header ── */
.ds-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.ds-meta-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-3);
}

.ds-meta-badges { display: flex; gap: var(--space-2); }

.btn-delete {
  font-size: 0.8rem;
  color: var(--color-error);
  border-color: rgba(239, 68, 68, 0.3);
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: var(--color-error);
}

/* ── Column strip ── */
.column-strip {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-4) var(--space-6);
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
}

.strip-label {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.column-pills { display: flex; flex-wrap: wrap; gap: var(--space-2); }

/* ── Section headings ── */
.section-heading { margin-bottom: var(--space-5); }

.section-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: var(--space-1);
}

.section-sub {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* ── Chart placeholder ── */
.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  min-height: 160px;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.chart-placeholder-icon { font-size: 2.5rem; }

/* ── Delete modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}

.modal {
  max-width: 440px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.modal-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-error);
}

.modal-body { font-size: 0.9rem; color: var(--color-text-muted); line-height: 1.6; }

.modal-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
  margin-top: var(--space-2);
}

.btn-delete-confirm {
  padding: var(--space-3) var(--space-6);
  background: var(--color-error);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.btn-delete-confirm:hover:not(:disabled) { opacity: 0.85; }
.btn-delete-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
