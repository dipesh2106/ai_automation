from __future__ import annotations


def breakdown_script(script: dict) -> list[dict]:
    lines = [script["hook"], *script["body"], script["cta"]]
    scenes = []
    for idx, line in enumerate(lines, start=1):
        scenes.append(
            {
                "scene_index": idx,
                "text": line,
                "visual_prompt": f"Cinematic scene for: {line}",
                "emotion": "dramatic" if idx == 1 else "inspiring",
                "duration_sec": 5,
            }
        )
    return scenes
