/**
 * DataTable.test.js — Component tests for the data table.
 *
 * DataTable calls GET /api/datasets/<pk>/rows/ on mount.
 * We mock axios so those calls return controlled test data.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DataTable from '@/components/DataTable.vue'

// ── Mock axios ─────────────────────────────────────────────────────────────
vi.mock('@/axios', () => ({
  default: {
    get: vi.fn(),
    interceptors: { response: { use: vi.fn() } }
  }
}))

// ── Sample test data ───────────────────────────────────────────────────────
const COLUMNS = [
  { id: 1, name: 'product', position: 0, data_type: 'text' },
  { id: 2, name: 'revenue', position: 1, data_type: 'number' }
]

const ROWS = [
  { id: 1, row_index: 0, data: { product: 'Pen',    revenue: 100 } },
  { id: 2, row_index: 1, data: { product: 'Book',   revenue: 250 } },
  { id: 3, row_index: 2, data: { product: 'Pen',    revenue: 300 } },
  { id: 4, row_index: 3, data: { product: 'Eraser', revenue: 50  } }
]

function mountTable(apiRows = ROWS) {
  const api = require('@/axios').default
  api.get.mockResolvedValue({ data: apiRows })
  return mount(DataTable, {
    props: { columns: COLUMNS, datasetId: 1 }
  })
}

describe('DataTable', () => {
  let api

  beforeEach(async () => {
    vi.clearAllMocks()
    api = (await import('@/axios')).default
  })

  it('renders a table header for each column', async () => {
    api.get.mockResolvedValueOnce({ data: ROWS })
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    await flushPromises()

    // There should be one <th> per column (plus the row-number th)
    const headers = wrapper.findAll('.col-th')
    expect(headers).toHaveLength(COLUMNS.length)
    expect(headers[0].text()).toContain('product')
    expect(headers[1].text()).toContain('revenue')
  })

  it('renders a table row for each data row returned by the API', async () => {
    api.get.mockResolvedValueOnce({ data: ROWS })
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    await flushPromises()

    const rows = wrapper.findAll('.data-row')
    expect(rows).toHaveLength(ROWS.length)
  })

  it('displays the correct cell values', async () => {
    api.get.mockResolvedValueOnce({ data: ROWS })
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    await flushPromises()

    // First data cell in first row should be "Pen"
    const firstRow = wrapper.findAll('.data-row')[0]
    const cells = firstRow.findAll('.data-cell')
    expect(cells[0].text()).toBe('Pen')
    expect(cells[1].text()).toBe('100')
  })

  it('shows "null" for missing values', async () => {
    const rowsWithNull = [
      { id: 1, row_index: 0, data: { product: null, revenue: 50 } }
    ]
    api.get.mockResolvedValueOnce({ data: rowsWithNull })
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    await flushPromises()

    const nullSpan = wrapper.find('.null-value')
    expect(nullSpan.exists()).toBe(true)
    expect(nullSpan.text()).toBe('null')
  })

  it('calls API with filter params when Apply is clicked', async () => {
    // First call: initial load (all rows)
    api.get.mockResolvedValueOnce({ data: ROWS })
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    await flushPromises()

    // Select a filter column and value
    await wrapper.find('#filter-col').setValue('product')
    await wrapper.find('#filter-val').setValue('Pen')

    // Second call: filtered rows
    api.get.mockResolvedValueOnce({ data: [ROWS[0], ROWS[2]] })
    await wrapper.find('button.btn-primary').trigger('click')
    await flushPromises()

    // The second API call should have column + value params
    expect(api.get).toHaveBeenCalledTimes(2)
    const secondCallParams = api.get.mock.calls[1][1].params
    expect(secondCallParams.column).toBe('product')
    expect(secondCallParams.value).toBe('Pen')
  })

  it('resets to all rows when Clear is clicked', async () => {
    api.get.mockResolvedValue({ data: ROWS })
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    await flushPromises()

    // Apply a filter
    await wrapper.find('#filter-col').setValue('product')
    await wrapper.find('#filter-val').setValue('Pen')
    api.get.mockResolvedValueOnce({ data: [ROWS[0], ROWS[2]] })
    await wrapper.find('button.btn-primary').trigger('click')
    await flushPromises()

    // Now clear — should call API without params
    api.get.mockResolvedValueOnce({ data: ROWS })
    await wrapper.find('button.btn-secondary').trigger('click')
    await flushPromises()

    const lastCall = api.get.mock.calls.at(-1)
    expect(lastCall[1].params).toEqual({})
  })

  it('shows the spinner while loading', () => {
    // Don't resolve the mock yet — component is in loading state
    api.get.mockReturnValue(new Promise(() => {}))
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    expect(wrapper.find('.spinner').exists()).toBe(true)
  })

  it('shows error box when API call fails', async () => {
    api.get.mockRejectedValueOnce(new Error('Network error'))
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, datasetId: 1 }
    })
    await flushPromises()
    expect(wrapper.find('.error-box').exists()).toBe(true)
  })
})
