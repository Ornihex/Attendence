import subprocess
import time
from datetime import date

import pytest
import requests


BASE_URL = "http://127.0.0.1:8099"
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
    response = requests.request(method, f"{API_URL}{path}", timeout=90, **kwargs)
    assert (
        response.status_code == expected_status
    ), f"{method} {path} returned {response.status_code}, expected {expected_status}. Body: {response.text}"
    return response


def test_full_api_smoke(server_process):
    ts = int(time.time())
    class_name = f"Class_{ts}"
    class_password = "pass1234"
    unfilled_class_name = f"Class_unfilled_{ts}"
    unfilled_class_password = "pass5678"

    login_admin = _request(
        "POST",
        "/auth/login",
        200,
        json={"login": "admin", "password": "admin123"},
    )
    admin_id = login_admin.json()["userId"]
    admin_token = login_admin.json()["accessToken"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    _request("POST", "/users", 410, headers=admin_headers)

    users_list = _request("GET", "/users", 200, headers=admin_headers).json()
    assert any("promotedBy" in item for item in users_list), "UserResponse must include promotedBy"

    _request(
        "POST",
        "/classes",
        201,
        headers=admin_headers,
        json={"name": class_name, "password": class_password},
    )
    _request(
        "POST",
        "/classes",
        201,
        headers=admin_headers,
        json={"name": unfilled_class_name, "password": unfilled_class_password},
    )

    classes_admin = _request("GET", "/classes", 200, headers=admin_headers)
    class_id = next((item["id"] for item in classes_admin.json() if item["name"] == class_name), None)
    unfilled_class_id = next((item["id"] for item in classes_admin.json() if item["name"] == unfilled_class_name), None)
    assert class_id is not None, "Created class not found in GET /classes response"
    assert unfilled_class_id is not None, "Second class not found in GET /classes response"

    users_after_create = _request("GET", "/users", 200, headers=admin_headers).json()
    class_user_id = next((u["id"] for u in users_after_create if u.get("classId") == class_id), None)
    assert class_user_id is not None, "Class account user must exist"

    updated_class_login = f"{class_name}_renamed"
    updated_class_password = "pass12345"
    _request(
        "PATCH",
        f"/classes/{class_id}/credentials",
        200,
        headers=admin_headers,
        json={"login": updated_class_login, "password": updated_class_password},
    )

    _request("DELETE", f"/classes/{unfilled_class_id}", 200, headers=admin_headers)
    classes_after_delete = _request("GET", "/classes", 200, headers=admin_headers).json()
    assert not any(item["id"] == unfilled_class_id for item in classes_after_delete)
    unfilled_class_id = None

    login_teacher = _request(
        "POST",
        "/auth/login",
        200,
        json={"login": updated_class_login, "password": updated_class_password},
    )
    teacher_token = login_teacher.json()["accessToken"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    _request("GET", "/classes", 200, headers=teacher_headers)

    today = date.today().isoformat()
    unfilled_attendance = _request(
        "GET",
        f"/attendance?date={today}&classId={class_id}",
        200,
        headers=teacher_headers,
    ).json()
    assert unfilled_attendance["isFilled"] is False
    assert unfilled_attendance["totalStudents"] == 0
    assert unfilled_attendance["presentCount"] == 0

    _request(
        "PUT",
        f"/attendance?date={today}",
        200,
        headers=teacher_headers,
        json={
            "totalStudents": 25,
            "presentCount": 23,
            "absentUnexcused": ["Ivanov"],
            "absentExcused": [{"fullName": "Petrov", "reason": "Болезнь"}],
        },
    )

    attendance_single = _request("GET", f"/attendance?date={today}&classId={class_id}", 200, headers=teacher_headers).json()
    assert "isFilled" in attendance_single, "Attendance response must include isFilled"
    assert attendance_single["isFilled"] is True
    assert attendance_single["totalStudents"] == 25
    assert attendance_single["presentCount"] == 23

    _request(
        "PUT",
        f"/attendance?date={today}",
        400,
        headers=teacher_headers,
        json={
            "totalStudents": 25,
            "presentCount": 24,
            "absentUnexcused": ["Sidorov", "Smirnov"],
            "absentExcused": [],
        },
    )
    _request(
        "PUT",
        f"/attendance?date={today}",
        400,
        headers=teacher_headers,
        json={
            "totalStudents": 25,
            "presentCount": 23,
            "absentUnexcused": ["Ivanov"],
            "absentExcused": [{"fullName": "Ivanov", "reason": "Болезнь"}],
        },
    )
    _request(
        "PUT",
        f"/attendance?date={today}",
        400,
        headers=teacher_headers,
        json={
            "totalStudents": 25,
            "presentCount": 24,
            "absentUnexcused": [],
            "absentExcused": [{"fullName": "Petrov", "reason": ""}],
        },
    )

    admin_all_classes_attendance = _request("GET", f"/attendance?date={today}", 200, headers=admin_headers)
    assert isinstance(admin_all_classes_attendance.json(), list), "Admin attendance response without classId must be a list"
    assert any(item["classId"] == class_id for item in admin_all_classes_attendance.json()), "Created class not found in all-classes attendance response"
    daily_stats = _request(
        "GET",
        f"/statistics/daily?date={today}&classId={class_id}",
        200,
        headers=teacher_headers,
    ).json()
    assert "totalAbsent" in daily_stats
    assert isinstance(daily_stats.get("absent"), list)
    teacher_all_classes_daily = _request(
        "GET",
        f"/statistics/daily?date={today}",
        200,
        headers=teacher_headers,
    ).json()
    assert isinstance(teacher_all_classes_daily, list), "Teacher daily statistics without classId must be a list"
    assert any(item["classId"] == class_id for item in teacher_all_classes_daily)

    admin_all_classes_daily = _request(
        "GET",
        f"/statistics/daily?date={today}",
        200,
        headers=admin_headers,
    )
    assert isinstance(admin_all_classes_daily.json(), list), "Admin daily statistics response without classId must be a list"
    assert any(item["classId"] == class_id for item in admin_all_classes_daily.json()), "Created class not found in all-classes daily statistics response"
    unfilled_classes = _request(
        "GET",
        f"/attendance/unfilled-classes?date={today}",
        200,
        headers=admin_headers,
    ).json()
    assert all("teacherId" in item for item in unfilled_classes)
    assert all("teacherLogin" in item for item in unfilled_classes)
    assert not any(item["id"] == class_id for item in unfilled_classes), "Filled class should not be returned in unfilled list"

    export_daily = _request(
        "GET",
        f"/statistics/daily/export?date={today}",
        200,
        headers=admin_headers,
    )
    assert export_daily.headers["Content-Type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert export_daily.content[:2] == b"PK", "XLSX payload must be a zip-based file"
    export_daily_csv = _request(
        "GET",
        f"/statistics/daily/export/csv?date={today}",
        200,
        headers=admin_headers,
    )
    assert export_daily_csv.headers["Content-Type"].startswith("text/csv")
    assert "Date,Class ID,Class Name,Full Name,Reason" in export_daily_csv.content.decode("utf-8-sig")

    _request(
        "PATCH",
        f"/users/{class_user_id}/role",
        200,
        headers=admin_headers,
        json={"role": "admin"},
    )

    promoted_admin_login = _request(
        "POST",
        "/auth/login",
        200,
        json={"login": updated_class_login, "password": updated_class_password},
    )
    promoted_admin_headers = {"Authorization": f"Bearer {promoted_admin_login.json()['accessToken']}"}

    new_promoted_password = "pass123456"
    _request(
        "PATCH",
        "/profile/credentials",
        200,
        headers=promoted_admin_headers,
        json={"password": new_promoted_password},
    )
    _request(
        "POST",
        "/auth/login",
        200,
        json={"login": updated_class_login, "password": new_promoted_password},
    )

    _request(
        "PATCH",
        f"/users/{admin_id}/role",
        403,
        headers=promoted_admin_headers,
        json={"role": "teacher"},
    )
