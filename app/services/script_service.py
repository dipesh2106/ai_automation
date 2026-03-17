from __future__ import annotations


def generate_script(topic: str, language: str, style: str, duration: str) -> dict:
    opening = "Kya aap jaante ho" if language == "hi" else "Did you know"
    body = [
        f"{opening}? {topic} has lessons that can change your life.",
        f"In this {style} video, we break the journey into practical steps.",
        "Every setback became a setup for a better comeback.",
        "The key pattern: clarity, consistency, and courageous decisions.",
    ]
    cta = "Agar video pasand aaye, channel subscribe karein." if language == "hi" else "If this helped, subscribe for more."
    return {
        "hook": body[0],
        "body": body[1:],
        "cta": cta,
        "full_text": " ".join(body + [cta]),
        "duration": duration,
    }
