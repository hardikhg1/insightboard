/**
 * useToast.js — Global toast notification composable.
 *
 * What is a composable?
 * A composable is a function that uses Vue's reactivity system (ref, computed, etc.)
 * and can be imported into any component. It's how you share logic across
 * components in Vue 3 without a full state-management library.
 *
 * By creating the `toasts` ref OUTSIDE the function, it becomes module-level
 * state — shared by every component that imports useToast().
 * This is the Vue 3 equivalent of a Vuex store for simple cases.
 *
 * Usage inside any component:
 *   import { useToast } from '@/composables/useToast'
 *   const { showToast } = useToast()
 *   showToast('File uploaded!', 'success')
 */
import { ref } from 'vue'

// Module-level reactive array — shared across all components
const toasts = ref([])
let nextId = 0

export function useToast() {
  /**
   * showToast(message, type, duration)
   *
   * @param {string} message  - Text to display
   * @param {string} type     - 'success' | 'error' | 'info'  (controls colour)
   * @param {number} duration - Milliseconds before auto-dismiss (default 3500)
   */
  function showToast(message, type = 'info', duration = 3500) {
    const id = ++nextId

    // Add the toast to the array — ToastNotification.vue watches this
    toasts.value.push({ id, message, type })

    // Auto-remove after `duration` ms
    setTimeout(() => {
      dismiss(id)
    }, duration)
  }

  function dismiss(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) toasts.value.splice(index, 1)
  }

  // Convenience wrappers so callers don't need to remember type strings
  const success = (msg, duration) => showToast(msg, 'success', duration)
  const error   = (msg, duration) => showToast(msg, 'error',   duration || 5000)
  const info    = (msg, duration) => showToast(msg, 'info',    duration)

  return { toasts, showToast, dismiss, success, error, info }
}
