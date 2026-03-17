import json
import threading
import time
import unittest
from urllib.request import Request, urlopen

from app.main import run


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_thread = threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 8010}, daemon=True)
        cls.server_thread.start()
        time.sleep(1)

    def test_create_job_pipeline(self):
        payload = {
            "topic": "Success story of Elon Musk",
            "language": "en",
            "duration": "5_min",
            "style": "motivational",
            "auto_upload": True,
        }
        req = Request("http://127.0.0.1:8010/api/v1/jobs", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
        job_id = data["job_id"]

        status = data["status"]
        for _ in range(30):
            with urlopen(f"http://127.0.0.1:8010/api/v1/jobs/{job_id}") as resp:
                obj = json.loads(resp.read().decode())
            status = obj["status"]
            if status in {"uploaded", "completed", "failed"}:
                break
            time.sleep(0.2)

        self.assertIn(status, {"uploaded", "completed"})
        with urlopen(f"http://127.0.0.1:8010/api/v1/artifacts/{job_id}") as resp:
            files = json.loads(resp.read().decode())
        self.assertGreaterEqual(len(files), 4)

    def test_dashboard_ui_available(self):
        with urlopen("http://127.0.0.1:8010/") as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode()
        self.assertIn("Create Job", html)
        self.assertIn("jobForm", html)


if __name__ == "__main__":
    unittest.main()
