<template>
  <!--
    NavBar.vue — Fixed top navigation bar.
    Uses <RouterLink> instead of <a href> so navigation
    happens without a full page reload (SPA behaviour).
  -->
  <nav class="navbar">
    <div class="container navbar-inner">
      <!-- Brand / Logo -->
      <RouterLink to="/" class="brand">
        <span class="brand-icon">📊</span>
        <span class="brand-name">Insight<span class="gradient-text">Board</span></span>
      </RouterLink>

      <!-- Navigation links -->
      <div class="nav-links">
        <RouterLink to="/" class="nav-link" active-class="nav-link--active" exact>
          Datasets
        </RouterLink>
        <RouterLink to="/upload" class="nav-link" active-class="nav-link--active">
          Upload CSV
        </RouterLink>
      </div>
    </div>
  </nav>
</template>

<script setup>
// No logic needed — this component is purely presentational.
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 64px;
  background: rgba(15, 17, 23, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
}

.navbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

/* Brand */
.brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-decoration: none;
  color: var(--color-text);
}

.brand-icon { font-size: 1.4rem; }

.brand-name {
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

/* Nav links */
.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.nav-link {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  transition: color var(--transition-fast), background var(--transition-fast);
}

.nav-link:hover {
  color: var(--color-text);
  background: var(--color-surface-2);
}

.nav-link--active {
  color: var(--color-text);
  background: var(--color-surface-2);
}
</style>
