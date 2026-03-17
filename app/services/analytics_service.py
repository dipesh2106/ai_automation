from __future__ import annotations

import random


def get_mock_analytics(youtube_video_id: str) -> dict:
    return {
        "youtube_video_id": youtube_video_id,
        "views": random.randint(100, 5000),
        "ctr": round(random.uniform(2.0, 9.0), 2),
        "watch_time_minutes": random.randint(50, 1000),
    }
