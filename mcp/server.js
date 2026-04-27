'use strict';

/**
 * Magpie MCP Server — JSON-RPC 2.0 over stdio
 *
 * Thin bridge between Claude and the Magpie FastAPI backend.
 * All heavy logic lives in the API; this server just translates
 * tool calls to HTTP requests.
 *
 * Env:
 *   MAGPIE_API_URL  - Magpie API base (default: http://localhost:8532)
 */

const MAGPIE_URL = (process.env.MAGPIE_API_URL || 'http://localhost:8532').replace(/\/$/, '');
const BASE = `${MAGPIE_URL}/api/v1`;

process.stderr.write(`[magpie-mcp] starting — API: ${MAGPIE_URL}\n`);

// ─── HTTP helper ──────────────────────────────────────────────────────────────

async function api(method, path, body) {
  const url = `${BASE}${path}`;
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const text = await res.text();
  if (!res.ok) throw new Error(`HTTP ${res.status} ${path}: ${text}`);
  return text ? JSON.parse(text) : null;
}

// ─── Tool definitions ─────────────────────────────────────────────────────────

const TOOLS = [
  // Campaigns
  {
    name: 'list_campaigns',
    description: 'List all Magpie campaigns. Optionally filter to active only.',
    inputSchema: {
      type: 'object',
      properties: {
        active_only: { type: 'boolean', description: 'If true, only return active campaigns', default: false },
      },
    },
  },
  {
    name: 'get_campaign',
    description: 'Get a single campaign by ID, including its variants and subs.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
      },
      required: ['campaign_id'],
    },
  },
  {
    name: 'create_campaign',
    description: 'Create a new campaign. Returns the created campaign record.',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Human-readable campaign name' },
        product: { type: 'string', description: 'Product code (e.g. kiwi, peregrine, snipe, circuitforge)' },
        platform: { type: 'string', description: 'Platform (default: reddit)', default: 'reddit' },
        cron_schedule: { type: 'string', description: 'Cron expression for auto-scheduling (e.g. "0 9 * * 2"). Leave blank for manual-only.' },
        notes: { type: 'string', description: 'Internal notes about this campaign' },
      },
      required: ['name', 'product'],
    },
  },
  {
    name: 'update_campaign',
    description: 'Update a campaign (name, cron_schedule, active state, notes). Only provided fields are updated.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
        name: { type: 'string' },
        cron_schedule: { type: 'string', description: 'New cron expression, or null to clear' },
        active: { type: 'boolean', description: 'true = active, false = paused' },
        notes: { type: 'string' },
      },
      required: ['campaign_id'],
    },
  },
  {
    name: 'trigger_campaign',
    description: 'Manually trigger a campaign to post to all its configured subreddits immediately. Returns per-sub results.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID to fire' },
      },
      required: ['campaign_id'],
    },
  },

  // Variants
  {
    name: 'list_variants',
    description: 'List content variants for a campaign. Each variant has a sub_pattern (exact sub, prefix*, or * for default).',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
      },
      required: ['campaign_id'],
    },
  },
  {
    name: 'create_variant',
    description: 'Add a content variant to a campaign. Use sub_pattern="*" for the default, an exact sub name for a sub-specific variant, or "prefix*" for a prefix match (e.g. "nd_*" matches nd_audhd, nd_adhd, etc.).',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
        sub_pattern: { type: 'string', description: 'Sub pattern: "*" = default, exact name, or "prefix*"', default: '*' },
        title: { type: 'string', description: 'Post title' },
        body: { type: 'string', description: 'Post body (Reddit markdown)' },
        flair: { type: 'string', description: 'Flair label required by the subreddit (optional)' },
        notes: { type: 'string', description: 'Internal framing notes' },
      },
      required: ['campaign_id', 'title', 'body'],
    },
  },
  {
    name: 'delete_variant',
    description: 'Delete a content variant by ID.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID the variant belongs to' },
        variant_id: { type: 'integer', description: 'Variant ID to delete' },
      },
      required: ['campaign_id', 'variant_id'],
    },
  },

  // Subs
  {
    name: 'list_campaign_subs',
    description: 'List the subreddits configured for a campaign.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
      },
      required: ['campaign_id'],
    },
  },
  {
    name: 'add_campaign_sub',
    description: 'Add a subreddit to a campaign target list.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
        sub: { type: 'string', description: 'Subreddit name without r/ prefix' },
        sort_order: { type: 'integer', description: 'Posting order (lower = first, default 0)', default: 0 },
      },
      required: ['campaign_id', 'sub'],
    },
  },
  {
    name: 'remove_campaign_sub',
    description: 'Remove a subreddit from a campaign target list.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
        sub: { type: 'string', description: 'Subreddit name to remove' },
      },
      required: ['campaign_id', 'sub'],
    },
  },

  // Posts
  {
    name: 'list_posts',
    description: 'List post history. Filter by campaign or subreddit.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Filter by campaign ID (optional)' },
        target: { type: 'string', description: 'Filter by subreddit name (optional)' },
        limit: { type: 'integer', description: 'Max results (default 50)', default: 50 },
      },
    },
  },
  {
    name: 'trigger_sub_post',
    description: 'Manually trigger a post to a single subreddit for a specific campaign.',
    inputSchema: {
      type: 'object',
      properties: {
        campaign_id: { type: 'integer', description: 'Campaign ID' },
        sub: { type: 'string', description: 'Subreddit to post to (without r/)' },
      },
      required: ['campaign_id', 'sub'],
    },
  },

  // Sub rules
  {
    name: 'get_sub_rules',
    description: 'Get the stored rules and posting metadata for a specific subreddit.',
    inputSchema: {
      type: 'object',
      properties: {
        sub: { type: 'string', description: 'Subreddit name without r/ prefix' },
      },
      required: ['sub'],
    },
  },
  {
    name: 'upsert_sub_rules',
    description: 'Create or update posting rules for a subreddit (flair_required, promo_allowed, rule_warning).',
    inputSchema: {
      type: 'object',
      properties: {
        sub: { type: 'string', description: 'Subreddit name without r/ prefix' },
        flair_required: { type: 'boolean', description: 'Does this sub require flair to post?' },
        flair_to_use: { type: 'string', description: 'Default flair label for this sub' },
        promo_allowed: { type: 'boolean', description: 'true = allowed, false = banned, omit = unknown' },
        rule_warning: { type: 'boolean', description: 'Does the sub show a rule-warning dialog on post?' },
        notes: { type: 'string', description: 'Posting notes for this sub' },
      },
      required: ['sub'],
    },
  },

  // Opportunities
  {
    name: 'list_opportunities',
    description: 'List signal-detected opportunities for manual review. Filter by status: pending_review, approved, posted, manual_posted, dismissed.',
    inputSchema: {
      type: 'object',
      properties: {
        status: {
          type: 'string',
          description: 'Filter by status (omit for all)',
          enum: ['pending_review', 'approved', 'posted', 'manual_posted', 'dismissed'],
        },
      },
    },
  },
  {
    name: 'create_opportunity',
    description: 'Record a new posting opportunity for review. Use this when you spot a thread that would benefit from a Magpie campaign reply.',
    inputSchema: {
      type: 'object',
      properties: {
        community: { type: 'string', description: 'Subreddit, Lemmy community, or other community handle (e.g. "nd_adhd", "lemmy.world/c/memes")' },
        thread_url: { type: 'string', description: 'Full URL to the thread' },
        thread_title: { type: 'string', description: 'Thread title for context' },
        thread_body: { type: 'string', description: 'Thread body text for context (optional)' },
        platform: { type: 'string', description: 'Platform: reddit, lemmy, linkedin, etc. (default: reddit)', default: 'reddit' },
        signal_reason: { type: 'string', description: 'Why this thread is a good opportunity (1-2 sentences)' },
        product: { type: 'string', description: 'Product this is relevant to (e.g. peregrine, kiwi, snipe)' },
        draft_title: { type: 'string', description: 'Draft post title (for new_post type)' },
        draft_body: { type: 'string', description: 'Draft reply or post body (Reddit/Lemmy markdown)' },
        post_type: { type: 'string', description: 'reply_to_thread or new_post', enum: ['reply_to_thread', 'new_post'], default: 'reply_to_thread' },
        campaign_id: { type: 'integer', description: 'Campaign ID to associate (optional)' },
      },
      required: ['community', 'thread_url'],
    },
  },
  {
    name: 'approve_opportunity',
    description: 'Approve an opportunity for posting. Returns auto_post_ready (Reddit) or manual_handoff (other platforms) with instructions.',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_id: { type: 'integer', description: 'Opportunity ID to approve' },
      },
      required: ['opportunity_id'],
    },
  },
  {
    name: 'dismiss_opportunity',
    description: 'Dismiss an opportunity (not worth posting). Optionally provide a reason.',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_id: { type: 'integer', description: 'Opportunity ID to dismiss' },
        note: { type: 'string', description: 'Reason for dismissal (optional)' },
      },
      required: ['opportunity_id'],
    },
  },
  {
    name: 'update_opportunity',
    description: 'Edit the draft body, draft title, signal reason, product, or campaign link on an opportunity.',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_id: { type: 'integer', description: 'Opportunity ID' },
        draft_title: { type: 'string', description: 'Updated draft title' },
        draft_body: { type: 'string', description: 'Updated draft body' },
        signal_reason: { type: 'string', description: 'Updated signal reason' },
        product: { type: 'string', description: 'Updated product association' },
        campaign_id: { type: 'integer', description: 'Campaign ID to associate' },
      },
      required: ['opportunity_id'],
    },
  },

  // Blog (Directus)
  {
    name: 'publish_blog_post',
    description: 'Publish a blog post to the CircuitForge website via Directus. Defaults to published immediately. Returns the created post including its id and slug.',
    inputSchema: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Post title' },
        body: { type: 'string', description: 'Post body (Markdown)' },
        slug: { type: 'string', description: 'URL slug — auto-generated from title if omitted' },
        tags: { type: 'array', items: { type: 'string' }, description: 'Tag list (e.g. ["sprint-review", "kiwi"])' },
        author: { type: 'string', description: 'Author name (optional)' },
        seo_description: { type: 'string', description: 'Short SEO/meta description (optional)' },
        published_at: { type: 'string', description: 'ISO 8601 publish timestamp — defaults to now' },
      },
      required: ['title', 'body'],
    },
  },
  {
    name: 'get_blog_post',
    description: 'Fetch an existing blog post by its URL slug.',
    inputSchema: {
      type: 'object',
      properties: {
        slug: { type: 'string', description: 'The post slug (e.g. "2026-04-28-sprint-review")' },
      },
      required: ['slug'],
    },
  },

  // Scheduler
  {
    name: 'scheduler_status',
    description: 'Check the scheduler status and see next scheduled run times for all campaigns.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'refresh_reddit_session',
    description: 'Re-establish the Playwright Reddit session. Use target="bridge" to refresh the claude-bridge poster session, or "magpie" (default) for Magpie\'s own session. Takes ~30s.',
    inputSchema: {
      type: 'object',
      properties: {
        target: { type: 'string', enum: ['magpie', 'bridge'], default: 'magpie', description: 'Which session to refresh: "magpie" or "bridge" (claude-bridge/reddit-poster)' },
      },
    },
  },
  {
    name: 'reddit_session_status',
    description: 'Check whether the Reddit Playwright session is valid and how old it is.',
    inputSchema: {
      type: 'object',
      properties: {
        target: { type: 'string', enum: ['magpie', 'bridge'], default: 'magpie', description: 'Which session to check' },
      },
    },
  },
];

// ─── Dispatch ─────────────────────────────────────────────────────────────────

async function callTool(name, args) {
  switch (name) {
    case 'list_campaigns': {
      const qs = args.active_only ? '?active_only=true' : '';
      return await api('GET', `/campaigns${qs}`);
    }
    case 'get_campaign': {
      const [campaign, variants, subs] = await Promise.all([
        api('GET', `/campaigns/${args.campaign_id}`),
        api('GET', `/campaigns/${args.campaign_id}/variants`),
        api('GET', `/campaigns/${args.campaign_id}/subs`),
      ]);
      return { ...campaign, variants, subs };
    }
    case 'create_campaign': {
      const body = { name: args.name, product: args.product, platform: args.platform || 'reddit' };
      if (args.cron_schedule) body.cron_schedule = args.cron_schedule;
      if (args.notes) body.notes = args.notes;
      return await api('POST', '/campaigns', body);
    }
    case 'update_campaign': {
      const { campaign_id, ...fields } = args;
      return await api('PATCH', `/campaigns/${campaign_id}`, fields);
    }
    case 'trigger_campaign':
      return await api('POST', `/campaigns/${args.campaign_id}/trigger`);

    case 'list_variants':
      return await api('GET', `/campaigns/${args.campaign_id}/variants`);
    case 'create_variant': {
      const { campaign_id, ...body } = args;
      return await api('POST', `/campaigns/${campaign_id}/variants`, body);
    }
    case 'delete_variant':
      return await api('DELETE', `/campaigns/${args.campaign_id}/variants/${args.variant_id}`);

    case 'list_campaign_subs':
      return await api('GET', `/campaigns/${args.campaign_id}/subs`);
    case 'add_campaign_sub':
      return await api('POST', `/campaigns/${args.campaign_id}/subs`, {
        sub: args.sub,
        sort_order: args.sort_order || 0,
      });
    case 'remove_campaign_sub':
      return await api('DELETE', `/campaigns/${args.campaign_id}/subs/${args.sub}`);

    case 'list_posts': {
      const params = new URLSearchParams();
      if (args.campaign_id) params.set('campaign_id', args.campaign_id);
      if (args.target) params.set('target', args.target);
      if (args.limit) params.set('limit', args.limit);
      const qs = params.toString() ? `?${params}` : '';
      return await api('GET', `/posts${qs}`);
    }
    case 'trigger_sub_post':
      return await api('POST', '/posts/trigger', { campaign_id: args.campaign_id, sub: args.sub });

    case 'get_sub_rules':
      return await api('GET', `/subs/${args.sub}`);
    case 'upsert_sub_rules': {
      const { sub, ...body } = args;
      return await api('PUT', `/subs/${sub}`, body);
    }

    case 'publish_blog_post': {
      const { title, body, ...rest } = args;
      return await api('POST', '/blog', { title, body, ...rest });
    }
    case 'get_blog_post':
      return await api('GET', `/blog/${encodeURIComponent(args.slug)}`);

    case 'scheduler_status':
      return await api('GET', '/scheduler/status');

    case 'list_opportunities': {
      const qs = args.status ? `?status=${encodeURIComponent(args.status)}` : '';
      return await api('GET', `/opportunities${qs}`);
    }
    case 'create_opportunity': {
      const body = {
        community: args.community,
        thread_url: args.thread_url,
        platform: args.platform || 'reddit',
        draft_body: args.draft_body || '',
        post_type: args.post_type || 'reply_to_thread',
      };
      if (args.thread_title) body.thread_title = args.thread_title;
      if (args.thread_body) body.thread_body = args.thread_body;
      if (args.signal_reason) body.signal_reason = args.signal_reason;
      if (args.product) body.product = args.product;
      if (args.draft_title) body.draft_title = args.draft_title;
      if (args.campaign_id) body.campaign_id = args.campaign_id;
      return await api('POST', '/opportunities', body);
    }
    case 'approve_opportunity':
      return await api('POST', `/opportunities/${args.opportunity_id}/approve`);
    case 'dismiss_opportunity':
      return await api('POST', `/opportunities/${args.opportunity_id}/dismiss`, { note: args.note || null });
    case 'update_opportunity': {
      const { opportunity_id, ...fields } = args;
      return await api('PATCH', `/opportunities/${opportunity_id}`, fields);
    }

    case 'refresh_reddit_session': {
      const target = args.target || 'magpie';
      return await api('POST', `/reddit/refresh-session?target=${target}`);
    }
    case 'reddit_session_status': {
      const target = args.target || 'magpie';
      return await api('GET', `/reddit/session-status?target=${target}`);
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// ─── JSON-RPC 2.0 protocol ────────────────────────────────────────────────────

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function sendResult(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function sendError(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

async function handleMessage(msg) {
  const { id, method, params } = msg;

  if (method === 'initialize') {
    sendResult(id, {
      protocolVersion: '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'magpie-mcp', version: '0.1.0' },
    });
    return;
  }

  if (method === 'notifications/initialized') return;

  if (method === 'tools/list') {
    sendResult(id, { tools: TOOLS });
    return;
  }

  if (method === 'tools/call') {
    const { name, arguments: args = {} } = params || {};
    try {
      const result = await callTool(name, args);
      sendResult(id, {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
      });
    } catch (err) {
      process.stderr.write(`[magpie-mcp] tool error: ${err.message}\n`);
      sendResult(id, {
        content: [{ type: 'text', text: JSON.stringify({ error: err.message }) }],
        isError: true,
      });
    }
    return;
  }

  if (id !== undefined) sendError(id, -32601, `Method not found: ${method}`);
}

// ─── Stdin line reader ────────────────────────────────────────────────────────

let buffer = '';

process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  buffer += chunk;
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    let msg;
    try { msg = JSON.parse(trimmed); }
    catch (e) { process.stderr.write(`[magpie-mcp] parse error: ${e.message}\n`); continue; }
    handleMessage(msg).catch(err => {
      process.stderr.write(`[magpie-mcp] unhandled error: ${err.message}\n`);
    });
  }
});

process.stdin.on('end', () => {
  process.stderr.write('[magpie-mcp] stdin closed, exiting\n');
  process.exit(0);
});
