<template>
  <!--
    App.vue — Root component.
    NavBar + ToastNotification live here (every page).
    Page content is swapped in via <RouterView>.
  -->
  <div id="app-shell">
    <NavBar />
    <main class="main-content">
      <!-- Page transition: fades in/out when navigating between routes -->
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <!-- Global toast notifications — rendered on top of everything -->
    <ToastNotification />
  </div>
</template>

<script setup>
/**
 * Axios global interceptor — set up once at the app root.
 *
 * An "interceptor" is a function that runs on every Axios request/response.
 * Here we add a RESPONSE interceptor that catches any network-level error
 * (e.g. Django server is down, 500 error) and shows a toast automatically.
 *
 * This means individual components don't need to handle generic network
 * errors — they only handle their own specific logic.
 */
import { onMounted } from 'vue'
import NavBar            from '@/components/NavBar.vue'
import ToastNotification from '@/components/ToastNotification.vue'
import api               from '@/axios'
import { useToast }      from '@/composables/useToast'

const { error: showError } = useToast()

onMounted(() => {
  // Response interceptor — runs after EVERY api call
  api.interceptors.response.use(
    // Success: just pass the response through unchanged
    response => response,

    // Error: show a toast for common HTTP errors, then re-throw so
    // individual components can still catch and handle if needed
    err => {
      const status = err.response?.status

      if (!err.response) {
        // No response at all → backend is down or network issue
        showError('Cannot reach the server. Is Django running?')
      } else if (status === 500) {
        showError('Server error (500). Check the Django terminal for details.')
      } else if (status === 404) {
        // 404 is often handled per-component (e.g. "dataset not found")
        // so we don't show a global toast — let it bubble up.
      }
      // Always re-throw so components can catch specific errors too
      return Promise.reject(err)
    }
  )
})
</script>

<style scoped>
#app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding-top: 80px; /* offset for fixed navbar */
}

/* ── Page transition ── */
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-enter-active { transition: opacity 200ms ease, transform 200ms ease; }
.page-leave-to  { opacity: 0; transform: translateY(-4px); }
.page-leave-active { transition: opacity 150ms ease, transform 150ms ease; }
</style>
