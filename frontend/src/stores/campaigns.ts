import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, type Campaign, type Variant, type CampaignSub, type Post } from '@/services/api'

export const useCampaignStore = defineStore('campaigns', () => {
  const campaigns = ref<Campaign[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCampaigns(activeOnly = false) {
    loading.value = true
    error.value = null
    try {
      campaigns.value = await api.campaigns.list(activeOnly)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load campaigns'
    } finally {
      loading.value = false
    }
  }

  async function createCampaign(data: Parameters<typeof api.campaigns.create>[0]) {
    const created = await api.campaigns.create(data)
    campaigns.value.push(created)
    return created
  }

  async function updateCampaign(id: number, data: Parameters<typeof api.campaigns.update>[1]) {
    const updated = await api.campaigns.update(id, data)
    const idx = campaigns.value.findIndex(c => c.id === id)
    if (idx !== -1) campaigns.value = [...campaigns.value.slice(0, idx), updated, ...campaigns.value.slice(idx + 1)]
    return updated
  }

  async function deleteCampaign(id: number) {
    await api.campaigns.delete(id)
    campaigns.value = campaigns.value.filter(c => c.id !== id)
  }

  async function triggerCampaign(id: number) {
    return api.campaigns.trigger(id)
  }

  return { campaigns, loading, error, fetchCampaigns, createCampaign, updateCampaign, deleteCampaign, triggerCampaign }
})

export const usePostStore = defineStore('posts', () => {
  const posts = ref<Post[]>([])
  const loading = ref(false)

  async function fetchPosts(campaignId?: number, target?: string, limit = 50) {
    loading.value = true
    try {
      posts.value = await api.posts.list(campaignId, target, limit)
    } finally {
      loading.value = false
    }
  }

  return { posts, loading, fetchPosts }
})
