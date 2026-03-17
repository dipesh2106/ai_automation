from __future__ import annotations

from pathlib import Path


def generate_thumbnail(job_dir: Path, topic: str) -> str:
    file_path = job_dir / "thumbnail.svg"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
  <rect width="100%" height="100%" fill="#111827"/>
  <text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" fill="#facc15" font-size="64" font-family="Arial">{topic[:40]}</text>
  <text x="50%" y="60%" dominant-baseline="middle" text-anchor="middle" fill="#ffffff" font-size="36" font-family="Arial">AI YouTube Automation</text>
</svg>'''
    file_path.write_text(svg, encoding="utf-8")
    return str(file_path)
