from __future__ import annotations

import json
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app import db
from app.services.analytics_service import get_mock_analytics
from app.services.scene_service import breakdown_script
from app.services.script_service import generate_script
from app.services.seo_service import generate_seo
from app.services.thumbnail_service import generate_thumbnail
from app.services.video_service import assemble_video
from app.services.visual_service import generate_visuals
from app.services.voice_service import generate_voiceover
from app.services.youtube_service import upload_video_mock


class PipelineEngine:
    def __init__(self) -> None:
        self.queue: queue.Queue[dict] = queue.Queue()
        self._running = False
        self.worker_thread: threading.Thread | None = None
        self.scheduler_thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.worker_thread.start()
        self.scheduler_thread.start()

    def stop(self) -> None:
        self._running = False

    def enqueue(self, payload: dict) -> None:
        self.queue.put(payload)

    def _worker_loop(self) -> None:
        while self._running:
            try:
                payload = self.queue.get(timeout=1)
            except queue.Empty:
                continue
            self._run_job(payload["job_id"])
            self.queue.task_done()

    def _scheduler_loop(self) -> None:
        while self._running:
            now = datetime.now(tz=timezone.utc)
            due = db.due_schedules(now)
            for schedule in due:
                job_id = str(uuid4())
                created_at = db.now_iso()
                db.create_job(
                    {
                        "job_id": job_id,
                        "topic": schedule["topic"],
                        "language": schedule["language"],
                        "duration": schedule["duration"],
                        "style": schedule["style"],
                        "auto_upload": bool(schedule["auto_upload"]),
                        "status": "queued",
                        "current_step": None,
                        "created_at": created_at,
                        "updated_at": created_at,
                    }
                )
                self.enqueue({"job_id": job_id})
                db.advance_schedule(schedule["schedule_id"], int(schedule["cron_minutes"]))
            time.sleep(10)

    def _run_job(self, job_id: str) -> None:
        job = db.get_job(job_id)
        if not job:
            return
        job_dir = Path("data/artifacts") / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        output = job.get("output", {})

        db.update_job(job_id, status="running")
        try:
            step_id = db.add_step(job_id, "script.generate")
            script = generate_script(job["topic"], job["language"], job["style"], job["duration"])
            (job_dir / "script.json").write_text(json.dumps(script, indent=2), encoding="utf-8")
            output["script"] = script
            db.finish_step(step_id, "completed", script)
            db.update_job(job_id, current_step="scene.breakdown", output_json=output)

            step_id = db.add_step(job_id, "scene.breakdown")
            scenes = breakdown_script(script)
            (job_dir / "scenes.json").write_text(json.dumps(scenes, indent=2), encoding="utf-8")
            output["scenes"] = scenes
            db.finish_step(step_id, "completed", {"count": len(scenes)})
            db.update_job(job_id, current_step="visual.generate", output_json=output)

            step_id = db.add_step(job_id, "visual.generate")
            output["visuals"] = generate_visuals(job_dir, scenes)
            db.finish_step(step_id, "completed", {"count": len(scenes)})
            db.update_job(job_id, current_step="voice.generate", output_json=output)

            step_id = db.add_step(job_id, "voice.generate")
            voice_path = generate_voiceover(job_dir, script["full_text"])
            output["voiceover_path"] = voice_path
            db.finish_step(step_id, "completed", {"voiceover_path": voice_path})
            db.update_job(job_id, current_step="video.assemble", output_json=output)

            step_id = db.add_step(job_id, "video.assemble")
            final_video_path = assemble_video(job_dir, scenes, voice_path)
            output["final_video_path"] = final_video_path
            db.finish_step(step_id, "completed", {"final_video_path": final_video_path})
            db.update_job(job_id, current_step="thumbnail.generate", output_json=output)

            step_id = db.add_step(job_id, "thumbnail.generate")
            thumbnail_path = generate_thumbnail(job_dir, job["topic"])
            output["thumbnail_path"] = thumbnail_path
            db.finish_step(step_id, "completed", {"thumbnail_path": thumbnail_path})
            db.update_job(job_id, current_step="seo.generate", output_json=output)

            step_id = db.add_step(job_id, "seo.generate")
            seo = generate_seo(job["topic"], job["style"])
            output["seo"] = seo
            db.finish_step(step_id, "completed", seo)

            if job["auto_upload"]:
                db.update_job(job_id, current_step="youtube.upload", output_json=output)
                step_id = db.add_step(job_id, "youtube.upload")
                upload = upload_video_mock(job_id, seo["title"], final_video_path, thumbnail_path)
                output["upload"] = upload
                output["analytics"] = get_mock_analytics(upload["youtube_video_id"])
                db.finish_step(step_id, "completed", upload)
                db.update_job(job_id, status="uploaded", current_step="done", output_json=output)
            else:
                db.update_job(job_id, status="completed", current_step="done", output_json=output)
        except Exception as exc:
            db.update_job(job_id, status="failed", current_step="failed", error=str(exc), output_json=output)


engine = PipelineEngine()
