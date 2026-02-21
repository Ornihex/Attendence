import subprocess
import time
from datetime import date

import pytest
import requests
from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8101"
API_URL = f"{BASE_URL}/api/v1"


def _wait_for_server(timeout_seconds: int = 25) -> None:
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


def _api_request(method: str, path: str, expected_status: int, **kwargs):
    response = requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
    assert (
        response.status_code == expected_status
    ), f"{method} {path} returned {response.status_code}, expected {expected_status}. Body: {response.text}"
    return response


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
            "8101",
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


@pytest.fixture()
def seeded_teacher(server_process):
    ts = int(time.time())
    teacher_login = f"ui_teacher_{ts}"
    teacher_password = "pass1234"
    class_name = f"UI_Class_{ts}"

    login_admin = _api_request(
        "POST",
        "/auth/login",
        200,
        json={"login": "admin", "password": "admin123"},
    )
    admin_token = login_admin.json()["accessToken"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    register_teacher = _api_request(
        "POST",
        "/users",
        201,
        headers=admin_headers,
        json={"login": teacher_login, "password": teacher_password},
    )
    teacher_id = register_teacher.json()["id"]

    _api_request(
        "POST",
        "/classes",
        201,
        headers=admin_headers,
        json={"name": class_name, "teacherId": teacher_id},
    )
    classes = _api_request("GET", "/classes", 200, headers=admin_headers).json()
    class_id = next(item["id"] for item in classes if item["name"] == class_name)

    login_teacher = _api_request(
        "POST",
        "/auth/login",
        200,
        json={"login": teacher_login, "password": teacher_password},
    )
    teacher_token = login_teacher.json()["accessToken"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    _api_request(
        "POST",
        f"/classes/{class_id}/students",
        201,
        headers=teacher_headers,
        json={"fullName": "UI Student 1"},
    )
    _api_request(
        "POST",
        f"/classes/{class_id}/students",
        201,
        headers=teacher_headers,
        json={"fullName": "UI Student 2"},
    )
    return {
        "teacher_login": teacher_login,
        "teacher_password": teacher_password,
        "class_id": class_id,
        "teacher_headers": teacher_headers,
    }


def test_ui_bulk_attendance_update(seeded_teacher):
    today = date.today().isoformat()
    teacher_login = seeded_teacher["teacher_login"]
    teacher_password = seeded_teacher["teacher_password"]
    class_id = seeded_teacher["class_id"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.fill("#apiBase", API_URL)
        page.fill("#login", teacher_login)
        page.fill("#password", teacher_password)
        page.click("#loginForm button[type='submit']")

        page.wait_for_selector("#appView:not(.hidden)")
        page.click("button[data-tab='attendanceTab']")
        page.wait_for_selector("#attendanceTab.active")

        page.fill("#attendanceEditDate", today)
        page.select_option("#attendanceEditClassId", str(class_id))
        page.click("#attendanceEditForm button[type='submit']")

        page.wait_for_selector(".attendance-status-select")
        page.click("#setAllPresent")
        page.click("#attendanceSaveBtn")
        page.wait_for_function(
            "() => { const t = document.getElementById('toast'); return t && t.textContent.includes('сохранена'); }"
        )

        browser.close()

    verify = _api_request(
        "GET",
        f"/attendance?date={today}&classId={class_id}",
        200,
        headers=seeded_teacher["teacher_headers"],
    ).json()
    assert verify["records"], "Attendance records are empty after UI save"
    assert all(item["status"] == "present" for item in verify["records"])
