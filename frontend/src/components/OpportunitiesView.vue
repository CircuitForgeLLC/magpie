<template>
  <div class="opportunities-view">
    <div class="view-header">
      <h1 class="view-title">Opportunities</h1>
      <div class="header-actions">
        <select v-model="filterStatus" class="status-filter">
          <option value="">All</option>
          <option value="pending_review">Pending review</option>
          <option value="approved">Approved</option>
          <option value="posted">Posted</option>
          <option value="manual_posted">Manual posted</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <button class="btn btn-primary" @click="showAddModal = true">+ Add</button>
      </div>
    </div>

    <div v-if="loading" class="state-empty">Loading...</div>
    <div v-else-if="loadError" class="state-empty" style="color: var(--color-danger)">
      Could not load opportunities: {{ loadError }}
    </div>
    <div v-else-if="filtered.length === 0" class="state-empty">
      No opportunities{{ filterStatus ? ` with status "${filterStatus}"` : '' }}.
    </div>

    <div v-else class="opp-list">
      <div
        v-for="opp in filtered"
        :key="opp.id"
        class="opp-card"
        :class="`status-${opp.status}`"
        @click="select(opp)"
      >
        <div class="opp-meta">
          <span class="opp-platform">{{ opp.platform }}</span>
          <span class="opp-community">{{ opp.community }}</span>
          <span class="opp-type">{{ opp.post_type === 'reply_to_thread' ? 'reply' : 'new post' }}</span>
          <span v-if="opp.product" class="opp-product">{{ opp.product }}</span>
        </div>
        <div class="opp-title">{{ opp.thread_title || opp.thread_url }}</div>
        <div v-if="opp.signal_reason" class="opp-signal">{{ opp.signal_reason }}</div>
        <div class="opp-footer">
          <span class="status-badge" :class="`badge-${opp.status}`">{{ opp.status.replace('_', ' ') }}</span>
          <span class="opp-date">{{ formatDate(opp.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Detail / review panel -->
    <div v-if="selected" class="detail-overlay" @click.self="selected = null">
      <div class="detail-panel">
        <button class="close-btn" @click="selected = null">✕</button>

        <div class="detail-header">
          <div class="opp-meta">
            <span class="opp-platform">{{ selected.platform }}</span>
            <span class="opp-community">{{ selected.community }}</span>
            <span class="opp-type">{{ selected.post_type === 'reply_to_thread' ? 'reply' : 'new post' }}</span>
          </div>
          <span class="status-badge" :class="`badge-${selected.status}`">{{ selected.status.replace('_', ' ') }}</span>
        </div>

        <!-- Thread context -->
        <section class="detail-section">
          <h3 class="section-label">Thread</h3>
          <a :href="selected.thread_url" target="_blank" class="thread-link">
            {{ selected.thread_title || selected.thread_url }}
          </a>
          <p v-if="selected.thread_body" class="thread-body">{{ selected.thread_body }}</p>
        </section>

        <section v-if="selected.signal_reason" class="detail-section">
          <h3 class="section-label">Why flagged</h3>
          <p class="signal-reason">{{ selected.signal_reason }}</p>
        </section>

        <!-- Draft editor -->
        <section class="detail-section">
          <h3 class="section-label">Draft {{ selected.post_type === 'new_post' ? 'post' : 'reply' }}</h3>
          <input
            v-if="selected.post_type === 'new_post'"
            v-model="editTitle"
            class="input draft-title-input"
            placeholder="Post title"
          />
          <textarea
            v-model="editBody"
            class="textarea draft-body"
            rows="10"
            placeholder="Draft content..."
          />
          <button
            v-if="editBody !== selected.draft_body || editTitle !== (selected.draft_title ?? '')"
            class="btn btn-secondary"
            :disabled="saving"
            @click="saveDraft"
          >
            Save draft
          </button>
        </section>

        <!-- Actions -->
        <section v-if="selected.status === 'pending_review'" class="detail-actions">
          <button class="btn btn-primary" :disabled="saving" @click="approve">
            Approve
          </button>
          <button class="btn btn-danger" :disabled="saving" @click="dismiss">
            Dismiss
          </button>
        </section>

        <!-- Handoff panel for approved non-Reddit -->
        <section v-if="selected.status === 'approved' && selected.platform !== 'reddit'" class="handoff-panel">
          <h3 class="section-label">Manual handoff</h3>
          <div class="handoff-actions">
            <button class="btn btn-secondary" @click="copyDraft">📋 Copy draft</button>
            <a :href="selected.thread_url" target="_blank" class="btn btn-secondary">🔗 Open thread</a>
            <button v-if="!confirmingPosted" class="btn btn-success" @click="confirmingPosted = true">
              ✓ Mark as posted
            </button>
          </div>
          <div v-if="copied" class="copy-confirm">Copied to clipboard</div>
          <div v-if="confirmingPosted" class="post-url-confirm">
            <input
              v-model="postedUrl"
              class="input"
              placeholder="Post URL (optional — paste link to your comment/post)"
              @keydown.enter="markManualPosted"
              @keydown.escape="confirmingPosted = false"
            />
            <div class="handoff-actions" style="margin-top: var(--spacing-xs);">
              <button class="btn btn-success" :disabled="saving" @click="markManualPosted">Confirm</button>
              <button class="btn btn-secondary" @click="confirmingPosted = false">Cancel</button>
            </div>
          </div>
        </section>

        <!-- Auto-post panel for approved Reddit -->
        <section v-if="selected.status === 'approved' && selected.platform === 'reddit'" class="handoff-panel">
          <h3 class="section-label">Ready to post</h3>
          <p class="handoff-note">Use trigger_sub_post from the Campaigns view, or mark as posted manually if you handled it.</p>
          <div v-if="!confirmingPosted">
            <button class="btn btn-success" @click="confirmingPosted = true">
              ✓ Mark as posted
            </button>
          </div>
          <div v-if="confirmingPosted" class="post-url-confirm">
            <input
              v-model="postedUrl"
              class="input"
              placeholder="Post URL (optional)"
              @keydown.enter="markManualPosted"
              @keydown.escape="confirmingPosted = false"
            />
            <div class="handoff-actions" style="margin-top: var(--spacing-xs);">
              <button class="btn btn-success" :disabled="saving" @click="markManualPosted">Confirm</button>
              <button class="btn btn-secondary" @click="confirmingPosted = false">Cancel</button>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Add opportunity modal -->
    <div v-if="showAddModal" class="detail-overlay" @click.self="showAddModal = false">
      <div class="detail-panel">
        <button class="close-btn" @click="showAddModal = false">✕</button>
        <h2 class="panel-title">Add opportunity</h2>

        <div class="form-grid">
          <label class="form-label">Thread URL
            <input v-model="newOpp.thread_url" class="input" placeholder="https://..." />
          </label>
          <label class="form-label">Platform
            <select v-model="newOpp.platform" class="input">
              <option>reddit</option>
              <option>lemmy</option>
              <option>linkedin</option>
              <option>other</option>
            </select>
          </label>
          <label class="form-label">Community
            <input v-model="newOpp.community" class="input" placeholder="selfhosted, lemmy.world/c/lsc, etc." />
          </label>
          <label class="form-label">Post type
            <select v-model="newOpp.post_type" class="input">
              <option value="reply_to_thread">Reply to thread</option>
              <option value="new_post">New post</option>
            </select>
          </label>
          <label class="form-label">Product
            <select v-model="newOpp.product" class="input">
              <option value="">— any —</option>
              <option>peregrine</option>
              <option>kiwi</option>
              <option>snipe</option>
              <option>circuitforge</option>
            </select>
          </label>
          <label class="form-label">Thread title (optional)
            <input v-model="newOpp.thread_title" class="input" placeholder="Original post title" />
          </label>
          <label class="form-label" style="grid-column: 1 / -1">Why flagged
            <input v-model="newOpp.signal_reason" class="input" placeholder="Pain point match, keyword, etc." />
          </label>
          <label class="form-label" style="grid-column: 1 / -1">Draft
            <textarea v-model="newOpp.draft_body" class="textarea" rows="6" placeholder="Draft reply or post body..." />
          </label>
        </div>

        <div class="detail-actions">
          <button class="btn btn-primary" :disabled="saving || !newOpp.thread_url || !newOpp.community" @click="createOpp">
            Add to queue
          </button>
          <button class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { api, type Opportunity, type OpportunityStatus } from '../services/api'

const opportunities = ref<Opportunity[]>([])
const loading = ref(false)
const saving = ref(false)
const selected = ref<Opportunity | null>(null)
const showAddModal = ref(false)
const copied = ref(false)
const filterStatus = ref<OpportunityStatus | ''>('')
const loadError = ref<string | null>(null)
const confirmingPosted = ref(false)
const postedUrl = ref('')

const editBody = ref('')
const editTitle = ref('')

const newOpp = ref({
  platform: 'reddit',
  community: '',
  thread_url: '',
  thread_title: '',
  signal_reason: '',
  product: '',
  draft_body: '',
  post_type: 'reply_to_thread' as const,
})

const filtered = computed(() =>
  filterStatus.value
    ? opportunities.value.filter(o => o.status === filterStatus.value)
    : opportunities.value
)

async function load() {
  loading.value = true
  loadError.value = null
  try {
    opportunities.value = await api.opportunities.list()
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : 'Failed to load opportunities'
  } finally {
    loading.value = false
  }
}

function select(opp: Opportunity) {
  selected.value = opp
  editBody.value = opp.draft_body
  editTitle.value = opp.draft_title ?? ''
  confirmingPosted.value = false
  postedUrl.value = ''
}

watch(selected, opp => {
  if (opp) {
    editBody.value = opp.draft_body
    editTitle.value = opp.draft_title ?? ''
  }
})

async function saveDraft() {
  if (!selected.value) return
  saving.value = true
  try {
    const updated = await api.opportunities.update(selected.value.id, {
      draft_body: editBody.value,
      draft_title: editTitle.value || undefined,
    })
    replace(updated)
  } finally {
    saving.value = false
  }
}

async function approve() {
  if (!selected.value) return
  saving.value = true
  try {
    // Save any unsaved draft edits first
    if (editBody.value !== selected.value.draft_body) {
      await api.opportunities.update(selected.value.id, { draft_body: editBody.value })
    }
    const result = await api.opportunities.approve(selected.value.id)
    replace(result.opportunity)
  } finally {
    saving.value = false
  }
}

async function dismiss() {
  if (!selected.value) return
  saving.value = true
  try {
    const updated = await api.opportunities.dismiss(selected.value.id)
    replace(updated)
  } finally {
    saving.value = false
  }
}

async function markManualPosted() {
  if (!selected.value) return
  saving.value = true
  try {
    const updated = await api.opportunities.markPosted(selected.value.id, true, postedUrl.value || null)
    replace(updated)
    confirmingPosted.value = false
    postedUrl.value = ''
  } finally {
    saving.value = false
  }
}

async function copyDraft() {
  if (!selected.value) return
  await navigator.clipboard.writeText(selected.value.draft_body)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function createOpp() {
  saving.value = true
  try {
    const created = await api.opportunities.create({
      ...newOpp.value,
      product: newOpp.value.product || undefined,
      thread_title: newOpp.value.thread_title || undefined,
      signal_reason: newOpp.value.signal_reason || undefined,
    })
    opportunities.value.unshift(created)
    showAddModal.value = false
    newOpp.value = { platform: 'reddit', community: '', thread_url: '', thread_title: '', signal_reason: '', product: '', draft_body: '', post_type: 'reply_to_thread' }
  } finally {
    saving.value = false
  }
}

function replace(updated: Opportunity) {
  const idx = opportunities.value.findIndex(o => o.id === updated.id)
  if (idx >= 0) opportunities.value[idx] = updated
  if (selected.value?.id === updated.id) selected.value = updated
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
.opportunities-view { padding: var(--spacing-lg); }

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.view-title { margin: 0; font-size: 1.4rem; color: var(--color-text); }

.header-actions { display: flex; gap: var(--spacing-sm); align-items: center; }

.status-filter {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.state-empty { color: var(--color-text-muted); text-align: center; padding: var(--spacing-xl); }

.opp-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }

.opp-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: border-color 0.15s;
}
.opp-card:hover { border-color: var(--color-primary); }
.opp-card.status-dismissed { opacity: 0.5; }

.opp-meta { display: flex; gap: var(--spacing-sm); align-items: center; margin-bottom: var(--spacing-xs); flex-wrap: wrap; }

.opp-platform, .opp-community, .opp-type, .opp-product {
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background: var(--color-bg-secondary);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
.opp-platform { color: var(--color-info); border-color: var(--color-info); }
.opp-community { color: var(--color-primary); border-color: var(--color-primary); }

.opp-title { font-size: 0.95rem; color: var(--color-text); margin-bottom: var(--spacing-xs); }
.opp-signal { font-size: 0.8rem; color: var(--color-text-muted); margin-bottom: var(--spacing-xs); font-style: italic; }

.opp-footer { display: flex; align-items: center; justify-content: space-between; }
.opp-date { font-size: 0.75rem; color: var(--color-text-muted); }

.status-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: capitalize;
  font-weight: 600;
}
.badge-pending_review { background: color-mix(in srgb, var(--color-warning) 15%, transparent); color: var(--color-warning); }
.badge-approved       { background: color-mix(in srgb, var(--color-primary) 15%, transparent); color: var(--color-primary); }
.badge-posted         { background: color-mix(in srgb, var(--color-success) 15%, transparent); color: var(--color-success); }
.badge-manual_posted  { background: color-mix(in srgb, var(--color-success) 15%, transparent); color: var(--color-success); }
.badge-dismissed      { background: color-mix(in srgb, var(--color-danger) 15%, transparent); color: var(--color-danger); }

/* Detail panel */
.detail-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: flex-start; justify-content: flex-end;
  z-index: 100;
  padding: var(--spacing-md);
}

.detail-panel {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  width: min(680px, 95vw);
  max-height: calc(100vh - 2 * var(--spacing-md));
  overflow-y: auto;
  padding: var(--spacing-lg);
  position: relative;
}

.close-btn {
  position: absolute; top: var(--spacing-md); right: var(--spacing-md);
  background: none; border: none; color: var(--color-text-muted);
  font-size: 1.1rem; cursor: pointer; padding: 4px;
}
.close-btn:hover { color: var(--color-text); }

.panel-title { margin: 0 0 var(--spacing-lg); font-size: 1.1rem; }

.detail-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.detail-section { margin-bottom: var(--spacing-lg); }

.section-label {
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--color-text-muted); margin: 0 0 var(--spacing-sm);
}

.thread-link {
  color: var(--color-info); text-decoration: none; font-size: 0.95rem;
  display: block; margin-bottom: var(--spacing-sm);
}
.thread-link:hover { text-decoration: underline; }

.thread-body {
  font-size: 0.85rem; color: var(--color-text-muted);
  background: var(--color-bg); border-radius: var(--radius-sm);
  padding: var(--spacing-sm); margin: 0;
  white-space: pre-wrap; max-height: 120px; overflow-y: auto;
}

.signal-reason { font-size: 0.85rem; color: var(--color-text-muted); margin: 0; font-style: italic; }

.draft-title-input { width: 100%; margin-bottom: var(--spacing-sm); }
.draft-body { width: 100%; resize: vertical; font-family: var(--font-mono); font-size: 0.85rem; }

.detail-actions { display: flex; gap: var(--spacing-sm); flex-wrap: wrap; margin-top: var(--spacing-md); }

.handoff-panel {
  background: color-mix(in srgb, var(--color-success) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-success) 30%, transparent);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.handoff-actions { display: flex; gap: var(--spacing-sm); flex-wrap: wrap; margin-top: var(--spacing-sm); }
.handoff-note { font-size: 0.85rem; color: var(--color-text-muted); margin: var(--spacing-xs) 0 0; }

.copy-confirm {
  font-size: 0.8rem; color: var(--color-success);
  margin-top: var(--spacing-xs);
}

.post-url-confirm {
  margin-top: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

/* Add form */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); }

.form-label {
  display: flex; flex-direction: column; gap: var(--spacing-xs);
  font-size: 0.8rem; color: var(--color-text-muted);
}

/* Shared */
.input, .textarea {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  font-size: 0.9rem;
  width: 100%;
  box-sizing: border-box;
}
.input:focus, .textarea:focus { outline: none; border-color: var(--color-primary); }

.btn {
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  font-size: 0.85rem;
  cursor: pointer;
  transition: opacity 0.15s;
  text-decoration: none;
  display: inline-block;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--color-primary); color: #fff; }
.btn-secondary { background: var(--color-bg-card); color: var(--color-text); border-color: var(--color-border); }
.btn-danger { background: color-mix(in srgb, var(--color-danger) 15%, transparent); color: var(--color-danger); border-color: var(--color-danger); }
.btn-success { background: color-mix(in srgb, var(--color-success) 15%, transparent); color: var(--color-success); border-color: var(--color-success); }
.btn:hover:not(:disabled) { opacity: 0.85; }

@media (max-width: 600px) {
  .form-grid { grid-template-columns: 1fr; }
  .detail-overlay { padding: 0; align-items: flex-end; }
  .detail-panel { width: 100%; border-radius: var(--radius-lg) var(--radius-lg) 0 0; max-height: 90vh; }
}
</style>
