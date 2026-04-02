<template>
  <div class="layout">
    <header class="topbar">
      <div class="topbar-left">
        <div class="logo-wrap">
          <svg class="logo-icon" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="36" height="36" rx="18" fill="#1877F2"/>
            <text x="7" y="26" font-family="Arial Black, Arial" font-size="22" font-weight="900" fill="white">DB</text>
          </svg>
        </div>
        <span class="site-name">SEMA Studio</span>
      </div>

      <!-- Nav -->
      <nav class="topbar-nav">
        <router-link to="/run" class="nav-link" active-class="nav-link--active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
          </svg>
          <span>Run</span>
        </router-link>
        <router-link to="/plan" class="nav-link" active-class="nav-link--active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4zm2 2H5V5h14v14zM3 3v18h18V3H3z"/>
          </svg>
          <span>Profile</span>
        </router-link>
      </nav>

    </header>

    <main class="page-body">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--fb-bg);
}

/* ---- Topbar ---- */
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--fb-topbar-h);
  background: var(--fb-card);
  border-bottom: 1px solid var(--fb-divider);
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 8px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 220px;
}

.logo-wrap { flex-shrink: 0; }

.logo-icon { width: 40px; height: 40px; display: block; }

.site-name {
  font-size: 1.33rem;
  font-weight: 700;
  color: var(--fb-blue);
  letter-spacing: -0.3px;
}

/* Nav */
.topbar-nav {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.nav-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 36px;
  border-radius: var(--fb-radius);
  border-bottom: 3px solid transparent;
  text-decoration: none;
  color: var(--fb-text-2);
  font-size: 0.8rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
}

.nav-link:hover {
  background: var(--fb-hover);
  color: var(--fb-blue);
}

.nav-link--active {
  color: var(--fb-blue);
  border-bottom-color: var(--fb-blue);
  border-radius: var(--fb-radius) var(--fb-radius) 0 0;
}

.nav-icon {
  width: 22px;
  height: 22px;
}

/* Right */
.topbar-right {
  min-width: 220px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--fb-blue);
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

/* Page body */
.page-body {
  flex: 1;
}
</style>
