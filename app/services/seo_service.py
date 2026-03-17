from __future__ import annotations


def generate_seo(topic: str, style: str) -> dict:
    return {
        "title": f"{topic} | {style.title()} Story That Will Inspire You",
        "description": f"Watch this {style} breakdown about {topic}. Learn key lessons and actionable insights.",
        "tags": [topic, style, "motivation", "ai automation"],
        "hashtags": ["#motivation", "#story", "#youtubeautomation"],
    }
