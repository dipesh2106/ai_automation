from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path("data/app.db")


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                language TEXT NOT NULL,
                duration TEXT NOT NULL,
                style TEXT NOT NULL,
                auto_upload INTEGER NOT NULL,
                status TEXT NOT NULL,
                current_step TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                output_json TEXT NOT NULL DEFAULT '{}',
                error TEXT
            );

            CREATE TABLE IF NOT EXISTS job_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                step TEXT NOT NULL,
                status TEXT NOT NULL,
                output_json TEXT NOT NULL DEFAULT '{}',
                error TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            );

            CREATE TABLE IF NOT EXISTS schedules (
                schedule_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                language TEXT NOT NULL,
                duration TEXT NOT NULL,
                style TEXT NOT NULL,
                cron_minutes INTEGER NOT NULL,
                auto_upload INTEGER NOT NULL,
                next_run_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_job(job: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (job_id, topic, language, duration, style, auto_upload, status, current_step, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job["job_id"],
                job["topic"],
                job["language"],
                job["duration"],
                job["style"],
                int(job["auto_upload"]),
                job["status"],
                job.get("current_step"),
                job["created_at"],
                job["updated_at"],
            ),
        )


def update_job(job_id: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = now_iso()
    keys = list(fields.keys())
    vals = [json.dumps(v) if k == "output_json" and isinstance(v, dict) else v for k, v in fields.items()]
    clause = ", ".join(f"{k} = ?" for k in keys)
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {clause} WHERE job_id = ?", (*vals, job_id))


def get_job(job_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["output"] = json.loads(d.pop("output_json") or "{}")
    d["auto_upload"] = bool(d["auto_upload"])
    return d


def list_jobs() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100").fetchall()
    items = []
    for row in rows:
        d = dict(row)
        d["output"] = json.loads(d.pop("output_json") or "{}")
        d["auto_upload"] = bool(d["auto_upload"])
        items.append(d)
    return items


def add_step(job_id: str, step: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO job_steps (job_id, step, status, started_at) VALUES (?, ?, 'running', ?)",
            (job_id, step, now_iso()),
        )
        return int(cur.lastrowid)


def finish_step(step_id: int, status: str, output: dict[str, Any] | None = None, error: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE job_steps
            SET status = ?, output_json = ?, error = ?, finished_at = ?
            WHERE id = ?
            """,
            (status, json.dumps(output or {}), error, now_iso(), step_id),
        )


def create_schedule(s: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO schedules (schedule_id, topic, language, duration, style, cron_minutes, auto_upload, next_run_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                s["schedule_id"],
                s["topic"],
                s["language"],
                s["duration"],
                s["style"],
                s["cron_minutes"],
                int(s["auto_upload"]),
                s["next_run_at"],
                s["created_at"],
            ),
        )


def list_schedules() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM schedules ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def delete_schedule(schedule_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM schedules WHERE schedule_id = ?", (schedule_id,))
        return cur.rowcount > 0


def due_schedules(now: datetime) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM schedules WHERE next_run_at <= ?", (now.isoformat(),)).fetchall()
    return [dict(r) for r in rows]


def advance_schedule(schedule_id: str, minutes: int) -> None:
    next_run = datetime.now(tz=timezone.utc) + timedelta(minutes=minutes)
    with get_conn() as conn:
        conn.execute("UPDATE schedules SET next_run_at = ? WHERE schedule_id = ?", (next_run.isoformat(), schedule_id))
