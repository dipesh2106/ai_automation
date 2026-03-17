from __future__ import annotations

from pathlib import Path


def generate_visuals(job_dir: Path, scenes: list[dict]) -> list[dict]:
    visuals_dir = job_dir / "visuals"
    visuals_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for scene in scenes:
        file_path = visuals_dir / f"scene_{scene['scene_index']}.txt"
        file_path.write_text(
            f"VISUAL PLACEHOLDER\nPrompt: {scene['visual_prompt']}\nEmotion: {scene['emotion']}\n",
            encoding="utf-8",
        )
        outputs.append({"scene_index": scene["scene_index"], "asset_path": str(file_path)})
    return outputs
