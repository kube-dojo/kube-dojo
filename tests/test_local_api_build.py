from __future__ import annotations

import http.client
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from threading import Thread
from unittest import mock


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

local_api = _load_module()

class LocalApiBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        local_api._reset_build_jobs_state()

    def tearDown(self) -> None:
        local_api._reset_build_jobs_state()
        self._tmpdir.cleanup()

    def _spawn_python_build(self, script: str) -> subprocess.Popen[str]:
        return subprocess.Popen([sys.executable, "-c", script], cwd=self.repo_root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    def _wait_for_job(self, job_id: str, timeout: float = 5.0) -> dict[str, object]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            status_code, payload, _ = local_api.get_build_job_status(self.repo_root, job_id)
            self.assertEqual(status_code, 200)
            if payload["state"] != "running":
                return payload
            time.sleep(0.05)
        self.fail(f"timed out waiting for build job {job_id}")

    def test_build_status_persists_warning_diff_from_previous_green(self) -> None:
        local_api._write_build_jobs(self.repo_root, [{
            "job_id": "build-prev",
            "started_at": 10.0,
            "state": "pass",
            "duration_s": 1.2,
            "finished_at": 11.2,
            "last_30_lines": ["Legacy warning"],
            "warning_set": ["Legacy warning"],
            "new_warnings": [],
        }])
        script = "import sys; print('Legacy warning', flush=True); print('Brand new warning', file=sys.stderr, flush=True)"
        with mock.patch.object(local_api, "_spawn_build_process", side_effect=lambda repo_root: self._spawn_python_build(script)):
            status_code, payload, content_type = local_api.route_post_request(self.repo_root, "/api/build/run")
        self.assertEqual((status_code, content_type.startswith("application/json")), (202, True))
        final_payload = self._wait_for_job(payload["job_id"])
        self.assertEqual((final_payload["state"], final_payload["new_warnings"]), ("pass", ["Brand new warning"]))
        self.assertEqual(final_payload["last_30_lines"][-2:], ["Legacy warning", "Brand new warning"])
        persisted_jobs = json.loads(local_api._build_jobs_path(self.repo_root).read_text(encoding="utf-8"))
        self.assertEqual((persisted_jobs[-1]["job_id"], persisted_jobs[-1]["new_warnings"]), (payload["job_id"], ["Brand new warning"]))
        endpoints = {entry["path"]: entry for entry in local_api.build_api_schema()["endpoints"]}
        self.assertEqual(endpoints["/api/build/run"]["method"], "POST")
        self.assertEqual(endpoints["/api/build/status"]["query"], ["job_id=..."])

    def test_second_post_returns_409_with_inflight_job_id_over_http(self) -> None:
        script = "import time; print('step 1', flush=True); time.sleep(0.4); print('step 2', flush=True)"
        with mock.patch.object(local_api, "_spawn_build_process", side_effect=lambda repo_root: self._spawn_python_build(script)):
            server = local_api.ThreadingHTTPServer(("127.0.0.1", 0), local_api.make_handler(self.repo_root))
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_address[1]
            self.addCleanup(server.shutdown)
            self.addCleanup(server.server_close)
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("POST", "/api/build/run")
            first = conn.getresponse()
            first_payload = json.loads(first.read().decode("utf-8"))
            self.assertEqual(first.status, 202)
            job_id = first_payload["job_id"]
            conn.request("POST", "/api/build/run")
            second = conn.getresponse()
            second_payload = json.loads(second.read().decode("utf-8"))
            self.assertEqual((second.status, second_payload["error"], second_payload["job_id"]), (409, "build_in_progress", job_id))
            conn.request("GET", f"/api/build/status?job_id={job_id}")
            status_response = conn.getresponse()
            status_payload = json.loads(status_response.read().decode("utf-8"))
            self.assertEqual((status_response.status, status_payload["job_id"]), (200, job_id))
            self.assertIn(status_payload["state"], {"running", "pass"})
            conn.close()
            self.assertEqual(self._wait_for_job(job_id)["state"], "pass")

    def test_build_jobs_ring_buffer_keeps_last_ten_entries(self) -> None:
        local_api._write_build_jobs(self.repo_root, [{
            "job_id": f"build-{idx}",
            "started_at": float(idx),
            "state": "pass",
            "duration_s": 1.0,
            "finished_at": float(idx) + 1.0,
            "last_30_lines": [f"job {idx}"],
            "warning_set": [],
            "new_warnings": [],
        } for idx in range(10)])
        with mock.patch.object(local_api, "_spawn_build_process", side_effect=lambda repo_root: self._spawn_python_build("print('fresh build', flush=True)")):
            status_code, payload, _ = local_api.route_post_request(self.repo_root, "/api/build/run")
        self.assertEqual(status_code, 202)
        self._wait_for_job(payload["job_id"])
        persisted_jobs = json.loads(local_api._build_jobs_path(self.repo_root).read_text(encoding="utf-8"))
        self.assertEqual((len(persisted_jobs), persisted_jobs[0]["job_id"], persisted_jobs[-1]["job_id"]), (10, "build-1", payload["job_id"]))
