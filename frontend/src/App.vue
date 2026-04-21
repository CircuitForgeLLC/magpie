<template>
  <div class="app-shell">
    <nav class="sidebar">
      <div class="nav-brand">🪶 Magpie</div>
      <router-link class="nav-link" to="/opportunities" active-class="active">Opportunities</router-link>
      <router-link class="nav-link" to="/campaigns" active-class="active">Campaigns</router-link>
      <router-link class="nav-link" to="/posts" active-class="active">Post History</router-link>
      <router-link class="nav-link" to="/subs" active-class="active">Sub Rules</router-link>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>
