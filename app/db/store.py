from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Columns whose values are stored as JSON and should be auto-decoded on read.
_JSON_COLUMNS = frozenset()


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row)
    for col in _JSON_COLUMNS:
        if col in d and isinstance(d[col], str):
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


class Store:
    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------------ #
    # Migrations
    # ------------------------------------------------------------------ #

    def run_migrations(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        self.conn.commit()
        applied = {
            row[0]
            for row in self.conn.execute("SELECT name FROM _migrations").fetchall()
        }
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if sql_file.name not in applied:
                self.conn.executescript(sql_file.read_text())
                self.conn.execute(
                    "INSERT INTO _migrations (name) VALUES (?)", (sql_file.name,)
                )
                self.conn.commit()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _insert_returning(self, sql: str, params: tuple = ()) -> dict[str, Any]:
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.execute(sql, params)
        row = _row_to_dict(cur.fetchone())
        self.conn.commit()
        return row

    def _fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.execute(sql, params)
        return [_row_to_dict(r) for r in cur.fetchall()]

    def _fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.execute(sql, params)
        return _row_to_dict(cur.fetchone())

    # ------------------------------------------------------------------ #
    # Campaigns
    # ------------------------------------------------------------------ #

    def list_campaigns(self, active_only: bool = False) -> list[dict]:
        where = "WHERE active = 1" if active_only else ""
        return self._fetchall(f"SELECT * FROM campaigns {where} ORDER BY product, name")

    def get_campaign(self, campaign_id: int) -> dict | None:
        return self._fetchone("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))

    def create_campaign(self, name: str, product: str, platform: str = "reddit",
                        cron_schedule: str | None = None, notes: str | None = None) -> dict:
        return self._insert_returning(
            "INSERT INTO campaigns (name, product, platform, cron_schedule, notes) VALUES (?,?,?,?,?) RETURNING *",
            (name, product, platform, cron_schedule, notes),
        )

    def update_campaign(self, campaign_id: int, **fields) -> dict | None:
        allowed = {"name", "product", "cron_schedule", "active", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_campaign(campaign_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        params = tuple(updates.values()) + (campaign_id,)
        self.conn.execute(
            f"UPDATE campaigns SET {set_clause} WHERE id = ?", params
        )
        self.conn.commit()
        return self.get_campaign(campaign_id)

    def delete_campaign(self, campaign_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        self.conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    # Campaign variants
    # ------------------------------------------------------------------ #

    def list_variants(self, campaign_id: int) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM campaign_variants WHERE campaign_id = ? ORDER BY sub_pattern",
            (campaign_id,),
        )

    def get_variant(self, variant_id: int) -> dict | None:
        return self._fetchone("SELECT * FROM campaign_variants WHERE id = ?", (variant_id,))

    def resolve_variant(self, campaign_id: int, sub: str) -> dict | None:
        """Pick the best-matching variant for a given sub (exact > prefix > default)."""
        variants = self.list_variants(campaign_id)
        exact = next((v for v in variants if v["sub_pattern"] == sub), None)
        if exact:
            return exact
        prefix = next(
            (v for v in variants
             if v["sub_pattern"].endswith("*") and sub.startswith(v["sub_pattern"][:-1])),
            None,
        )
        if prefix:
            return prefix
        return next((v for v in variants if v["sub_pattern"] == "*"), None)

    def create_variant(self, campaign_id: int, title: str, body: str,
                       sub_pattern: str = "*", flair: str | None = None,
                       notes: str | None = None) -> dict:
        return self._insert_returning(
            "INSERT INTO campaign_variants (campaign_id, sub_pattern, title, body, flair, notes) VALUES (?,?,?,?,?,?) RETURNING *",
            (campaign_id, sub_pattern, title, body, flair, notes),
        )

    def update_variant(self, variant_id: int, **fields) -> dict | None:
        allowed = {"sub_pattern", "title", "body", "flair", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_variant(variant_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        params = tuple(updates.values()) + (variant_id,)
        self.conn.execute(
            f"UPDATE campaign_variants SET {set_clause} WHERE id = ?", params
        )
        self.conn.commit()
        return self.get_variant(variant_id)

    def delete_variant(self, variant_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM campaign_variants WHERE id = ?", (variant_id,))
        self.conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    # Campaign subs
    # ------------------------------------------------------------------ #

    def list_campaign_subs(self, campaign_id: int) -> list[dict]:
        return self._fetchall(
            "SELECT * FROM campaign_subs WHERE campaign_id = ? ORDER BY sort_order, sub",
            (campaign_id,),
        )

    def add_campaign_sub(self, campaign_id: int, sub: str, sort_order: int = 0) -> dict:
        return self._insert_returning(
            "INSERT OR REPLACE INTO campaign_subs (campaign_id, sub, sort_order) VALUES (?,?,?) RETURNING *",
            (campaign_id, sub, sort_order),
        )

    def remove_campaign_sub(self, campaign_id: int, sub: str) -> bool:
        cur = self.conn.execute(
            "DELETE FROM campaign_subs WHERE campaign_id = ? AND sub = ?", (campaign_id, sub)
        )
        self.conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    # Posts
    # ------------------------------------------------------------------ #

    def list_posts(self, campaign_id: int | None = None, target: str | None = None,
                   limit: int = 50) -> list[dict]:
        clauses, params = [], []
        if campaign_id is not None:
            clauses.append("campaign_id = ?")
            params.append(campaign_id)
        if target is not None:
            clauses.append("target = ?")
            params.append(target)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        return self._fetchall(
            f"SELECT * FROM posts {where} ORDER BY posted_at DESC LIMIT ?", tuple(params)
        )

    def create_post(self, campaign_id: int, target: str, variant_id: int | None = None,
                    platform: str = "reddit", triggered_by: str = "scheduler") -> dict:
        return self._insert_returning(
            "INSERT INTO posts (campaign_id, variant_id, platform, target, status, triggered_by) VALUES (?,?,?,?,'pending',?) RETURNING *",
            (campaign_id, variant_id, platform, target, triggered_by),
        )

    def update_post_status(self, post_id: int, status: str, url: str | None = None,
                           error_msg: str | None = None, screenshot_path: str | None = None) -> dict | None:
        self.conn.execute(
            "UPDATE posts SET status = ?, url = ?, error_msg = ?, screenshot_path = ? WHERE id = ?",
            (status, url, error_msg, screenshot_path, post_id),
        )
        self.conn.commit()
        return self._fetchone("SELECT * FROM posts WHERE id = ?", (post_id,))

    def already_posted_this_week(self, campaign_id: int, target: str) -> bool:
        """Return True if a successful post to this sub exists in the past 7 days."""
        row = self._fetchone(
            "SELECT id FROM posts WHERE campaign_id = ? AND target = ? AND status = 'success'"
            " AND posted_at >= datetime('now', '-7 days')",
            (campaign_id, target),
        )
        return row is not None

    # ------------------------------------------------------------------ #
    # Sub rules
    # ------------------------------------------------------------------ #

    def list_sub_rules(self, platform: str = "reddit") -> list[dict]:
        return self._fetchall(
            "SELECT * FROM sub_rules WHERE platform = ? ORDER BY sub", (platform,)
        )

    def get_sub_rules(self, sub: str, platform: str = "reddit") -> dict | None:
        return self._fetchone(
            "SELECT * FROM sub_rules WHERE platform = ? AND sub = ?", (platform, sub)
        )

    def upsert_sub_rules(self, sub: str, platform: str = "reddit", **fields) -> dict:
        existing = self.get_sub_rules(sub, platform)
        if existing:
            allowed = {"flair_required", "flair_to_use", "promo_allowed", "rule_warning", "notes", "last_checked"}
            updates = {k: v for k, v in fields.items() if k in allowed}
            if updates:
                set_clause = ", ".join(f"{k} = ?" for k in updates)
                set_clause += ", updated_at = datetime('now')"
                params = tuple(updates.values()) + (platform, sub)
                self.conn.execute(
                    f"UPDATE sub_rules SET {set_clause} WHERE platform = ? AND sub = ?", params
                )
                self.conn.commit()
            return self.get_sub_rules(sub, platform)
        return self._insert_returning(
            "INSERT INTO sub_rules (platform, sub, flair_required, flair_to_use, promo_allowed, rule_warning, notes, last_checked) VALUES (?,?,?,?,?,?,?,?) RETURNING *",
            (platform, sub,
             fields.get("flair_required", 0), fields.get("flair_to_use"),
             fields.get("promo_allowed"), fields.get("rule_warning", 0),
             fields.get("notes"), fields.get("last_checked")),
        )

    # ------------------------------------------------------------------ #
    # Engagement
    # ------------------------------------------------------------------ #

    def record_engagement(self, post_id: int, score: int | None = None,
                          upvotes: int | None = None, comments: int | None = None,
                          awards: int = 0) -> dict:
        return self._insert_returning(
            "INSERT INTO engagement (post_id, score, upvotes, comments, awards) VALUES (?,?,?,?,?) RETURNING *",
            (post_id, score, upvotes, comments, awards),
        )

    def get_latest_engagement(self, post_id: int) -> dict | None:
        return self._fetchone(
            "SELECT * FROM engagement WHERE post_id = ? ORDER BY checked_at DESC LIMIT 1",
            (post_id,),
        )

    # ------------------------------------------------------------------ #
    # Opportunities
    # ------------------------------------------------------------------ #

    def list_opportunities(self, status: str | None = None) -> list[dict]:
        if status:
            return self._fetchall(
                "SELECT * FROM opportunities WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        return self._fetchall(
            "SELECT * FROM opportunities ORDER BY created_at DESC"
        )

    def get_opportunity(self, opportunity_id: int) -> dict | None:
        return self._fetchone(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        )

    def create_opportunity(
        self,
        community: str,
        thread_url: str,
        draft_body: str,
        platform: str = "reddit",
        thread_title: str | None = None,
        thread_body: str | None = None,
        signal_reason: str | None = None,
        product: str | None = None,
        draft_title: str | None = None,
        post_type: str = "reply_to_thread",
        campaign_id: int | None = None,
    ) -> dict:
        return self._insert_returning(
            """INSERT INTO opportunities
               (platform, community, thread_url, thread_title, thread_body,
                signal_reason, product, draft_title, draft_body, post_type, campaign_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?) RETURNING *""",
            (platform, community, thread_url, thread_title, thread_body,
             signal_reason, product, draft_title, draft_body, post_type, campaign_id),
        )

    def update_opportunity(self, opportunity_id: int, **fields) -> dict | None:
        allowed = {"draft_title", "draft_body", "signal_reason", "product",
                   "status", "dismiss_note", "campaign_id"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_opportunity(opportunity_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        params = tuple(updates.values()) + (opportunity_id,)
        self.conn.execute(
            f"UPDATE opportunities SET {set_clause} WHERE id = ?", params
        )
        self.conn.commit()
        return self.get_opportunity(opportunity_id)

    def approve_opportunity(self, opportunity_id: int) -> dict | None:
        return self.update_opportunity(opportunity_id, status="approved")

    def dismiss_opportunity(self, opportunity_id: int, note: str | None = None) -> dict | None:
        return self.update_opportunity(opportunity_id, status="dismissed", dismiss_note=note)
