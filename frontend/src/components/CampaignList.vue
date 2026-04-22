<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Campaigns</h1>
      <button class="btn btn-primary" @click="showCreate = true">+ New Campaign</button>
    </div>

    <div v-if="store.loading" class="empty-state">Loading...</div>
    <div v-else-if="store.error" class="empty-state" style="color: var(--color-danger)">{{ store.error }}</div>
    <div v-else-if="store.campaigns.length === 0" class="empty-state">
      No campaigns yet. Create one to get started.
    </div>

    <div v-else class="card" style="padding: 0; overflow: hidden;">
      <table class="table table-responsive">
        <thead>
          <tr>
            <th>Name</th>
            <th>Product</th>
            <th>Schedule</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in store.campaigns" :key="c.id">
            <td data-label="Name">
              <router-link :to="`/campaigns/${c.id}`" style="color: var(--color-primary); text-decoration: none; font-weight: 500;">
                {{ c.name }}
              </router-link>
            </td>
            <td data-label="Product"><span class="badge badge-info">{{ c.product }}</span></td>
            <td data-label="Schedule" class="text-mono text-sm text-muted">
              {{ c.cron_schedule ?? '— manual' }}
            </td>
            <td data-label="Status">
              <span :class="['badge', c.active ? 'badge-success' : 'badge-muted']">
                {{ c.active ? 'active' : 'paused' }}
              </span>
            </td>
            <td data-label="">
              <div style="display: flex; gap: 6px; justify-content: flex-end;">
                <button class="btn btn-ghost btn-sm" @click="toggle(c)" :title="c.active ? 'Pause' : 'Resume'">
                  {{ c.active ? '⏸' : '▶' }}
                </button>
                <button class="btn btn-primary btn-sm" @click="trigger(c)" :disabled="triggering === c.id">
                  {{ triggering === c.id ? '...' : 'Run' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate = false">
      <div class="modal card" style="width: 480px;">
        <h2 style="margin-bottom: var(--spacing-md); font-size: 16px;">New Campaign</h2>
        <div class="form-group">
          <label class="form-label">Name</label>
          <input class="form-input" v-model="form.name" placeholder="Kiwi food waste launch" />
        </div>
        <div class="form-group">
          <label class="form-label">Product</label>
          <select class="form-select" v-model="form.product">
            <option value="kiwi">kiwi</option>
            <option value="peregrine">peregrine</option>
            <option value="snipe">snipe</option>
            <option value="circuitforge">circuitforge</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Cron schedule <span style="color: var(--color-text-muted)">(optional — blank = manual)</span></label>
          <input class="form-input" v-model="form.cron_schedule" placeholder="0 9 * * 2  (Tues 9 AM)" style="font-family: var(--font-mono);" />
        </div>
        <div class="form-group">
          <label class="form-label">Notes</label>
          <textarea class="form-textarea" v-model="form.notes" rows="2" placeholder="Internal notes..." />
        </div>
        <div style="display: flex; gap: var(--spacing-sm); justify-content: flex-end;">
          <button class="btn btn-ghost" @click="showCreate = false">Cancel</button>
          <button class="btn btn-primary" @click="create" :disabled="!form.name || !form.product">Create</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useCampaignStore } from '@/stores/campaigns'

const store = useCampaignStore()
const showCreate = ref(false)
const triggering = ref<number | null>(null)

const form = reactive({ name: '', product: 'kiwi', cron_schedule: '', notes: '' })

onMounted(() => store.fetchCampaigns())

async function create() {
  await store.createCampaign({
    name: form.name,
    product: form.product,
    cron_schedule: form.cron_schedule || null,
    notes: form.notes || null,
  })
  showCreate.value = false
  Object.assign(form, { name: '', product: 'kiwi', cron_schedule: '', notes: '' })
}

async function toggle(c: { id: number; active: number }) {
  await store.updateCampaign(c.id, { active: !c.active })
}

async function trigger(c: { id: number }) {
  triggering.value = c.id
  try {
    await store.triggerCampaign(c.id)
  } finally {
    triggering.value = null
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal { padding: var(--spacing-lg); }
</style>
