<template>
  <!--
    ToastNotification.vue — Animated toast container.

    This component sits in App.vue and watches the shared `toasts` array
    from useToast(). Whenever a toast is added, it animates in from the
    bottom-right and disappears after the auto-dismiss timeout.

    <TransitionGroup> is a Vue built-in that animates lists as items
    are added and removed. The `name="toast"` maps to CSS class names
    like .toast-enter-active, .toast-leave-active (defined below).
  -->
  <div class="toast-container" aria-live="polite">
    <TransitionGroup name="toast" tag="div" class="toast-list">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="`toast--${toast.type}`"
        role="alert"
        @click="dismiss(toast.id)"
      >
        <span class="toast-icon">{{ iconFor(toast.type) }}</span>
        <span class="toast-msg">{{ toast.message }}</span>
        <button class="toast-close" aria-label="Dismiss">✕</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useToast } from '@/composables/useToast'

const { toasts, dismiss } = useToast()

function iconFor(type) {
  return { success: '✅', error: '❌', info: 'ℹ️' }[type] ?? 'ℹ️'
}
</script>

<style scoped>
/* Fixed container in the bottom-right corner */
.toast-container {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  z-index: 9999;
  pointer-events: none; /* don't block clicks on the page behind */
}

.toast-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  align-items: flex-end;
}

/* Individual toast */
.toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  min-width: 280px;
  max-width: 420px;
  pointer-events: all; /* re-enable clicks on the toast itself */
  cursor: pointer;
  backdrop-filter: blur(8px);
}

.toast--success {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.1);
}
.toast--error {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.1);
}
.toast--info {
  border-color: rgba(99, 102, 241, 0.4);
  background: rgba(99, 102, 241, 0.1);
}

.toast-icon { font-size: 1.1rem; flex-shrink: 0; }
.toast-msg  { flex: 1; font-size: 0.88rem; line-height: 1.4; }
.toast-close {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
  flex-shrink: 0;
  transition: color var(--transition-fast);
}
.toast-close:hover { color: var(--color-text); }

/* ── TransitionGroup animations ── */
/* 'toast-enter' = when a new toast is added */
.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.toast-enter-active {
  transition: opacity 250ms ease, transform 250ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* 'toast-leave' = when a toast is removed */
.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
.toast-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
  position: absolute; /* prevents layout shift during leave */
}

/* Smooth repositioning of remaining toasts when one leaves */
.toast-move {
  transition: transform 250ms ease;
}

/* Mobile: full width at bottom */
@media (max-width: 480px) {
  .toast-container {
    left: var(--space-4);
    right: var(--space-4);
    bottom: var(--space-4);
  }
  .toast { min-width: unset; max-width: unset; width: 100%; }
}
</style>
