# API Contract (Draft)

## Base URL

`/api/v1`

## 1) Create automation job

`POST /jobs`

### Request

```json
{
  "topic": "Success story of Elon Musk",
  "language": "en",
  "duration": "5_min",
  "style": "motivational",
  "channelId": "ch_123",
  "autoUpload": true,
  "scheduleAt": "2026-04-01T12:00:00.000Z"
}
```

### Response

```json
{
  "jobId": "job_abc123",
  "status": "queued",
  "nextStep": "script.generate"
}
```

---

## 2) Get job details

`GET /jobs/:jobId`

### Response

```json
{
  "jobId": "job_abc123",
  "status": "running",
  "currentStep": "video.assemble",
  "steps": [
    { "name": "script.generate", "status": "completed" },
    { "name": "scene.breakdown", "status": "completed" },
    { "name": "video.assemble", "status": "running" }
  ],
  "artifacts": {
    "finalVideoUrl": null,
    "thumbnailUrl": null
  }
}
```

---

## 3) Retry a failed step

`POST /jobs/:jobId/retry`

```json
{
  "step": "voice.generate"
}
```

---

## 4) List jobs

`GET /jobs?status=failed&limit=20&cursor=...`

---

## 5) Schedule management

- `POST /schedules`
- `GET /schedules`
- `DELETE /schedules/:scheduleId`

---

## 6) YouTube integration

- `GET /youtube/oauth/start`
- `GET /youtube/oauth/callback`
- `POST /jobs/:jobId/upload`

---

## 7) Analytics

`GET /analytics/videos/:youtubeVideoId?range=30d`

### Response

```json
{
  "videoId": "yt_123",
  "range": "30d",
  "views": 18234,
  "ctr": 5.9,
  "watchTimeMinutes": 940,
  "avgViewDurationSec": 102
}
```

---

## Error shape

```json
{
  "error": {
    "code": "PROVIDER_RATE_LIMIT",
    "message": "Visual provider rate limit exceeded",
    "retryable": true,
    "requestId": "req_123"
  }
}
```

