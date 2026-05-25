<template>
  <div class="toast-list" aria-live="polite" aria-atomic="false">
    <div
      v-for="t in toasts"
      :key="t.id"
      :class="['toast', `toast--${t.type}`]"
      role="alert"
    >
      <span class="toast-icon">{{ icons[t.type] }}</span>
      <span class="toast-message">{{ t.message }}</span>
      <button class="toast-close" @click="dismiss(t.id)" aria-label="Dismiss">✕</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '../composables/useToast'

const { toasts, dismiss } = useToast()
const icons = { error: '⚠️', success: '✓', info: 'ℹ' }
</script>

<style scoped>
.toast-list {
  position: fixed;
  bottom: calc(var(--bottom-nav-height, 60px) + 12px);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 9999;
  width: min(420px, 92vw);
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.4;
  box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  pointer-events: all;
  color: var(--color-text);
  background: var(--color-bg-card);
  border-left: 4px solid var(--color-border);
}
.toast--error  { border-color: var(--color-danger,  #e05252); }
.toast--success{ border-color: var(--color-success, #4caf7d); }
.toast--info   { border-color: var(--color-accent,  #5b7fa6); }

.toast-icon  { flex-shrink: 0; font-size: 1rem; }
.toast-message { flex: 1; }
.toast-close {
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted, #888);
  font-size: 0.8rem;
  padding: 0 2px;
  line-height: 1;
}
.toast-close:hover { color: var(--color-text); }

@media (min-width: 768px) {
  .toast-list {
    bottom: 20px;
    left: unset;
    right: 20px;
    transform: none;
  }
}
</style>
