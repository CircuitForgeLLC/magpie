<template>
  <div v-if="campaign">
    <div class="page-header">
      <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
        <router-link to="/campaigns" style="color: var(--color-text-muted); text-decoration: none;">← Campaigns</router-link>
        <span style="color: var(--color-border);">/</span>
        <h1 class="page-title">{{ campaign.name }}</h1>
        <span class="badge badge-info">{{ campaign.product }}</span>
      </div>
      <button class="btn btn-primary" @click="triggerAll" :disabled="triggering">
        {{ triggering ? 'Running...' : '▶ Run All Subs' }}
      </button>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-lg);">
      <!-- Left: variants + subs -->
      <div>
        <!-- Variants -->
        <div class="card" style="margin-bottom: var(--spacing-lg);">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--spacing-md);">
            <div class="card-title" style="margin: 0;">Content Variants</div>
            <button class="btn btn-ghost btn-sm" @click="showAddVariant = true">+ Variant</button>
          </div>
          <div v-if="variants.length === 0" class="empty-state" style="padding: var(--spacing-md);">
            No variants. Add a default (*) variant to start posting.
          </div>
          <div v-for="v in variants" :key="v.id" class="variant-row">
            <div style="display: flex; align-items: center; gap: var(--spacing-sm); margin-bottom: 4px;">
              <code style="font-size: 11px; color: var(--color-primary); background: var(--color-primary-dim); padding: 1px 6px; border-radius: 4px;">{{ v.sub_pattern }}</code>
              <span v-if="v.flair" style="font-size: 11px; color: var(--color-text-muted);">flair: {{ v.flair }}</span>
              <button class="btn btn-ghost btn-sm" style="margin-left: auto;" @click="deleteVariant(v.id)">✕</button>
            </div>
            <div style="font-weight: 500; font-size: 13px; margin-bottom: 2px;">{{ v.title }}</div>
            <div style="color: var(--color-text-muted); font-size: 12px; white-space: pre-wrap; max-height: 60px; overflow: hidden;">{{ v.body }}</div>
          </div>
        </div>

        <!-- Subs -->
        <div class="card">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--spacing-md);">
            <div class="card-title" style="margin: 0;">Target Subreddits</div>
            <button class="btn btn-ghost btn-sm" @click="showAddSub = true">+ Sub</button>
          </div>
          <div v-for="s in campaignSubs" :key="s.id" style="display: flex; align-items: center; gap: var(--spacing-sm); padding: 6px 0; border-bottom: 1px solid var(--color-border);">
            <span>r/{{ s.sub }}</span>
            <button class="btn btn-ghost btn-sm" style="margin-left: auto; color: var(--color-danger);" @click="removeSub(s.sub)">✕</button>
          </div>
          <div v-if="campaignSubs.length === 0" class="empty-state" style="padding: var(--spacing-md);">No subs configured.</div>
        </div>
      </div>

      <!-- Right: recent posts -->
      <div class="card" style="padding: 0; overflow: hidden; align-self: start;">
        <div class="card-title" style="padding: var(--spacing-md) var(--spacing-md) 0;">Recent Posts</div>
        <table class="table">
          <thead>
            <tr>
              <th>Sub</th>
              <th>Status</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in recentPosts" :key="p.id">
              <td>r/{{ p.target }}</td>
              <td>
                <span :class="['status-dot', p.status]"></span>
                <a v-if="p.url" :href="p.url" target="_blank" style="color: var(--color-primary); text-decoration: none;">{{ p.status }}</a>
                <span v-else>{{ p.status }}</span>
              </td>
              <td style="color: var(--color-text-muted); font-size: 12px;">{{ formatDate(p.posted_at) }}</td>
            </tr>
            <tr v-if="recentPosts.length === 0">
              <td colspan="3" style="color: var(--color-text-muted); text-align: center; padding: var(--spacing-lg);">No posts yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add variant modal -->
    <div v-if="showAddVariant" class="modal-backdrop" @click.self="showAddVariant = false">
      <div class="modal card" style="width: 600px; max-height: 90vh; overflow-y: auto;">
        <h2 style="margin-bottom: var(--spacing-md); font-size: 16px;">Add Variant</h2>
        <div class="form-group">
          <label class="form-label">Sub pattern <span style="color: var(--color-text-muted)">(* = default, exact sub name, or prefix*)</span></label>
          <input class="form-input" v-model="variantForm.sub_pattern" placeholder="*" style="font-family: var(--font-mono);" />
        </div>
        <div class="form-group">
          <label class="form-label">Flair (optional)</label>
          <input class="form-input" v-model="variantForm.flair" placeholder="Action / DIY / Activism" />
        </div>
        <div class="form-group">
          <label class="form-label">Title</label>
          <input class="form-input" v-model="variantForm.title" placeholder="Post title..." />
        </div>
        <div class="form-group">
          <label class="form-label">Body</label>
          <textarea class="form-textarea" v-model="variantForm.body" rows="8" placeholder="Post body (markdown)..." style="min-height: 200px;" />
        </div>
        <div class="form-group">
          <label class="form-label">Internal notes</label>
          <input class="form-input" v-model="variantForm.notes" placeholder="Framing angle, tone notes..." />
        </div>
        <div style="display: flex; gap: var(--spacing-sm); justify-content: flex-end;">
          <button class="btn btn-ghost" @click="showAddVariant = false">Cancel</button>
          <button class="btn btn-primary" @click="addVariant" :disabled="!variantForm.title || !variantForm.body">Add Variant</button>
        </div>
      </div>
    </div>

    <!-- Add sub modal -->
    <div v-if="showAddSub" class="modal-backdrop" @click.self="showAddSub = false">
      <div class="modal card" style="width: 360px;">
        <h2 style="margin-bottom: var(--spacing-md); font-size: 16px;">Add Subreddit</h2>
        <div class="form-group">
          <label class="form-label">Subreddit name (without r/)</label>
          <input class="form-input" v-model="subForm.sub" placeholder="selfhosted" />
        </div>
        <div style="display: flex; gap: var(--spacing-sm); justify-content: flex-end;">
          <button class="btn btn-ghost" @click="showAddSub = false">Cancel</button>
          <button class="btn btn-primary" @click="addSub" :disabled="!subForm.sub">Add</button>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="empty-state">Loading campaign...</div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, type Campaign, type Variant, type CampaignSub, type Post } from '@/services/api'

const route = useRoute()
const campaignId = Number(route.params.id)

const campaign = ref<Campaign | null>(null)
const variants = ref<Variant[]>([])
const campaignSubs = ref<CampaignSub[]>([])
const recentPosts = ref<Post[]>([])
const triggering = ref(false)
const showAddVariant = ref(false)
const showAddSub = ref(false)

const variantForm = reactive({ sub_pattern: '*', title: '', body: '', flair: '', notes: '' })
const subForm = reactive({ sub: '' })

onMounted(async () => {
  const [c, v, s, p] = await Promise.all([
    api.campaigns.get(campaignId),
    api.variants.list(campaignId),
    api.subs.listForCampaign(campaignId),
    api.posts.list(campaignId, undefined, 20),
  ])
  campaign.value = c
  variants.value = v
  campaignSubs.value = s
  recentPosts.value = p
})

async function triggerAll() {
  triggering.value = true
  try {
    await api.campaigns.trigger(campaignId)
    recentPosts.value = await api.posts.list(campaignId, undefined, 20)
  } finally {
    triggering.value = false
  }
}

async function addVariant() {
  const v = await api.variants.create(campaignId, {
    sub_pattern: variantForm.sub_pattern || '*',
    title: variantForm.title,
    body: variantForm.body,
    flair: variantForm.flair || null,
    notes: variantForm.notes || null,
  })
  variants.value = [...variants.value, v]
  showAddVariant.value = false
  Object.assign(variantForm, { sub_pattern: '*', title: '', body: '', flair: '', notes: '' })
}

async function deleteVariant(id: number) {
  await api.variants.delete(campaignId, id)
  variants.value = variants.value.filter(v => v.id !== id)
}

async function addSub() {
  const s = await api.subs.add(campaignId, subForm.sub)
  campaignSubs.value = [...campaignSubs.value, s]
  showAddSub.value = false
  subForm.sub = ''
}

async function removeSub(sub: string) {
  await api.subs.remove(campaignId, sub)
  campaignSubs.value = campaignSubs.value.filter(s => s.sub !== sub)
}

function formatDate(iso: string) {
  const d = new Date(iso + 'Z')
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { padding: var(--spacing-lg); }
.variant-row { padding: var(--spacing-sm); border-bottom: 1px solid var(--color-border); }
.variant-row:last-child { border-bottom: none; }
</style>
