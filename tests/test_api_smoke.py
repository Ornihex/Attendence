import subprocess
import time
from datetime import date

import pytest
import requests


BASE_URL = "http://127.0.0.1:8099"
API_URL = f"{BASE_URL}/api/v1"


def _wait_for_server(timeout_seconds: int = 20) -> None:
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
            "8099",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server()
        yield process
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def _request(method: str, path: str, expected_status: int, **kwargs):
    response = requests.request(method, f"{API_URL}{path}", timeout=30, **kwargs)
    assert (
        response.status_code == expected_status
    ), f"{method} {path} returned {response.status_code}, expected {expected_status}. Body: {response.text}"
    return response


def test_full_api_smoke(server_process):
    ts = int(time.time())
    teacher_login = f"teacher_{ts}"
    teacher_password = "pass1234"
    class_name = f"Class_{ts}"

    login_admin = _request(
        "POST",
        "/auth/login",
        200,
        json={"login": "admin", "password": "admin123"},
    )
    admin_token = login_admin.json()["accessToken"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    register_teacher = _request(
        "POST",
        "/users",
        201,
        headers=admin_headers,
        json={"login": teacher_login, "password": teacher_password},
    )
    teacher_id = register_teacher.json()["id"]

    _request("GET", "/users", 200, headers=admin_headers)

    updated_teacher_password = "pass12345"
    _request(
        "PATCH",
        f"/users/{teacher_id}/credentials",
        200,
        headers=admin_headers,
        json={"password": updated_teacher_password},
    )

    login_teacher = _request(
        "POST",
        "/auth/login",
        200,
        json={"login": teacher_login, "password": updated_teacher_password},
    )
    teacher_token = login_teacher.json()["accessToken"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    _request(
        "POST",
        "/classes",
        201,
        headers=admin_headers,
        json={"name": class_name, "teacherId": teacher_id},
    )

    classes_admin = _request("GET", "/classes", 200, headers=admin_headers)
    class_id = next((item["id"] for item in classes_admin.json() if item["name"] == class_name), None)
    assert class_id is not None, "Created class not found in GET /classes response"

    _request("GET", "/classes", 200, headers=teacher_headers)

    _request(
        "POST",
        f"/classes/{class_id}/students",
        201,
        headers=teacher_headers,
        json={"fullName": "Test Student"},
    )

    students_response = _request("GET", f"/classes/{class_id}/students", 200, headers=teacher_headers)
    students = students_response.json()
    assert students, "No students returned after creation"
    student_id = students[0]["id"]

    _request(
        "PATCH",
        f"/students/{student_id}",
        200,
        headers=teacher_headers,
        json={"isActive": True, "fullName": "Test Student Updated"},
    )

    today = date.today().isoformat()
    _request(
        "PUT",
        f"/attendance?date={today}",
        200,
        headers=teacher_headers,
        json={"classId": class_id, "records": [{"studentId": student_id, "status": "present"}]},
    )

    attendance_single = _request("GET", f"/attendance?date={today}&classId={class_id}", 200, headers=teacher_headers).json()
    assert "isFilled" in attendance_single, "Attendance response must include isFilled"
    assert attendance_single["isFilled"] is True
    admin_all_classes_attendance = _request("GET", f"/attendance?date={today}", 200, headers=admin_headers)
    assert isinstance(admin_all_classes_attendance.json(), list), "Admin attendance response without classId must be a list"
    assert any(item["classId"] == class_id for item in admin_all_classes_attendance.json()), "Created class not found in all-classes attendance response"
    _request(
        "GET",
        f"/statistics/weekly?startDate={today}&classId={class_id}",
        200,
        headers=teacher_headers,
    )
    admin_all_classes_weekly = _request(
        "GET",
        f"/statistics/weekly?startDate={today}",
        200,
        headers=admin_headers,
    )
    assert isinstance(admin_all_classes_weekly.json(), list), "Admin weekly statistics response without classId must be a list"
    assert any(item["classId"] == class_id for item in admin_all_classes_weekly.json()), "Created class not found in all-classes weekly statistics response"
