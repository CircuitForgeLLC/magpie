<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Signal Queue</h1>
      <div style="display: flex; gap: var(--spacing-sm);">
        <select class="form-select" v-model="filterStatus" style="width: auto; font-size: 13px;">
          <option value="">All</option>
          <option value="new">New</option>
          <option value="saved">Saved</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <button class="btn btn-ghost btn-sm" @click="showRules = true">⚙ Rules</button>
      </div>
    </div>

    <div v-if="loading" class="empty-state">Loading...</div>
    <div v-else-if="error" class="empty-state" style="color: var(--color-danger)">{{ error }}</div>
    <div v-else-if="filtered.length === 0" class="empty-state">
      {{ filterStatus ? `No ${filterStatus} signals.` : 'No signals yet — add monitoring rules and run the scraper.' }}
    </div>

    <div v-else class="signal-feed">
      <div
        v-for="s in filtered"
        :key="s.id"
        class="signal-card"
        :class="{ 'is-dismissed': s.status === 'dismissed', 'is-saved': s.status === 'saved' }"
      >
        <div class="signal-header">
          <div class="signal-chips">
            <span class="chip chip-sub">{{ s.sub }}</span>
            <span v-if="s.score !== null" class="chip chip-score">↑{{ s.score }}</span>
            <span v-if="s.comment_count !== null" class="chip chip-comments">{{ s.comment_count }}c</span>
            <span v-for="kw in s.matched_keywords" :key="kw" class="chip chip-kw">{{ kw }}</span>
          </div>
          <div class="signal-actions">
            <button
              v-if="s.status !== 'saved'"
              class="btn btn-ghost btn-xs"
              title="Save"
              @click.stop="updateStatus(s, 'saved')"
            >★</button>
            <button
              v-if="s.status !== 'dismissed'"
              class="btn btn-ghost btn-xs"
              title="Dismiss"
              @click.stop="updateStatus(s, 'dismissed')"
            >✕</button>
            <button
              v-if="s.status === 'dismissed'"
              class="btn btn-ghost btn-xs"
              title="Restore"
              @click.stop="updateStatus(s, 'new')"
            >↩</button>
          </div>
        </div>

        <a
          v-if="s.url"
          :href="s.url"
          target="_blank"
          class="signal-title"
        >{{ s.title }}</a>
        <div v-else class="signal-title" style="cursor: default;">{{ s.title }}</div>

        <p v-if="s.body_snippet" class="signal-snippet">{{ s.body_snippet }}</p>

        <div class="signal-footer">
          <span class="signal-author">u/{{ s.author ?? '?' }}</span>
          <span class="signal-date">{{ formatDate(s.surfaced_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Signal rules panel -->
    <div v-if="showRules" class="modal-backdrop" @click.self="showRules = false">
      <div class="modal card" style="width: 560px; max-height: 85vh; overflow-y: auto;">
        <h2 style="margin-bottom: var(--spacing-md); font-size: 16px;">Signal Monitoring Rules</h2>

        <div v-if="rules.length === 0" class="empty-state" style="padding: var(--spacing-md);">
          No rules. Add one to start monitoring communities.
        </div>

        <div v-for="r in rules" :key="r.id" class="rule-row">
          <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
            <span style="font-weight: 500; font-size: 13px;">{{ r.name }}</span>
            <span v-if="r.sub" class="chip chip-sub" style="font-size: 10px;">{{ r.sub }}</span>
            <span v-if="r.label" class="chip" :class="`chip-label-${r.label}`" style="font-size: 10px;">{{ r.label }}</span>
            <div style="margin-left: auto; display: flex; align-items: center; gap: 4px;">
              <span v-if="!r.active" class="badge badge-muted" style="font-size: 10px;">paused</span>
              <button class="btn btn-ghost btn-xs" :title="r.active ? 'Pause' : 'Resume'" @click="toggleRule(r)">{{ r.active ? '⏸' : '▶' }}</button>
              <button class="btn btn-ghost btn-xs" style="color: var(--color-danger);" title="Delete" @click="deleteRule(r.id)">✕</button>
            </div>
          </div>
          <div class="rule-keywords">
            <code v-for="kw in r.keywords" :key="kw" class="kw-tag">{{ kw }}</code>
            <span v-if="r.keywords.length === 0" style="color: var(--color-text-muted); font-size: 11px;">no keywords — matches all posts</span>
          </div>
          <div style="font-size: 11px; color: var(--color-text-muted);">
            {{ r.match_mode }} match · min score {{ r.min_score }}
          </div>
        </div>

        <div style="border-top: 1px solid var(--color-border); margin-top: var(--spacing-md); padding-top: var(--spacing-md);">
          <div style="font-size: 13px; font-weight: 500; margin-bottom: var(--spacing-sm);">New rule</div>
          <div class="form-group">
            <label class="form-label">Name</label>
            <input class="form-input" v-model="ruleForm.name" placeholder="Kiwi pain points" />
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-sm);">
            <div class="form-group">
              <label class="form-label">Sub (blank = all)</label>
              <input class="form-input" v-model="ruleForm.sub" placeholder="selfhosted" />
            </div>
            <div class="form-group">
              <label class="form-label">Label</label>
              <select class="form-select" v-model="ruleForm.label">
                <option value="">— none —</option>
                <option value="pain-point">pain-point</option>
                <option value="feedback">feedback</option>
                <option value="mention">mention</option>
                <option value="trust">trust</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Keywords (comma-separated)</label>
            <input class="form-input" v-model="ruleForm.keywordsRaw" placeholder="food waste, expiry, pantry" style="font-family: var(--font-mono);" />
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-sm);">
            <div class="form-group">
              <label class="form-label">Match mode</label>
              <select class="form-select" v-model="ruleForm.match_mode">
                <option value="any">any keyword</option>
                <option value="all">all keywords</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Min score</label>
              <input class="form-input" type="number" v-model.number="ruleForm.min_score" min="0" />
            </div>
          </div>
        </div>

        <div style="display: flex; gap: var(--spacing-sm); justify-content: flex-end; margin-top: var(--spacing-sm);">
          <button class="btn btn-ghost" @click="showRules = false">Close</button>
          <button class="btn btn-primary" @click="addRule" :disabled="!ruleForm.name">Add Rule</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { api, type Signal, type SignalStatus, type SignalRule } from '@/services/api'

const signals = ref<Signal[]>([])
const rules = ref<SignalRule[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const filterStatus = ref<SignalStatus | ''>('')
const showRules = ref(false)

const ruleForm = reactive({
  name: '',
  sub: '',
  label: '' as '' | 'pain-point' | 'feedback' | 'mention' | 'trust',
  keywordsRaw: '',
  match_mode: 'any' as 'any' | 'all',
  min_score: 0,
})

const filtered = computed(() =>
  filterStatus.value
    ? signals.value.filter(s => s.status === filterStatus.value)
    : signals.value
)

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const [sigs, rls] = await Promise.all([
      api.signals.list(),
      api.signalRules.list(),
    ])
    signals.value = sigs
    rules.value = rls
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load signals'
  } finally {
    loading.value = false
  }
})

async function updateStatus(s: Signal, status: SignalStatus) {
  const updated = await api.signals.updateStatus(s.id, status)
  const idx = signals.value.findIndex(x => x.id === s.id)
  if (idx >= 0) signals.value[idx] = updated
}

async function addRule() {
  const keywords = ruleForm.keywordsRaw
    .split(',')
    .map(k => k.trim())
    .filter(Boolean)
  const rule = await api.signalRules.create({
    name: ruleForm.name,
    sub: ruleForm.sub || null,
    label: ruleForm.label || null,
    keywords,
    match_mode: ruleForm.match_mode,
    min_score: ruleForm.min_score,
  })
  rules.value = [...rules.value, rule]
  Object.assign(ruleForm, { name: '', sub: '', label: '', keywordsRaw: '', match_mode: 'any', min_score: 0 })
}

async function toggleRule(r: SignalRule) {
  const updated = await api.signalRules.update(r.id, { active: !r.active })
  const idx = rules.value.findIndex(x => x.id === r.id)
  if (idx >= 0) rules.value[idx] = updated
}

async function deleteRule(id: number) {
  await api.signalRules.delete(id)
  rules.value = rules.value.filter(r => r.id !== id)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.signal-feed {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.signal-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  transition: border-color 0.15s;
}
.signal-card:hover { border-color: var(--color-primary); }
.signal-card.is-dismissed { opacity: 0.45; }
.signal-card.is-saved { border-left: 3px solid var(--color-primary); }

.signal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.signal-chips { display: flex; flex-wrap: wrap; gap: 4px; }

.chip {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}
.chip-sub { color: var(--color-primary); border-color: var(--color-primary); }
.chip-score { color: var(--color-success); border-color: var(--color-success); }
.chip-comments { color: var(--color-text-muted); }
.chip-kw { color: var(--color-warning); border-color: var(--color-warning); }
.chip-label-pain-point { color: var(--color-danger); border-color: var(--color-danger); }
.chip-label-feedback { color: var(--color-info); border-color: var(--color-info); }
.chip-label-mention { color: var(--color-primary); border-color: var(--color-primary); }
.chip-label-trust { color: var(--color-success); border-color: var(--color-success); }

.signal-actions { display: flex; gap: 2px; flex-shrink: 0; }

.btn-xs {
  padding: 2px 6px;
  font-size: 11px;
  min-height: 24px;
}

.signal-title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  text-decoration: none;
  margin-bottom: var(--spacing-xs);
  line-height: 1.4;
}
a.signal-title:hover { color: var(--color-primary); }

.signal-snippet {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0 0 var(--spacing-xs);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.signal-footer {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

/* Rules panel */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal { padding: var(--spacing-lg); }

.rule-row {
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rule-row:last-of-type { border-bottom: none; }

.rule-keywords { display: flex; flex-wrap: wrap; gap: 4px; }

.kw-tag {
  font-size: 10px;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  border-radius: var(--radius-sm);
  padding: 1px 6px;
  font-family: var(--font-mono);
}

@media (max-width: 640px) {
  .modal { width: calc(100vw - 2 * var(--spacing-md)) !important; }
}
</style>
