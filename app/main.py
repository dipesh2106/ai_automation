from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from app import db
from app.pipeline import engine


class AppHandler(BaseHTTPRequestHandler):
    def _send(self, code: int, body, content_type: str = "application/json") -> None:
        payload = body.encode("utf-8") if isinstance(body, str) else json.dumps(body, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self._send(200, _dashboard_html(), "text/html; charset=utf-8")
        if path == "/api/v1/jobs":
            return self._send(200, db.list_jobs())
        if path == "/api/v1/schedules":
            return self._send(200, db.list_schedules())

        parts = [p for p in path.split("/") if p]
        if len(parts) == 4 and parts[:3] == ["api", "v1", "jobs"]:
            job = db.get_job(parts[3])
            return self._send(200, job) if job else self._send(404, {"error": "Job not found"})
        if len(parts) == 4 and parts[:3] == ["api", "v1", "analytics"]:
            job = db.get_job(parts[3])
            return self._send(200, job.get("output", {}).get("analytics", {})) if job else self._send(404, {"error": "Job not found"})
        if len(parts) == 4 and parts[:3] == ["api", "v1", "artifacts"]:
            job_dir = Path("data/artifacts") / parts[3]
            if not job_dir.exists():
                return self._send(404, {"error": "Artifacts not found"})
            files = sorted(str(p) for p in job_dir.rglob("*") if p.is_file())
            return self._send(200, files)

        self._send(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/v1/jobs":
            body = self._read_json()
            required = ["topic", "language", "duration", "style"]
            if any(k not in body for k in required):
                return self._send(400, {"error": "Missing required fields"})
            job_id = str(uuid4())
            now = db.now_iso()
            db.create_job(
                {
                    "job_id": job_id,
                    "topic": body["topic"],
                    "language": body["language"],
                    "duration": body["duration"],
                    "style": body["style"],
                    "auto_upload": bool(body.get("auto_upload", True)),
                    "status": "queued",
                    "current_step": None,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            engine.enqueue({"job_id": job_id})
            return self._send(200, db.get_job(job_id))

        if path == "/api/v1/schedules":
            body = self._read_json()
            required = ["topic", "language", "duration", "style", "cron_minutes"]
            if any(k not in body for k in required):
                return self._send(400, {"error": "Missing required fields"})
            schedule_id = str(uuid4())
            now = datetime.now(tz=timezone.utc)
            next_run_at = now + timedelta(minutes=int(body["cron_minutes"]))
            db.create_schedule(
                {
                    "schedule_id": schedule_id,
                    "topic": body["topic"],
                    "language": body["language"],
                    "duration": body["duration"],
                    "style": body["style"],
                    "cron_minutes": int(body["cron_minutes"]),
                    "auto_upload": bool(body.get("auto_upload", True)),
                    "next_run_at": next_run_at.isoformat(),
                    "created_at": now.isoformat(),
                }
            )
            return self._send(200, {"schedule_id": schedule_id, "next_run_at": next_run_at.isoformat()})

        parts = [p for p in path.split("/") if p]
        if len(parts) == 5 and parts[:3] == ["api", "v1", "jobs"] and parts[4] == "retry":
            job = db.get_job(parts[3])
            if not job:
                return self._send(404, {"error": "Job not found"})
            db.update_job(parts[3], status="queued", current_step=None, error=None)
            engine.enqueue({"job_id": parts[3]})
            return self._send(200, db.get_job(parts[3]))

        self._send(404, {"error": "Not found"})

    def do_DELETE(self):
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]
        if len(parts) == 5 and parts[:3] == ["api", "v1", "schedules"]:
            ok = db.delete_schedule(parts[4])
            return self._send(200, {"deleted": True}) if ok else self._send(404, {"error": "Schedule not found"})
        self._send(404, {"error": "Not found"})


def _dashboard_html() -> str:
    jobs = db.list_jobs()[:20]
    rows = "".join(
        f"<tr><td>{j['job_id']}</td><td>{j['topic']}</td><td>{j['status']}</td><td>{j['current_step']}</td></tr>" for j in jobs
    )
    return f"""
    <html><head><title>AI YouTube Automation</title></head>
    <body style='font-family:Arial;background:#111;color:#eee'>
      <h1>AI YouTube Automation Tool</h1>
      <p>Use API endpoints to create jobs and schedules.</p>
      <table border='1' cellpadding='6' cellspacing='0'>
        <tr><th>Job ID</th><th>Topic</th><th>Status</th><th>Current Step</th></tr>
        {rows}
      </table>
    </body></html>
    """


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    db.init_db()
    engine.start()
    server = ThreadingHTTPServer((host, port), AppHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        server.server_close()


if __name__ == "__main__":
    run()
