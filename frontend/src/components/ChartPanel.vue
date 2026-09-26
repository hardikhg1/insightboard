<template>
  <!--
    ChartPanel.vue — Dynamic Chart.js visualisation panel.

    Props:
      columns   — Array of DatasetColumn objects { id, name, data_type }
      datasetId — Dataset pk (used to fetch all rows)

    How vue-chartjs works:
      vue-chartjs wraps Chart.js chart types (Bar, Line, Pie, Doughnut)
      as Vue components. You pass `data` and `options` props and it
      handles the canvas rendering automatically.
      We must call Chart.register() first to tell Chart.js which
      components (scales, elements, plugins) to include.
  -->
  <div class="chart-panel card">

    <!-- ── Controls row ──────────────────────────────────────────── -->
    <div class="chart-controls">
      <!-- Column picker -->
      <div class="ctrl-group">
        <label class="filter-label" for="chart-col">Column to visualise</label>
        <select id="chart-col" v-model="selectedColumn" class="input" @change="onColumnChange">
          <option value="">— choose a column —</option>
          <option v-for="col in columns" :key="col.id" :value="col">
            {{ col.name }}
            <template v-if="col.data_type !== 'text'"> ({{ col.data_type }})</template>
          </option>
        </select>
      </div>

      <!-- Chart type toggle -->
      <div class="ctrl-group">
        <label class="filter-label">Chart type</label>
        <div class="chart-type-btns" role="group">
          <button
            v-for="ct in chartTypes"
            :key="ct.value"
            class="chart-type-btn"
            :class="{ 'chart-type-btn--active': chartType === ct.value }"
            @click="chartType = ct.value"
          >
            {{ ct.icon }} {{ ct.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── States ─────────────────────────────────────────────────── -->
    <div v-if="!selectedColumn" class="chart-empty">
      <span class="chart-empty-icon">📊</span>
      <p>Select a column above to generate a chart.</p>
    </div>

    <div v-else-if="loadingRows" class="spinner"></div>

    <div v-else-if="rowError" class="error-box">{{ rowError }}</div>

    <div v-else-if="chartData" class="chart-canvas-wrap">
      <!-- Chart type info badge -->
      <div class="chart-info">
        <span class="badge" :class="`badge-${selectedColumn.data_type}`">
          {{ selectedColumn.name }}
        </span>
        <span class="chart-desc">{{ chartDescription }}</span>
        <span class="badge badge-number">{{ chartData.labels.length }} data points</span>
      </div>

      <!--
        Dynamic chart rendering.
        v-if / v-else-if swaps the component based on chartType.
        :data and :options are passed as props to the vue-chartjs wrapper.
      -->
      <Bar
        v-if="chartType === 'bar'"
        :data="chartData"
        :options="chartOptions"
        class="chart-canvas"
      />
      <Line
        v-else-if="chartType === 'line'"
        :data="chartData"
        :options="chartOptions"
        class="chart-canvas"
      />
      <Doughnut
        v-else-if="chartType === 'doughnut'"
        :data="doughnutData"
        :options="doughnutOptions"
        class="chart-canvas chart-canvas--doughnut"
      />
    </div>

  </div>
</template>

<script setup>
/**
 * Imports explained:
 *
 * 1. Chart.js — the actual charting library. We import the specific
 *    "pieces" we need and register them. This keeps the bundle small.
 *
 * 2. vue-chartjs — Vue wrappers (Bar, Line, Doughnut) that turn
 *    Chart.js canvases into Vue components.
 *
 * 3. Vue reactivity — ref() for reactive state, computed() for
 *    values that auto-recalculate, watch() to react to changes.
 */
import { ref, computed } from 'vue'
import {
  Chart,
  BarElement, BarController,
  LineElement, LineController, PointElement,
  ArcElement, DoughnutController,
  CategoryScale, LinearScale,
  Title, Tooltip, Legend,
  Filler
} from 'chart.js'
import { Bar, Line, Doughnut } from 'vue-chartjs'
import api from '@/axios'

// Register all Chart.js components we'll use.
// Without this, Chart.js throws "X is not a registered scale".
Chart.register(
  BarElement, BarController,
  LineElement, LineController, PointElement,
  ArcElement, DoughnutController,
  CategoryScale, LinearScale,
  Title, Tooltip, Legend,
  Filler
)

// ── Props ──────────────────────────────────────────────────────────────────
const props = defineProps({
  columns:   { type: Array,            required: true },
  datasetId: { type: [Number, String], required: true }
})

// ── State ──────────────────────────────────────────────────────────────────
const selectedColumn = ref('')    // the full column object { id, name, data_type }
const chartType      = ref('bar') // 'bar' | 'line' | 'doughnut'
const allRows        = ref([])    // raw DataRow objects from the API
const loadingRows    = ref(false)
const rowError       = ref(null)

const chartTypes = [
  { value: 'bar',      label: 'Bar',      icon: '▬' },
  { value: 'line',     label: 'Line',     icon: '📈' },
  { value: 'doughnut', label: 'Doughnut', icon: '🍩' }
]

// ── Colour palette ─────────────────────────────────────────────────────────
const PALETTE = [
  'rgba(99,  102, 241, 0.85)',
  'rgba(168, 85,  247, 0.85)',
  'rgba(16,  185, 129, 0.85)',
  'rgba(245, 158, 11,  0.85)',
  'rgba(239, 68,  68,  0.85)',
  'rgba(14,  165, 233, 0.85)',
  'rgba(244, 114, 182, 0.85)',
  'rgba(52,  211, 153, 0.85)',
  'rgba(251, 146, 60,  0.85)',
  'rgba(163, 230, 53,  0.85)',
  'rgba(129, 140, 248, 0.85)',
  'rgba(192, 132, 252, 0.85)',
  'rgba(110, 231, 183, 0.85)',
  'rgba(253, 224, 71,  0.85)',
  'rgba(147, 197, 253, 0.85)',
]

// ── Fetch rows ─────────────────────────────────────────────────────────────
async function fetchAllRows() {
  if (!selectedColumn.value) return
  loadingRows.value = true
  rowError.value    = null
  try {
    const res = await api.get(`/datasets/${props.datasetId}/rows/`)
    allRows.value = res.data
  } catch {
    rowError.value = 'Could not load chart data. Please try again.'
  } finally {
    loadingRows.value = false
  }
}

function onColumnChange() {
  if (selectedColumn.value) {
    // Auto-pick sensible default chart type based on column type
    chartType.value = selectedColumn.value.data_type === 'number' ? 'line' : 'bar'
    fetchAllRows()
  }
}

// ── Chart data computation ─────────────────────────────────────────────────
function valueCounts(values, cap = 20) {
  const counts = {}
  for (const v of values) {
    const key = v === null || v === undefined ? '(empty)' : String(v)
    counts[key] = (counts[key] || 0) + 1
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, cap)
}

const chartData = computed(() => {
  if (!selectedColumn.value || allRows.value.length === 0) return null

  const colName = selectedColumn.value.name
  const dtype   = selectedColumn.value.data_type
  const rawValues = allRows.value
    .map(r => r.data[colName])
    .filter(v => v !== null && v !== undefined)

  if (rawValues.length === 0) return null

  // Number → values over row index
  if (dtype === 'number') {
    const LIMIT = 200
    const slice  = rawValues.slice(0, LIMIT)
    return {
      labels: slice.map((_, i) => `Row ${i + 1}`),
      datasets: [{
        label: colName,
        data: slice,
        backgroundColor: 'rgba(99, 102, 241, 0.25)',
        borderColor:     'rgba(99, 102, 241, 1)',
        borderWidth: 2,
        pointRadius: slice.length > 50 ? 0 : 3,
        tension: 0.35,
        fill: chartType.value === 'line'
      }]
    }
  }

  // Text / Date → value counts
  const counts  = valueCounts(rawValues)
  const labels   = counts.map(([k]) => k)
  const dataVals = counts.map(([, v]) => v)
  const colors   = labels.map((_, i) => PALETTE[i % PALETTE.length])

  return {
    labels,
    datasets: [{
      label: `${colName} — count`,
      data:  dataVals,
      backgroundColor: colors,
      borderColor:     colors.map(c => c.replace('0.85', '1')),
      borderWidth: 1,
      borderRadius: 4
    }]
  }
})

const doughnutData = computed(() => {
  if (!chartData.value) return null
  return {
    ...chartData.value,
    datasets: chartData.value.datasets.map(ds => ({ ...ds, hoverOffset: 12 }))
  }
})

// ── Chart options ──────────────────────────────────────────────────────────
const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 500 },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(26, 29, 46, 0.95)',
      titleColor: '#e2e8f0',
      bodyColor:  '#8892a4',
      borderColor: '#2e3349',
      borderWidth: 1,
      padding: 10,
      cornerRadius: 8
    }
  }
}

const chartOptions = computed(() => ({
  ...baseOptions,
  scales: {
    x: {
      ticks: { color: '#8892a4', maxRotation: 45, autoSkip: true, maxTicksLimit: 20, font: { size: 11 } },
      grid:  { color: 'rgba(46, 51, 73, 0.6)' }
    },
    y: {
      ticks: { color: '#8892a4', font: { size: 11 } },
      grid:  { color: 'rgba(46, 51, 73, 0.6)' },
      beginAtZero: true
    }
  }
}))

const doughnutOptions = {
  ...baseOptions,
  plugins: {
    ...baseOptions.plugins,
    legend: {
      display: true,
      position: 'right',
      labels: { color: '#e2e8f0', font: { size: 12 }, padding: 14, usePointStyle: true, pointStyleWidth: 10 }
    }
  }
}

const chartDescription = computed(() => {
  if (!selectedColumn.value) return ''
  return selectedColumn.value.data_type === 'number'
    ? 'Numeric values plotted over row index (first 200 rows)'
    : 'Count of each unique value (top 20)'
})
</script>

<style scoped>
.chart-panel { display: flex; flex-direction: column; gap: var(--space-6); }

.chart-controls {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-5);
  align-items: flex-end;
}

.ctrl-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 220px;
}

.filter-label {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.chart-type-btns { display: flex; gap: var(--space-2); flex-wrap: wrap; }

.chart-type-btn {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.chart-type-btn:hover { background: var(--color-surface-2); color: var(--color-text); }
.chart-type-btn--active {
  background: var(--color-surface-2);
  border-color: var(--accent-from);
  color: var(--accent-from);
  font-weight: 600;
}

.chart-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: var(--space-3); padding: var(--space-10) 0;
  color: var(--color-text-muted); font-size: 0.9rem;
}
.chart-empty-icon { font-size: 2.5rem; }

.chart-info {
  display: flex; align-items: center; gap: var(--space-3);
  font-size: 0.82rem; color: var(--color-text-muted); flex-wrap: wrap;
}
.chart-desc { flex: 1; }

.chart-canvas-wrap { display: flex; flex-direction: column; gap: var(--space-4); }

.chart-canvas {
  height: 380px !important;
  max-height: 380px;
}
.chart-canvas--doughnut {
  height: 340px !important;
  max-height: 340px;
}
</style>
