/**
 * setup.js — Vitest global setup file.
 *
 * This runs once before every test file.
 * We use it to configure @vue/test-utils globally (e.g. stubs for
 * RouterLink/RouterView so tests don't need a real router instance).
 */
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// Stub <RouterLink> and <RouterView> globally so any component that uses them
// doesn't throw "No router instance found" during tests.
config.global.stubs = {
  RouterLink: {
    template: '<a><slot /></a>',
    props: ['to']
  },
  RouterView: true
}

// Mock the browser's ResizeObserver (used by Chart.js internally).
// jsdom doesn't implement it, so without this mock Chart.js tests error out.
global.ResizeObserver = vi.fn(() => ({
  observe:   vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))
