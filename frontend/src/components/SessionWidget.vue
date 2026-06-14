<template>
  <div class="session-widget" :title="tooltipText">
    <span class="session-label">Reddit</span>
    <span class="session-dot" :class="dotClass" aria-hidden="true" />
    <span class="session-age">{{ ageText }}</span>
    <button
      class="session-refresh"
      :disabled="refreshing"
      :aria-label="refreshing ? 'Refreshing session…' : 'Refresh Reddit session'"
      @click="doRefresh"
    >
      <span :class="{ spinning: refreshing }">↻</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api } from '../services/api'
import type { SessionStatus } from '../services/api'
import { useToast } from '../composables/useToast'

const { success, error } = useToast()

const status = ref<SessionStatus | null>(null)
const refreshing = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

const dotClass = computed(() => {
  if (!status.value || typeof status.value !== 'object') return 'dot--unknown'
  if (!status.value.valid) return 'dot--bad'
  const age = status.value.age_hours ?? 0
  if (age >= 8) return 'dot--warn'
  return 'dot--ok'
})

const ageText = computed(() => {
  if (!status.value || typeof status.value !== 'object') return '—'
  const age = status.value.age_hours
  if (age == null) return 'none'
  return `${age.toFixed(1)}h`
})

const tooltipText = computed(() => {
  if (!status.value) return 'Session status unknown'
  if (!status.value.valid) return 'Reddit session expired — click ↻ to refresh'
  return `Session valid · ${ageText.value} old · ${status.value.session_file}`
})

async function fetchStatus() {
  try {
    status.value = await api.reddit.sessionStatus()
  } catch {
    // non-critical — widget just shows unknown state
  }
}

async function doRefresh() {
  refreshing.value = true
  try {
    await api.reddit.refreshSession()
    await fetchStatus()
    success('Reddit session refreshed')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Refresh failed'
    error(`Session refresh failed: ${msg}`)
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  fetchStatus()
  pollTimer = setInterval(fetchStatus, 60_000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.session-widget {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  margin: 8px 8px 0;
  border-radius: 8px;
  background: var(--color-bg-lift);
  border: 1px solid var(--color-border);
  font-size: 0.75rem;
  color: var(--color-text-muted);
  user-select: none;
}

.session-label {
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.session-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: background 0.3s;
}
.dot--ok      { background: var(--color-success, #3ecf8e); }
.dot--warn    { background: var(--color-warning, #f0b429); }
.dot--bad     { background: var(--color-danger,  #f26b6b); }
.dot--unknown { background: var(--color-text-dim); }

.session-age {
  flex: 1;
  font-family: var(--font-mono);
  font-size: 0.7rem;
}

.session-refresh {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 0 2px;
  line-height: 1;
  border-radius: 4px;
  transition: color 0.15s, background 0.15s;
}
.session-refresh:hover:not(:disabled) {
  color: var(--color-text);
  background: var(--color-bg-card);
}
.session-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}
</style>
