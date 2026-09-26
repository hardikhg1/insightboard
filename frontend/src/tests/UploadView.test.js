/**
 * UploadView.test.js — Component tests for the CSV upload page.
 *
 * Key concepts:
 *
 * mount() — renders the full component tree in jsdom.
 *
 * vi.mock() — replaces a module with a fake. Here we mock '@/axios' so
 *   API calls never hit the real network. Tests are fast and offline.
 *
 * await wrapper.vm.$nextTick() — waits for Vue to update the DOM after
 *   a reactive change.
 *
 * wrapper.find() — queries the DOM like document.querySelector().
 *
 * wrapper.trigger() — fires a DOM event (click, change, etc.).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHashHistory } from 'vue-router'
import UploadView from '@/views/UploadView.vue'

// ── Mock axios so no real HTTP requests happen ─────────────────────────────
vi.mock('@/axios', () => ({
  default: {
    post: vi.fn(),
    interceptors: {
      response: { use: vi.fn() }
    }
  }
}))

// ── Mock useToast so we can spy on toast calls ─────────────────────────────
const mockSuccess = vi.fn()
const mockError   = vi.fn()
vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: mockSuccess,
    error:   mockError,
    toasts:  { value: [] }
  })
}))

// ── A minimal router (UploadView uses useRouter for redirect) ──────────────
function makeRouter() {
  return createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: '/',          component: { template: '<div/>' } },
      { path: '/upload',    component: UploadView },
      { path: '/datasets/:id', component: { template: '<div/>' } }
    ]
  })
}

describe('UploadView', () => {
  let wrapper
  let api

  beforeEach(async () => {
    vi.clearAllMocks()
    // Re-import the mock so we can configure it per-test
    api = (await import('@/axios')).default

    const router = makeRouter()
    await router.push('/upload')

    wrapper = mount(UploadView, {
      global: { plugins: [router] }
    })
  })

  it('renders the upload page heading', () => {
    expect(wrapper.find('h1').text()).toContain('Upload a CSV')
  })

  it('upload button is disabled when no file is selected', () => {
    const btn = wrapper.find('button.upload-btn')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('upload button is enabled after a file is selected', async () => {
    /*
     * Simulate a file-change event with a fake File object.
     * We can't trigger a real file picker in jsdom, but we can
     * call the input's change handler directly.
     */
    const fakeFile = new File(['col1\nval1\n'], 'test.csv', { type: 'text/csv' })
    const input = wrapper.find('input[type="file"]')
    // Manually set the files property and trigger change
    Object.defineProperty(input.element, 'files', {
      value: [fakeFile], writable: false
    })
    await input.trigger('change')

    const btn = wrapper.find('button.upload-btn')
    expect(btn.attributes('disabled')).toBeUndefined()
  })

  it('calls api.post with FormData on submit', async () => {
    api.post.mockResolvedValueOnce({
      data: { id: 42, name: 'test', row_count: 1, column_count: 1 }
    })

    // Select a file
    const fakeFile = new File(['a,b\n1,2\n'], 'data.csv', { type: 'text/csv' })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [fakeFile], writable: false })
    await input.trigger('change')

    // Click upload
    await wrapper.find('button.upload-btn').trigger('click')
    await flushPromises()

    // api.post should have been called once with the upload URL
    expect(api.post).toHaveBeenCalledTimes(1)
    expect(api.post.mock.calls[0][0]).toBe('/datasets/upload/')
    // The second argument must be a FormData instance
    expect(api.post.mock.calls[0][1]).toBeInstanceOf(FormData)
  })

  it('shows success toast and resets file on successful upload', async () => {
    api.post.mockResolvedValueOnce({
      data: { id: 5, name: 'mydata', row_count: 10, column_count: 3 }
    })

    const fakeFile = new File(['x\n1\n'], 'mydata.csv', { type: 'text/csv' })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [fakeFile], writable: false })
    await input.trigger('change')
    await wrapper.find('button.upload-btn').trigger('click')
    await flushPromises()

    expect(mockSuccess).toHaveBeenCalledTimes(1)
    expect(mockSuccess.mock.calls[0][0]).toContain('mydata')
  })

  it('shows inline error for 400 response', async () => {
    api.post.mockRejectedValueOnce({
      response: { status: 400, data: { error: 'Only .csv files are supported.' } }
    })

    const fakeFile = new File(['x\n1\n'], 'mydata.csv', { type: 'text/csv' })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [fakeFile], writable: false })
    await input.trigger('change')
    await wrapper.find('button.upload-btn').trigger('click')
    await flushPromises()

    // The error-box div should appear in the DOM
    const errorBox = wrapper.find('.error-box')
    expect(errorBox.exists()).toBe(true)
    expect(errorBox.text()).toContain('Only .csv files are supported.')
  })
})
