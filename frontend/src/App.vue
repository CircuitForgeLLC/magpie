<template>
  <div class="app-shell">
    <!-- Sidebar (desktop ≥768px) -->
    <nav class="sidebar">
      <div class="nav-brand">🪶 Magpie</div>
      <router-link class="nav-link" to="/signals" active-class="active">
        <span>🔍</span> Signals
      </router-link>
      <router-link class="nav-link" to="/opportunities" active-class="active">
        <span>📥</span> Opportunities
      </router-link>
      <router-link class="nav-link" to="/campaigns" active-class="active">
        <span>📡</span> Campaigns
      </router-link>
      <router-link class="nav-link" to="/posts" active-class="active">
        <span>📋</span> Post History
      </router-link>
      <router-link class="nav-link" to="/subs" active-class="active">
        <span>📖</span> Sub Rules
      </router-link>
      <SessionWidget class="sidebar-session" />
    </nav>

    <!-- Main -->
    <main class="main-content">
      <StatsBar />
      <router-view />
    </main>

    <!-- Global toast notifications -->
    <ToastList />

    <!-- Bottom Nav (mobile <768px) -->
    <nav class="bottom-nav" aria-label="Main navigation">
      <router-link class="bottom-nav-item" to="/signals" active-class="active">
        <span class="nav-icon">🔍</span>
        <span>Signals</span>
      </router-link>
      <router-link class="bottom-nav-item" to="/opportunities" active-class="active">
        <span class="nav-icon">📥</span>
        <span>Queue</span>
      </router-link>
      <router-link class="bottom-nav-item" to="/campaigns" active-class="active">
        <span class="nav-icon">📡</span>
        <span>Campaigns</span>
      </router-link>
      <router-link class="bottom-nav-item" to="/posts" active-class="active">
        <span class="nav-icon">📋</span>
        <span>Posts</span>
      </router-link>
      <router-link class="bottom-nav-item" to="/subs" active-class="active">
        <span class="nav-icon">📖</span>
        <span>Rules</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import ToastList from './components/ToastList.vue'
import StatsBar from './components/StatsBar.vue'
import SessionWidget from './components/SessionWidget.vue'
</script>

<style scoped>
.sidebar-session {
  margin-top: auto;
}
</style>
