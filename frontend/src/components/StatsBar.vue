<template>
  <div v-if="stats" class="stats-bar" aria-label="Activity summary">
    <div class="stats-group">
      <span class="stats-label">Posts</span>
      <span class="stats-chip stats-chip--success">{{ stats.posts.success }} ok</span>
      <span v-if="stats.posts.failed" class="stats-chip stats-chip--danger">{{ stats.posts.failed }} failed</span>
      <span class="stats-chip">{{ stats.posts.last_7_days }} this week</span>
    </div>
    <div class="stats-sep" aria-hidden="true">|</div>
    <div class="stats-group">
      <span class="stats-label">Queue</span>
      <span v-if="stats.opportunities.pending_review" class="stats-chip stats-chip--warn">
        {{ stats.opportunities.pending_review }} pending
      </span>
      <span v-if="stats.opportunities.approved" class="stats-chip stats-chip--accent">
        {{ stats.opportunities.approved }} approved
      </span>
      <span class="stats-chip">{{ stats.opportunities.posted + stats.opportunities.manual_posted }} posted</span>
    </div>
    <div v-if="topCommunity" class="stats-sep" aria-hidden="true">|</div>
    <div v-if="topCommunity" class="stats-group stats-group--community">
      <span class="stats-label">Top</span>
      <span class="stats-chip">{{ topCommunity.community }} ({{ topCommunity.count }})</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api'

interface StatsPayload {
  posts: {
    total: number
    success: number
    failed: number
    skipped: number
    last_7_days: number
    by_platform: Record<string, number>
    top_communities: { community: string; count: number }[]
  }
  opportunities: {
    total: number
    pending_review: number
    approved: number
    posted: number
    manual_posted: number
    dismissed: number
  }
}

const stats = ref<StatsPayload | null>(null)

const topCommunity = computed(() =>
  stats.value?.posts.top_communities[0] ?? null
)

onMounted(async () => {
  try {
    stats.value = await api.stats()
  } catch {
    // Non-critical — stats bar is informational; fail silently
  }
})
</script>

<style scoped>
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 6px 16px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  font-size: 0.78rem;
  color: var(--color-text-muted, #888);
  min-height: 36px;
}

.stats-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stats-group--community {
  /* hide on very narrow screens */
}

.stats-label {
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.72rem;
}

.stats-sep {
  color: var(--color-border);
  user-select: none;
}

.stats-chip {
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--color-bg, #1e1e1e);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  white-space: nowrap;
}
.stats-chip--success { border-color: var(--color-success, #4caf7d); color: var(--color-success, #4caf7d); }
.stats-chip--danger  { border-color: var(--color-danger,  #e05252); color: var(--color-danger,  #e05252); }
.stats-chip--warn    { border-color: var(--color-warn,    #d4a017); color: var(--color-warn,    #d4a017); }
.stats-chip--accent  { border-color: var(--color-accent,  #5b7fa6); color: var(--color-accent,  #5b7fa6); }

@media (max-width: 480px) {
  .stats-group--community { display: none; }
  .stats-sep:last-of-type { display: none; }
}
</style>
