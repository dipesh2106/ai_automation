# System Design

## 1) End-to-end pipeline

1. **Input Layer**
   - User submits topic, language, duration, style.
   - API validates payload and creates a `job` in MongoDB.
   - Orchestrator enqueues `script.generate` in BullMQ.

2. **Script Generation**
   - LLM prompt enforces structure: `HOOK`, `BODY`, `CTA`.
   - Output normalized into short TTS-friendly lines.

3. **Scene Breakdown**
   - LLM splits script into scene objects:
     - `sceneIndex`, `text`, `visualPrompt`, `emotion`, `durationSec`.

4. **Visual Generation**
   - Worker calls image/video provider per scene.
   - Assets uploaded to S3 and metadata persisted.

5. **Voiceover Generation**
   - Full script sent to ElevenLabs/Google TTS.
   - Audio stored in S3 and waveform metadata generated.

6. **Video Assembly**
   - FFmpeg pipeline stitches scene assets and voiceover.
   - Adds background music, subtitles, transitions, zoom effects.
   - Outputs final MP4 to S3.

7. **Thumbnail Generation**
   - AI proposes text + visual style.
   - Image generated and uploaded to S3.

8. **SEO Generation**
   - LLM returns title, description, tags, hashtags.

9. **YouTube Upload**
   - OAuth token selected for channel.
   - Upload MP4, set metadata and thumbnail.
   - Persist `youtubeVideoId` and publish status.

10. **Scheduling + Analytics**
    - Scheduler triggers queued publish windows.
    - Analytics worker pulls views, CTR, watch time from YouTube API.

---

## 2) Logical architecture

```txt
Client
  -> API Gateway / Backend API
      -> MongoDB (jobs, channels, assets, analytics)
      -> Redis + BullMQ (workflow queues)
      -> S3 (media artifacts)
      -> Worker Cluster (LLM/TTS/Visual/FFmpeg/YouTube)
      -> CloudFront (delivery)
```

---

## 3) Queue design

### Queues

- `job.create`
- `script.generate`
- `scene.breakdown`
- `visual.generate`
- `voice.generate`
- `video.assemble`
- `thumbnail.generate`
- `seo.generate`
- `youtube.upload`
- `analytics.sync`

### Retry policy (recommended)

- Provider timeouts: retries 3, exponential backoff.
- Rate-limit errors: retries 5, jitter + capped backoff.
- Validation errors: no retry, mark failed.

### Idempotency

Each queue payload includes:

- `jobId`
- `step`
- `attempt`
- `idempotencyKey` (`jobId:step:version`)

Workers should check if completed artifact exists before re-running.

---

## 4) MongoDB schema sketch

### `jobs`
- `_id`
- `topic`
- `language`
- `duration`
- `style`
- `status` (`queued | running | failed | completed | uploaded`)
- `currentStep`
- `createdAt`, `updatedAt`

### `job_steps`
- `_id`
- `jobId`
- `step`
- `status`
- `input`
- `output`
- `error`
- `startedAt`, `finishedAt`

### `assets`
- `_id`
- `jobId`
- `type` (`scene_image | scene_video | voice | subtitle | final_video | thumbnail`)
- `s3Key`
- `durationSec`
- `metadata`

### `youtube_channels`
- `_id`
- `ownerUserId`
- `channelId`
- `oauthTokens` (encrypted)
- `defaultLanguage`
- `postingSchedule`

### `analytics_daily`
- `_id`
- `youtubeVideoId`
- `date`
- `views`
- `ctr`
- `watchTimeMinutes`
- `avgViewDurationSec`

---

## 5) Observability and operations

- Correlation ID across API + workers.
- Structured logs for all provider calls.
- Metrics:
  - Step latency
  - Step success rate
  - Cost per video
  - Retry count per provider
- Alerts:
  - Queue lag spike
  - FFmpeg failure ratio
  - YouTube upload failures

---

## 6) Security

- Encrypt OAuth tokens at rest.
- Signed URLs for artifact access.
- Scoped API keys per provider.
- Redact prompts and PII in logs.

