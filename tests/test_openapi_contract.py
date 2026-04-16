import subprocess
import time
from datetime import date
from pathlib import Path

import pytest
import requests


BASE_URL = "http://127.0.0.1:8102"
API_URL = f"{BASE_URL}/api/v1"


def _wait_for_server(timeout_seconds: int = 45) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(f"{BASE_URL}/api/ping", timeout=1)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.25)
    raise RuntimeError("Server did not start within timeout")


@pytest.fixture(scope="session")
def server_process():
    process = subprocess.Popen(
        [
            r".\venv\Scripts\python.exe",
            "-m",
            "uvicorn",
            "main:app",
            "--app-dir",
            "app",
            "--host",
            "127.0.0.1",
            "--port",
            "8102",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server()
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def _request(method: str, path: str, expected_status: int, **kwargs):
    response = requests.request(method, f"{API_URL}{path}", timeout=30, **kwargs)
    assert response.status_code == expected_status, response.text
    return response


def test_openapi_yaml_contains_new_attendance_contract():
    spec = Path("openapi.yaml").read_text(encoding="utf-8")
    assert "/classes/{classId}/students:" not in spec
    assert "/students/{id}:" not in spec
    assert "absentUnexcused" in spec
    assert "absentExcused" in spec
    assert "totalStudents" in spec
    assert "presentCount" in spec
    assert "ErrorResponse" in spec
    assert "required: [message]" in spec
    assert "/attendance/unfilled-classes:" in spec
    assert "UnfilledClassResponse" in spec
    assert "/classes/{id}/teacher:" in spec
    assert "/classes/{id}:" in spec
    assert "UpdateClassTeacherRequest" in spec
    assert "/statistics/daily/export:" in spec
    assert "/statistics/daily/export/csv:" in spec


def test_runtime_error_shape_and_attendance_fields(server_process):
    login = _request("POST", "/auth/login", 200, json={"login": "admin", "password": "admin123"}).json()
    headers = {"Authorization": f"Bearer {login['accessToken']}"}
    today = date.today().isoformat()

    invalid = _request(
        "PUT",
        f"/attendance?date={today}",
        404,
        headers=headers,
        json={"classId": 999999, "totalStudents": 1, "presentCount": 1, "absentUnexcused": [], "absentExcused": []},
    ).json()
    assert "message" in invalid
    assert isinstance(invalid["message"], str)

    classes = _request("GET", "/classes", 200, headers=headers).json()
    unfilled = _request("GET", f"/attendance/unfilled-classes?date={today}", 200, headers=headers).json()
    assert isinstance(unfilled, list)
    if classes:
        class_id = classes[0]["id"]
        attendance = _request(
            "GET",
            f"/attendance?date={today}&classId={class_id}",
            200,
            headers=headers,
        ).json()
        for key in ("date", "classId", "isFilled", "totalStudents", "presentCount", "absentUnexcused", "absentExcused"):
            assert key in attendance
