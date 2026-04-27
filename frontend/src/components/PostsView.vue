<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Post History</h1>
    </div>

    <div class="card" style="padding: 0; overflow: hidden;">
      <table class="table table-responsive">
        <thead>
          <tr>
            <th>Campaign</th>
            <th>Target</th>
            <th>Status</th>
            <th>Triggered by</th>
            <th>When</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in posts" :key="p.id">
            <td data-label="Campaign">{{ campaignName(p.campaign_id) }}</td>
            <td data-label="Target">{{ p.target }}</td>
            <td data-label="Status">
              <span :class="['status-dot', p.status]"></span>{{ p.status }}
              <span v-if="p.error_msg" :title="p.error_msg" style="color: var(--color-danger); cursor: help;"> ⚠</span>
            </td>
            <td data-label="Triggered by"><span class="badge badge-muted">{{ p.triggered_by }}</span></td>
            <td data-label="When" style="color: var(--color-text-muted); font-size: 12px;">{{ formatDate(p.posted_at) }}</td>
            <td data-label="Link">
              <a v-if="p.url" :href="p.url" target="_blank" style="color: var(--color-primary); font-size: 12px;">view →</a>
              <span v-else style="color: var(--color-text-muted);">—</span>
            </td>
          </tr>
          <tr v-if="posts.length === 0">
            <td colspan="6" class="empty-state">No posts yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { usePostStore, useCampaignStore } from '@/stores/campaigns'

const postStore = usePostStore()
const campaignStore = useCampaignStore()
const posts = postStore.posts

onMounted(async () => {
  await Promise.all([
    postStore.fetchPosts(undefined, undefined, 100),
    campaignStore.fetchCampaigns(),
  ])
})

function campaignName(id: number | null) {
  if (id === null) return 'manual'
  return campaignStore.campaigns.find(c => c.id === id)?.name ?? `#${id}`
}

function formatDate(iso: string) {
  const d = new Date(iso + 'Z')
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>
