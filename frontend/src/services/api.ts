import axios from 'axios'

const http = axios.create({ baseURL: `${import.meta.env.BASE_URL}api/v1` })

// ------------------------------------------------------------------ //
// Types
// ------------------------------------------------------------------ //

export interface Campaign {
  id: number
  name: string
  product: string
  platform: string
  cron_schedule: string | null
  active: number
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CampaignCreate {
  name: string
  product: string
  platform?: string
  cron_schedule?: string | null
  notes?: string | null
}

export interface CampaignUpdate {
  name?: string
  product?: string
  cron_schedule?: string | null
  active?: boolean
  notes?: string | null
}

export interface Variant {
  id: number
  campaign_id: number
  sub_pattern: string
  title: string
  body: string
  flair: string | null
  notes: string | null
  link_url: string | null
  created_at: string
  updated_at: string
}

export interface VariantCreate {
  sub_pattern?: string
  title: string
  body: string
  flair?: string | null
  notes?: string | null
  link_url?: string | null
}

export interface CampaignSub {
  id: number
  campaign_id: number
  sub: string
  sort_order: number
  active: number
}

export interface Post {
  id: number
  campaign_id: number | null
  variant_id: number | null
  platform: string
  target: string
  status: string
  url: string | null
  error_msg: string | null
  screenshot_path: string | null
  triggered_by: string
  posted_at: string
}

export interface SubRules {
  id: number
  platform: string
  sub: string
  flair_required: number
  flair_to_use: string | null
  promo_allowed: number | null
  rule_warning: number
  notes: string | null
  post_url: string | null
  last_checked: string | null
  updated_at: string
}

export interface SubRulesUpsert {
  flair_required?: boolean
  flair_to_use?: string | null
  promo_allowed?: boolean | null
  rule_warning?: boolean
  notes?: string | null
  post_url?: string | null
}

export type OpportunityStatus =
  | 'pending_review'
  | 'approved'
  | 'posted'
  | 'manual_posted'
  | 'dismissed'

export type PostType = 'reply_to_thread' | 'new_post'

export interface Opportunity {
  id: number
  platform: string
  community: string
  thread_url: string
  thread_title: string | null
  thread_body: string | null
  signal_reason: string | null
  product: string | null
  draft_title: string | null
  draft_body: string
  post_type: PostType
  status: OpportunityStatus
  campaign_id: number | null
  dismiss_note: string | null
  created_at: string
  updated_at: string
}

export interface OpportunityCreate {
  platform?: string
  community: string
  thread_url: string
  thread_title?: string | null
  thread_body?: string | null
  signal_reason?: string | null
  product?: string | null
  draft_title?: string | null
  draft_body?: string
  post_type?: PostType
  campaign_id?: number | null
}

export interface ApproveResult {
  type: 'auto_post_ready' | 'manual_handoff'
  opportunity: Opportunity
  draft_body?: string
  thread_url?: string
  instructions: string
}

export type SignalMatchMode = 'any' | 'all' | 'regex'
export type SignalLabel = 'pain-point' | 'feedback' | 'mention' | 'trust'
export type SignalStatus = 'new' | 'saved' | 'dismissed'

export interface SignalRule {
  id: number
  name: string
  platform: string
  sub: string | null
  keywords: string[]
  match_mode: SignalMatchMode
  min_score: number
  label: SignalLabel | null
  active: number
  created_at: string
  notes: string | null
}

export interface SignalRuleCreate {
  name: string
  platform?: string
  sub?: string | null
  keywords?: string[]
  match_mode?: SignalMatchMode
  min_score?: number
  label?: SignalLabel | null
  notes?: string | null
}

export interface Signal {
  id: number
  platform: string
  sub: string
  post_id: string
  title: string
  body_snippet: string | null
  score: number | null
  comment_count: number | null
  author: string | null
  url: string | null
  posted_at: string | null
  surfaced_at: string
  matched_keywords: string[]
  status: SignalStatus
  notes: string | null
  matched_rules?: SignalRule[]
}

export interface SessionStatus {
  target: string
  valid: boolean
  age_hours: number | null
  session_file: string
}

export interface RefreshResult {
  target: string
  ok: boolean
  message: string
}

// ------------------------------------------------------------------ //
// Campaigns
// ------------------------------------------------------------------ //

export const api = {
  campaigns: {
    list: (activeOnly = false) =>
      http.get<Campaign[]>('/campaigns', { params: { active_only: activeOnly } }).then(r => r.data),

    create: (data: CampaignCreate) =>
      http.post<Campaign>('/campaigns', data).then(r => r.data),

    get: (id: number) =>
      http.get<Campaign>(`/campaigns/${id}`).then(r => r.data),

    update: (id: number, data: CampaignUpdate) =>
      http.patch<Campaign>(`/campaigns/${id}`, data).then(r => r.data),

    delete: (id: number) =>
      http.delete(`/campaigns/${id}`),

    trigger: (id: number) =>
      http.post<{ campaign_id: number; results: unknown[] }>(`/campaigns/${id}/trigger`).then(r => r.data),
  },

  variants: {
    list: (campaignId: number) =>
      http.get<Variant[]>(`/campaigns/${campaignId}/variants`).then(r => r.data),

    create: (campaignId: number, data: VariantCreate) =>
      http.post<Variant>(`/campaigns/${campaignId}/variants`, data).then(r => r.data),

    update: (campaignId: number, variantId: number, data: Partial<VariantCreate>) =>
      http.patch<Variant>(`/campaigns/${campaignId}/variants/${variantId}`, data).then(r => r.data),

    delete: (campaignId: number, variantId: number) =>
      http.delete(`/campaigns/${campaignId}/variants/${variantId}`),
  },

  subs: {
    listForCampaign: (campaignId: number) =>
      http.get<CampaignSub[]>(`/campaigns/${campaignId}/subs`).then(r => r.data),

    add: (campaignId: number, sub: string, sortOrder = 0) =>
      http.post<CampaignSub>(`/campaigns/${campaignId}/subs`, { sub, sort_order: sortOrder }).then(r => r.data),

    remove: (campaignId: number, sub: string) =>
      http.delete(`/campaigns/${campaignId}/subs/${sub}`),

    listRules: (platform = 'reddit') =>
      http.get<SubRules[]>('/subs', { params: { platform } }).then(r => r.data),

    upsertRules: (sub: string, data: SubRulesUpsert, platform = 'reddit') =>
      http.put<SubRules>(`/subs/${sub}`, data, { params: { platform } }).then(r => r.data),
  },

  posts: {
    list: (campaignId?: number, target?: string, limit = 50) =>
      http.get<Post[]>('/posts', { params: { campaign_id: campaignId, target, limit } }).then(r => r.data),

    triggerSingle: (campaignId: number, sub: string) =>
      http.post<Post>('/posts/trigger', { campaign_id: campaignId, sub }).then(r => r.data),
  },

  opportunities: {
    list: (status?: OpportunityStatus) =>
      http.get<Opportunity[]>('/opportunities', { params: status ? { status } : {} }).then(r => r.data),

    create: (data: OpportunityCreate) =>
      http.post<Opportunity>('/opportunities', data).then(r => r.data),

    get: (id: number) =>
      http.get<Opportunity>(`/opportunities/${id}`).then(r => r.data),

    update: (id: number, data: Partial<Pick<Opportunity, 'draft_title' | 'draft_body' | 'signal_reason' | 'product' | 'status' | 'campaign_id'>>) =>
      http.patch<Opportunity>(`/opportunities/${id}`, data).then(r => r.data),

    approve: (id: number) =>
      http.post<ApproveResult>(`/opportunities/${id}/approve`).then(r => r.data),

    markPosted: (id: number, manual = false, url?: string | null) =>
      http.post<Opportunity>(`/opportunities/${id}/mark-posted`, { url: url ?? null }, { params: { manual } }).then(r => r.data),

    dismiss: (id: number, note?: string) =>
      http.post<Opportunity>(`/opportunities/${id}/dismiss`, { note: note ?? null }).then(r => r.data),
  },

  signalRules: {
    list: (activeOnly = false) =>
      http.get<SignalRule[]>('/signal-rules', { params: { active_only: activeOnly } }).then(r => r.data),

    create: (data: SignalRuleCreate) =>
      http.post<SignalRule>('/signal-rules', data).then(r => r.data),

    get: (id: number) =>
      http.get<SignalRule>(`/signal-rules/${id}`).then(r => r.data),

    update: (id: number, data: Partial<SignalRuleCreate> & { active?: boolean }) =>
      http.patch<SignalRule>(`/signal-rules/${id}`, data).then(r => r.data),

    delete: (id: number) =>
      http.delete(`/signal-rules/${id}`),
  },

  signals: {
    list: (params?: { status?: SignalStatus; platform?: string; sub?: string; limit?: number }) =>
      http.get<Signal[]>('/signals', { params }).then(r => r.data),

    get: (id: number) =>
      http.get<Signal>(`/signals/${id}`).then(r => r.data),

    updateStatus: (id: number, status: SignalStatus, notes?: string) =>
      http.patch<Signal>(`/signals/${id}/status`, { status, notes: notes ?? null }).then(r => r.data),
  },

  reddit: {
    sessionStatus: (target = 'magpie') =>
      http.get<SessionStatus>('/reddit/session-status', { params: { target } }).then(r => r.data),
    refreshSession: (target = 'magpie') =>
      http.post<RefreshResult>('/reddit/refresh-session', null, { params: { target } }).then(r => r.data),
  },

  stats: () => http.get('/stats').then(r => r.data),
}
