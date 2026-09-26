<template>
  <!--
    DataTable.vue — Paginated, filterable, sortable data table.

    Props:
      columns  — Array of DatasetColumn objects  { id, name, position, data_type }
      datasetId — The Dataset pk (used to call the row-filter API)

    What is a "prop"?
    A prop is data passed INTO a component from its parent.
    Just like a function argument — the parent supplies the value,
    the child uses it.
  -->
  <div class="data-table-wrapper">

    <!-- ── Filter Bar ─────────────────────────────────────────────── -->
    <div class="filter-bar card">
      <div class="filter-row">
        <!-- Column selector dropdown -->
        <div class="filter-group">
          <label class="filter-label" for="filter-col">Filter column</label>
          <select id="filter-col" v-model="filterColumn" class="input" @change="filterValue = ''">
            <option value="">— all columns —</option>
            <option v-for="col in columns" :key="col.id" :value="col.name">
              {{ col.name }}
            </option>
          </select>
        </div>

        <!-- Value input -->
        <div class="filter-group filter-group--grow">
          <label class="filter-label" for="filter-val">Search value</label>
          <input
            id="filter-val"
            v-model="filterValue"
            class="input"
            type="text"
            placeholder="Type to filter…"
            :disabled="!filterColumn"
            @keyup.enter="applyFilter"
          />
        </div>

        <!-- Apply / Clear buttons -->
        <div class="filter-actions">
          <button class="btn-primary" :disabled="!filterColumn || !filterValue" @click="applyFilter">
            Apply
          </button>
          <button class="btn-secondary" @click="clearFilter">
            Clear
          </button>
        </div>
      </div>

      <!-- Active filter badge -->
      <div v-if="activeFilter.column" class="active-filter">
        <span>Active filter:</span>
        <span class="badge badge-number">{{ activeFilter.column }} = "{{ activeFilter.value }}"</span>
        <span class="filter-count">{{ rows.length }} result{{ rows.length !== 1 ? 's' : '' }}</span>
      </div>
    </div>

    <!-- ── Loading / Error states ─────────────────────────────────── -->
    <div v-if="loadingRows" class="spinner"></div>
    <div v-else-if="rowError" class="error-box" style="margin-top:var(--space-5)">{{ rowError }}</div>

    <!-- ── Table ──────────────────────────────────────────────────── -->
    <div v-else class="table-outer">
      <div v-if="rows.length === 0" class="empty-table">
        <p>No rows match the current filter.</p>
      </div>

      <div v-else class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th class="row-num-th">#</th>
              <th
                v-for="col in columns"
                :key="col.id"
                class="col-th"
                :class="{ 'col-th--sorted': sortKey === col.name }"
                @click="toggleSort(col.name)"
              >
                <span class="th-inner">
                  {{ col.name }}
                  <span class="badge" :class="`badge-${col.data_type}`">{{ col.data_type }}</span>
                  <span class="sort-icon">
                    {{ sortKey === col.name ? (sortDir === 'asc' ? '↑' : '↓') : '↕' }}
                  </span>
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in paginatedRows"
              :key="row.id"
              class="data-row"
              :class="{ 'data-row--even': i % 2 === 0 }"
            >
              <!-- Row number (1-based, accounting for current page) -->
              <td class="row-num-td">{{ (currentPage - 1) * pageSize + i + 1 }}</td>
              <td v-for="col in columns" :key="col.id" class="data-cell">
                <span v-if="row.data[col.name] === null || row.data[col.name] === undefined" class="null-value">
                  null
                </span>
                <span v-else>{{ row.data[col.name] }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── Pagination ────────────────────────────────────────────── -->
      <div v-if="totalPages > 1" class="pagination">
        <button class="btn-secondary" :disabled="currentPage === 1" @click="currentPage = 1">
          «
        </button>
        <button class="btn-secondary" :disabled="currentPage === 1" @click="currentPage--">
          ‹
        </button>

        <span class="page-info">
          Page {{ currentPage }} of {{ totalPages }}
          <span class="page-total">({{ sortedRows.length }} rows)</span>
        </span>

        <button class="btn-secondary" :disabled="currentPage === totalPages" @click="currentPage++">
          ›
        </button>
        <button class="btn-secondary" :disabled="currentPage === totalPages" @click="currentPage = totalPages">
          »
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
/**
 * Why Composition API?
 * Vue 3's Composition API (ref, computed, watch) lets you group
 * related logic together instead of splitting it across data/methods/computed.
 * It's easier to understand once you see the pattern.
 */
import { ref, computed, watch } from 'vue'
import api from '@/axios'

// ── Props ──────────────────────────────────────────────────────────────────
const props = defineProps({
  columns:   { type: Array,  required: true },
  datasetId: { type: [Number, String], required: true }
})

// ── State ──────────────────────────────────────────────────────────────────
const rows        = ref([])         // rows currently shown (filtered or all)
const loadingRows = ref(true)
const rowError    = ref(null)

const filterColumn = ref('')        // which column is selected in the dropdown
const filterValue  = ref('')        // what the user typed
const activeFilter = ref({ column: '', value: '' })  // the last applied filter

const sortKey  = ref('')            // which column header was clicked
const sortDir  = ref('asc')        // 'asc' or 'desc'

const currentPage = ref(1)
const pageSize    = ref(20)         // rows per page

// ── Fetch rows ─────────────────────────────────────────────────────────────
async function fetchRows(column = '', value = '') {
  loadingRows.value = true
  rowError.value    = null
  currentPage.value = 1             // reset to first page on every fetch

  try {
    const params = {}
    if (column && value) {
      params.column = column
      params.value  = value
    }
    const res = await api.get(`/datasets/${props.datasetId}/rows/`, { params })
    rows.value = res.data
  } catch (err) {
    rowError.value = 'Could not load rows. Please try again.'
  } finally {
    loadingRows.value = false
  }
}

// Load all rows when the component is first mounted
fetchRows()

// ── Filter ─────────────────────────────────────────────────────────────────
function applyFilter() {
  if (!filterColumn.value || !filterValue.value) return
  activeFilter.value = { column: filterColumn.value, value: filterValue.value }
  fetchRows(filterColumn.value, filterValue.value)
}

function clearFilter() {
  filterColumn.value = ''
  filterValue.value  = ''
  activeFilter.value = { column: '', value: '' }
  fetchRows()
}

// ── Sort ───────────────────────────────────────────────────────────────────
// Computed = automatically recalculated whenever its dependencies change.
// sortedRows re-sorts whenever rows, sortKey or sortDir changes.
function toggleSort(colName) {
  if (sortKey.value === colName) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = colName
    sortDir.value = 'asc'
  }
  currentPage.value = 1
}

const sortedRows = computed(() => {
  if (!sortKey.value) return rows.value

  return [...rows.value].sort((a, b) => {
    const av = a.data[sortKey.value]
    const bv = b.data[sortKey.value]

    // null values always go to the bottom
    if (av === null || av === undefined) return 1
    if (bv === null || bv === undefined) return -1

    // Numeric sort if both values look like numbers
    if (typeof av === 'number' && typeof bv === 'number') {
      return sortDir.value === 'asc' ? av - bv : bv - av
    }

    // String sort (case-insensitive)
    const as = String(av).toLowerCase()
    const bs = String(bv).toLowerCase()
    if (as < bs) return sortDir.value === 'asc' ? -1 : 1
    if (as > bs) return sortDir.value === 'asc' ?  1 : -1
    return 0
  })
})

// ── Pagination ─────────────────────────────────────────────────────────────
const totalPages = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)))

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedRows.value.slice(start, start + pageSize.value)
})

// Reset to page 1 if sortedRows shrinks (e.g. filter applied)
watch(sortedRows, () => {
  if (currentPage.value > totalPages.value) currentPage.value = 1
})
</script>

<style scoped>
.data-table-wrapper { display: flex; flex-direction: column; gap: var(--space-5); }

/* ── Filter bar ── */
.filter-bar { padding: var(--space-5) var(--space-6); }

.filter-row {
  display: flex;
  align-items: flex-end;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 180px;
}

.filter-group--grow { flex: 1; }

.filter-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-actions {
  display: flex;
  gap: var(--space-2);
  align-items: flex-end;
  padding-bottom: 1px; /* visual alignment with inputs */
}

.active-filter {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.filter-count { margin-left: auto; color: var(--color-text-muted); font-size: 0.8rem; }

/* ── Table scroll container ── */
.table-scroll {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.empty-table {
  text-align: center;
  padding: var(--space-10);
  color: var(--color-text-muted);
}

/* ── Table ── */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  white-space: nowrap;
}

/* Header */
.data-table thead {
  background: var(--color-surface-2);
  position: sticky;
  top: 0;
  z-index: 1;
}

.col-th, .row-num-th {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  cursor: pointer;
  user-select: none;
  transition: color var(--transition-fast);
}

.row-num-th { cursor: default; width: 48px; }

.col-th:hover { color: var(--color-text); }

.col-th--sorted { color: var(--accent-from); }

.th-inner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.sort-icon {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

/* Body rows */
.data-row {
  border-bottom: 1px solid var(--color-border);
  transition: background var(--transition-fast);
}

.data-row:hover { background: var(--color-surface-2); }

.data-row--even { background: rgba(255,255,255,0.015); }
.data-row--even:hover { background: var(--color-surface-2); }

.row-num-td {
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-muted);
  font-size: 0.78rem;
  text-align: right;
  border-right: 1px solid var(--color-border);
}

.data-cell {
  padding: var(--space-3) var(--space-4);
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.null-value {
  color: var(--color-text-muted);
  font-style: italic;
  font-size: 0.8rem;
}

/* ── Pagination ── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding-top: var(--space-5);
  flex-wrap: wrap;
}

.page-info {
  font-size: 0.88rem;
  color: var(--color-text-muted);
  min-width: 140px;
  text-align: center;
}

.page-total {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

/* Make secondary buttons smaller for pagination */
.pagination .btn-secondary {
  padding: var(--space-2) var(--space-3);
  font-size: 0.85rem;
  min-width: 36px;
  justify-content: center;
}
</style>
