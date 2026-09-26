<template>
  <section class="container section">
    <!-- Loading -->
    <div v-if="loading" class="spinner"></div>

    <!-- Error -->
    <div v-else-if="error" class="error-box">{{ error }}</div>

    <!-- Content -->
    <template v-else-if="dataset">
      <!-- Header -->
      <div class="ds-header">
        <div>
          <h1 class="page-title">{{ dataset.name }}</h1>
          <p class="page-subtitle">{{ dataset.original_filename }}</p>
        </div>
        <div class="ds-meta">
          <span class="badge badge-number">{{ dataset.row_count }} rows</span>
          <span class="badge badge-text">{{ dataset.column_count }} columns</span>
        </div>
      </div>

      <!-- Placeholder for DataTable (Step 8) and Charts (Step 9) -->
      <div class="card placeholder-notice">
        <p>🔧 <strong>Step 8</strong> will add the data table &amp; filters here.</p>
        <p>📈 <strong>Step 9</strong> will add Chart.js visualisations here.</p>
        <p style="margin-top:var(--space-4); color:var(--color-text-muted); font-size:0.85rem;">
          Dataset loaded successfully — {{ dataset.columns.length }} columns detected.
        </p>
        <div class="column-pills">
          <span
            v-for="col in dataset.columns"
            :key="col.id"
            class="badge"
            :class="`badge-${col.data_type}`"
          >
            {{ col.name }}
          </span>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/axios'

// useRoute() gives access to the current URL parameters (:id from router)
const route   = useRoute()
const dataset = ref(null)
const loading = ref(true)
const error   = ref(null)

onMounted(async () => {
  try {
    const response = await api.get(`/datasets/${route.params.id}/`)
    dataset.value = response.data
  } catch (err) {
    error.value = 'Could not load dataset. It may have been deleted.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.section { padding-block: var(--space-10); }

.ds-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.ds-meta { display: flex; gap: var(--space-2); align-items: center; }

.placeholder-notice {
  color: var(--color-text-muted);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.column-pills {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}
</style>
