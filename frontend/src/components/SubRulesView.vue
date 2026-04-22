<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Sub / Channel Rules</h1>
      <button class="btn btn-primary" @click="showAdd = true">+ Add Sub</button>
    </div>

    <div class="card" style="padding: 0; overflow: hidden;">
      <table class="table table-responsive">
        <thead>
          <tr>
            <th>Sub / Channel</th>
            <th>Platform</th>
            <th>Flair</th>
            <th>Promo</th>
            <th>Rule Warning</th>
            <th>Notes</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rules" :key="r.id">
            <td data-label="Sub" style="font-weight: 500;">{{ r.sub }}</td>
            <td data-label="Platform"><span class="badge badge-muted">{{ r.platform }}</span></td>
            <td data-label="Flair">
              <span v-if="r.flair_required">{{ r.flair_to_use ?? '(required, unknown)' }}</span>
              <span v-else style="color: var(--color-text-muted);">—</span>
            </td>
            <td data-label="Promo">
              <span v-if="r.promo_allowed === null" class="badge badge-muted">unknown</span>
              <span v-else-if="r.promo_allowed" class="badge badge-success">allowed</span>
              <span v-else class="badge badge-danger">banned</span>
            </td>
            <td data-label="Rule Warning">
              <span v-if="r.rule_warning" class="badge badge-warning">yes</span>
              <span v-else style="color: var(--color-text-muted);">—</span>
            </td>
            <td data-label="Notes" style="color: var(--color-text-muted); max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              {{ r.notes ?? '—' }}
            </td>
            <td data-label="">
              <button class="btn btn-ghost btn-sm" @click="startEdit(r)">Edit</button>
            </td>
          </tr>
          <tr v-if="rules.length === 0">
            <td colspan="7" class="empty-state">No rules on record.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add/Edit modal -->
    <div v-if="showAdd || editing" class="modal-backdrop" @click.self="closeModal">
      <div class="modal card" style="width: 480px;">
        <h2 style="margin-bottom: var(--spacing-md); font-size: 16px;">
          {{ editing ? `Edit r/${editing.sub}` : 'Add Sub / Channel' }}
        </h2>
        <div v-if="!editing" class="form-group">
          <label class="form-label">Subreddit / channel name</label>
          <input class="form-input" v-model="form.sub" placeholder="selfhosted" />
        </div>
        <div v-if="!editing" class="form-group">
          <label class="form-label">Platform</label>
          <select class="form-select" v-model="form.platform">
            <option value="reddit">Reddit</option>
            <option value="facebook">Facebook</option>
            <option value="discord">Discord</option>
            <option value="lemmy">Lemmy</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Flair required?</label>
          <select class="form-select" v-model="form.flair_required">
            <option :value="false">No</option>
            <option :value="true">Yes</option>
          </select>
        </div>
        <div v-if="form.flair_required" class="form-group">
          <label class="form-label">Flair to use</label>
          <input class="form-input" v-model="form.flair_to_use" placeholder="Action / DIY / Activism" />
        </div>
        <div class="form-group">
          <label class="form-label">Promo allowed?</label>
          <select class="form-select" v-model="form.promo_allowed">
            <option :value="null">Unknown</option>
            <option :value="true">Yes</option>
            <option :value="false">Hard ban — skip</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Shows rule-warning dialog?</label>
          <select class="form-select" v-model="form.rule_warning">
            <option :value="false">No</option>
            <option :value="true">Yes</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Notes</label>
          <textarea class="form-textarea" v-model="form.notes" rows="2" placeholder="Any posting quirks..." />
        </div>
        <div style="display: flex; gap: var(--spacing-sm); justify-content: flex-end;">
          <button class="btn btn-ghost" @click="closeModal">Cancel</button>
          <button class="btn btn-primary" @click="save" :disabled="!editing && !form.sub">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, type SubRules } from '@/services/api'

const rules = ref<SubRules[]>([])
const showAdd = ref(false)
const editing = ref<SubRules | null>(null)

const form = reactive({
  sub: '',
  platform: 'reddit',
  flair_required: false,
  flair_to_use: '',
  promo_allowed: null as boolean | null,
  rule_warning: false,
  notes: '',
})

onMounted(async () => {
  rules.value = await api.subs.listRules()
})

function startEdit(r: SubRules) {
  editing.value = r
  Object.assign(form, {
    sub: r.sub,
    platform: r.platform,
    flair_required: !!r.flair_required,
    flair_to_use: r.flair_to_use ?? '',
    promo_allowed: r.promo_allowed === null ? null : !!r.promo_allowed,
    rule_warning: !!r.rule_warning,
    notes: r.notes ?? '',
  })
}

function closeModal() {
  showAdd.value = false
  editing.value = null
  Object.assign(form, { sub: '', platform: 'reddit', flair_required: false, flair_to_use: '', promo_allowed: null, rule_warning: false, notes: '' })
}

async function save() {
  const sub = editing.value ? editing.value.sub : form.sub
  const platform = editing.value ? editing.value.platform : form.platform
  const updated = await api.subs.upsertRules(sub, {
    flair_required: form.flair_required,
    flair_to_use: form.flair_to_use || null,
    promo_allowed: form.promo_allowed,
    rule_warning: form.rule_warning,
    notes: form.notes || null,
  }, platform)
  const idx = rules.value.findIndex(r => r.sub === sub && r.platform === platform)
  if (idx !== -1) {
    rules.value = [...rules.value.slice(0, idx), updated, ...rules.value.slice(idx + 1)]
  } else {
    rules.value = [...rules.value, updated]
  }
  closeModal()
}
</script>

<style scoped>
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { padding: var(--spacing-lg); }
</style>
