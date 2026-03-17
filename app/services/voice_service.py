from __future__ import annotations

from pathlib import Path


def generate_voiceover(job_dir: Path, script_text: str) -> str:
    voice_file = job_dir / "voiceover.txt"
    voice_file.write_text(f"VOICEOVER PLACEHOLDER\n{script_text}\n", encoding="utf-8")
    return str(voice_file)
