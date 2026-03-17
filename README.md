# AI YouTube Automation Tool (Functional End-to-End App)

A working backend application that automates the complete YouTube content pipeline:

1. Input topic/style/language/duration
2. Script generation
3. Scene breakdown
4. Visual generation (mock assets)
5. Voiceover generation (mock asset)
6. Video assembly (manifest)
7. Thumbnail generation
8. SEO title/description/tags
9. YouTube upload (mock)
10. Analytics generation (mock)
11. Scheduling for autopilot posting

## Tech

- Python 3 standard library (no external runtime dependencies)
- SQLite for persistence
- Thread-based queue worker + scheduler

## Run

```bash
python -m app.main
```

Open:
- Dashboard: `http://127.0.0.1:8000/`
- API base: `http://127.0.0.1:8000/api/v1`

## Test

```bash
python -m unittest tests/test_app.py
```

## API examples

Create Job:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"topic":"Success story of Elon Musk","language":"en","duration":"5_min","style":"motivational","auto_upload":true}'
```

List Jobs:

```bash
curl http://127.0.0.1:8000/api/v1/jobs
```

See `how-to.txt` for full usage.
