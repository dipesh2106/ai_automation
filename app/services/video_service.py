from __future__ import annotations

from pathlib import Path


def assemble_video(job_dir: Path, scenes: list[dict], voice_path: str) -> str:
    final_file = job_dir / "final_video.txt"
    content = ["FINAL VIDEO MANIFEST", f"Voice: {voice_path}"]
    for scene in scenes:
        content.append(f"Scene {scene['scene_index']}: {scene['text']}")
    final_file.write_text("\n".join(content) + "\n", encoding="utf-8")
    return str(final_file)
