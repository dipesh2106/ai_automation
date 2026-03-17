from __future__ import annotations


def upload_video_mock(job_id: str, title: str, video_path: str, thumbnail_path: str) -> dict:
    return {
        "youtube_video_id": f"yt_{job_id[-8:]}",
        "video_path": video_path,
        "thumbnail_path": thumbnail_path,
        "title": title,
        "status": "uploaded",
    }
