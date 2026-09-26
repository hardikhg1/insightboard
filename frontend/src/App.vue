<template>
  <!--
    App.vue — Root component.

    Every page in the app is rendered inside <RouterView />.
    Vue Router swaps the component here based on the current URL.
    The <NavBar> sits above the router view on every page.
  -->
  <div id="app-shell">
    <NavBar />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
/**
 * <script setup> is Vue 3's "Composition API" shorthand.
 * Code written here is the component's logic. Variables and functions
 * declared here are automatically available in the <template> above.
 */
import NavBar from '@/components/NavBar.vue'
</script>

<style scoped>
/*
  'scoped' means these styles ONLY apply to this component's elements.
  They won't accidentally affect child components.
*/
#app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding-top: 80px; /* offset for the fixed navbar height */
}
</style>
