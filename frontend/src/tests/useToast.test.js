/**
 * useToast.test.js — Unit tests for the useToast composable.
 *
 * What is `vi`?
 * vi is Vitest's version of Jest's `jest` object. vi.useFakeTimers()
 * makes setTimeout run instantly in tests — so we don't have to wait
 * 3500ms for a toast to auto-dismiss.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useToast } from '@/composables/useToast'

describe('useToast', () => {

  beforeEach(() => {
    // Use fake timers so setTimeout fires instantly in tests
    vi.useFakeTimers()
    // Clear toasts between tests
    const { toasts } = useToast()
    toasts.value.splice(0)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('adds a toast to the list', () => {
    const { toasts, showToast } = useToast()
    showToast('Hello!', 'success')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Hello!')
    expect(toasts.value[0].type).toBe('success')
  })

  it('auto-dismisses after the duration', () => {
    const { toasts, showToast } = useToast()
    showToast('Auto bye', 'info', 1000)
    expect(toasts.value).toHaveLength(1)

    // Fast-forward 1000ms — the auto-dismiss setTimeout should fire
    vi.advanceTimersByTime(1000)
    expect(toasts.value).toHaveLength(0)
  })

  it('dismiss() removes the correct toast', () => {
    const { toasts, showToast, dismiss } = useToast()
    showToast('First',  'success')
    showToast('Second', 'error')
    expect(toasts.value).toHaveLength(2)

    const firstId = toasts.value[0].id
    dismiss(firstId)

    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Second')
  })

  it('success() helper adds a success-typed toast', () => {
    const { toasts, success } = useToast()
    success('Done!')
    expect(toasts.value[0].type).toBe('success')
  })

  it('error() helper adds an error-typed toast', () => {
    const { toasts, error } = useToast()
    error('Something broke')
    expect(toasts.value[0].type).toBe('error')
  })
})
