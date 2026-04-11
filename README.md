# Attendance Management Project

## Русский

### 1. Обзор
Это full-stack проект для учета посещаемости:
- backend на `FastAPI` с JWT-аутентификацией и ролями (`admin` / `teacher`);
- PostgreSQL + SQLAlchemy + Alembic;
- frontend SPA (`frontend/index.html`, `frontend/app.js`), раздается backend-ом;
- контракт API в `openapi.yaml`.

Текущая модель посещаемости: **численность + фамилии отсутствующих** (без поименного списка учеников на каждый день):
- `totalStudents`
- `presentCount`
- `absentUnexcused[]`
- `absentExcused[]` с `reason`

Подробности по доменной модели:
- `ARCHITECTURE.md` (EN)
- `ARCHITECTURE_ru.md` (RU)

### 2. Возможности
- Авторизация: `POST /api/v1/auth/login`
- Управление учителями (admin):
  - регистрация учителя
  - изменение credentials учителя
  - смена роли пользователя
- Управление классами (admin):
  - создание класса
  - перепривязка класса к другому учителю
  - удаление класса
- Посещаемость:
  - просмотр за дату/класс или по всем классам (admin)
  - сохранение/обновление посещаемости
  - получение списка незаполненных классов за дату
- Дневная статистика:
  - список отсутствующих за дату (опционально по конкретному классу)
  - общее число отсутствующих

### 3. Технологии
- Python 3.11+
- FastAPI / Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL (`psycopg2-binary`)
- JWT (`pyjwt`)
- Bcrypt
- Pytest + Requests
- Playwright (UI e2e)

### 4. Структура репозитория
```text
app/
  main.py                 # FastAPI, обработчики ошибок, раздача статики
  db.py                   # SQLAlchemy-модели, engine, сидинг админа
  models.py               # Pydantic-схемы запросов
  routes/teacher.py       # API-роуты (auth/users/classes/attendance/stats)
alembic/
  versions/               # Миграции
frontend/
  index.html              # Разметка SPA
  app.js                  # Логика SPA
  styles.css              # Стили SPA
tests/
  test_api_smoke.py
  test_ui_e2e_playwright.py
  test_openapi_contract.py
openapi.yaml              # Контракт API
```

### 5. Требования
- PostgreSQL
- Python 3.11+
- Для Windows: при необходимости разрешение на запуск скриптов PowerShell

### 6. Переменные окружения
Приложение читает переменные из `app/.env` (`load_dotenv("app/.env")`).

Рекомендуемые переменные:
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `SERVER_ADDRESS` (по умолчанию: `0.0.0.0:8080`)
- `ADMIN_LOGIN` (по умолчанию: `admin`)
- `ADMIN_PASSWORD` (по умолчанию: `admin123`)

Важно:
- не храните реальные секреты в Git;
- если секреты уже попали в историю, их нужно заменить.

### 7. Запуск проекта

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\venv\Scripts\alembic.exe upgrade head
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir app --host 127.0.0.1 --port 8080
```

#### Linux/macOS
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn main:app --app-dir app --host 127.0.0.1 --port 8080
```

Открыть:
- UI: `http://127.0.0.1:8080/`
- Swagger: `http://127.0.0.1:8080/docs`
- Проверка живости: `http://127.0.0.1:8080/api/ping`

### 8. Миграции (Alembic)
Основные команды:
```bash
alembic heads
alembic history
alembic upgrade head
alembic downgrade -1
```

В этом проекте Alembic берет строку подключения из `app/.env` через `alembic/env.py`, а не из статического значения `alembic.ini`.

### 9. Замечания по API
- Формат ошибок унифицирован:
```json
{ "message": "..." }
```
- JWT передается в заголовке:
```http
Authorization: Bearer <token>
```
- При сохранении посещаемости backend валидирует:
  - `presentCount <= totalStudents`
  - число отсутствующих равно `totalStudents - presentCount`
  - пустые фамилии не допускаются
  - дубли фамилий в одном запросе не допускаются
  - для уважительной причины поле `reason` обязательно

Ключевые роуты:
- `POST /api/v1/auth/login`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `PATCH /api/v1/users/{id}/credentials`
- `PATCH /api/v1/profile/credentials`
- `PATCH /api/v1/users/{id}/role`
- `GET /api/v1/classes`
- `POST /api/v1/classes`
- `PATCH /api/v1/classes/{id}/teacher`
- `DELETE /api/v1/classes/{id}`
- `GET /api/v1/attendance`
- `PUT /api/v1/attendance?date=YYYY-MM-DD`
- `GET /api/v1/attendance/unfilled-classes?date=YYYY-MM-DD`
- `GET /api/v1/statistics/daily?date=YYYY-MM-DD`

Полная схема: `openapi.yaml`.

### 10. Тестирование
#### Smoke API
```bash
python -m pytest -q tests/test_api_smoke.py
```

#### Проверка OpenAPI-контракта
```bash
python -m pytest -q tests/test_openapi_contract.py
```

#### UI e2e (Playwright)
Установка браузера (один раз):
```bash
python -m playwright install chromium
```
Запуск:
```bash
python -m pytest -q tests/test_ui_e2e_playwright.py
```

Полный прогон:
```bash
python -m pytest -q tests/test_api_smoke.py tests/test_ui_e2e_playwright.py tests/test_openapi_contract.py
```

### 11. Роли и безопасность
- Админ может повышать/понижать роли пользователей.
- Назначенный админ не может менять роль админа, который его назначил (`promoted_by` защита).
- Учитель работает только со своими классами.

### 12. Частые проблемы
- `401 Unauthorized` при логине:
  - проверьте логин/пароль
  - убедитесь, что применены миграции (`alembic upgrade head`)
- Не удается войти под админом после пересоздания БД:
  - примените миграции и перезапустите приложение (на старте создается default admin)
- Ошибка `alembic upgrade head`:
  - проверьте переменные `app/.env`
  - убедитесь, что PostgreSQL доступен и поддерживает требуемый SSL-режим
- Изменения фронтенда не видны:
  - выполните hard refresh
  - проверьте версию ассета `?v=...` в `frontend/index.html`

### 13. Docker
В проект добавлен рабочий контейнерный запуск:
- `Dockerfile` собирает backend + frontend и при старте выполняет `alembic upgrade head`.
- `docker-compose.yml` поднимает:
  - `db` (`postgres:16-alpine`)
  - `app` (FastAPI + миграции)

Быстрый старт:
```bash
docker compose up --build
```

Открыть:
- UI: `http://127.0.0.1:8080/`
- Swagger: `http://127.0.0.1:8080/docs`
- API ping: `http://127.0.0.1:8080/api/ping`

Остановить:
```bash
docker compose down
```

Остановить и удалить volume БД:
```bash
docker compose down -v
```

Примечания:
- Для compose используются локальные переменные БД:
  - `DB_HOST=db`, `DB_SSLMODE=disable`, `DB_CHANNEL_BINDING=prefer`
- Для внешней managed БД можно задать `DB_URL` целиком или свои `DB_*` переменные.

---

## English

### 1. Overview
This project is a full-stack attendance system for schools:
- `FastAPI` backend with JWT auth and role-based access (`admin` / `teacher`).
- PostgreSQL + SQLAlchemy + Alembic migrations.
- Frontend SPA (`frontend/index.html`, `frontend/app.js`) served by backend.
- API contract in `openapi.yaml`.

Current attendance model is **totals + absent names** (no per-student daily roster):
- `totalStudents`
- `presentCount`
- `absentUnexcused[]`
- `absentExcused[]` with `reason`

See architecture details:
- `ARCHITECTURE.md` (EN)
- `ARCHITECTURE_ru.md` (RU)

### 2. Features
- Authentication: `POST /api/v1/auth/login`
- Teacher management (admin):
  - create teacher
  - update teacher credentials
  - change user role
- Class management (admin):
  - create class
  - reassign class to another teacher
  - delete class
- Attendance:
  - get attendance by date/class or all classes (admin)
  - upsert attendance for class/date
  - get unfilled classes by date
- Daily statistics:
  - absent list for date (optionally for one class)
  - total absences count

### 3. Tech Stack
- Python 3.11+
- FastAPI / Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL (`psycopg2-binary`)
- JWT (`pyjwt`)
- Bcrypt
- Pytest + Requests
- Playwright (for UI e2e tests)

### 4. Repository Structure
```text
app/
  main.py                 # FastAPI app, exception handlers, static serving
  db.py                   # SQLAlchemy models + DB engine + admin seeding
  models.py               # Pydantic request models
  routes/teacher.py       # Main API routes (auth/users/classes/attendance/stats)
alembic/
  versions/               # DB migrations
frontend/
  index.html              # SPA markup
  app.js                  # SPA logic
  styles.css              # SPA styles
tests/
  test_api_smoke.py
  test_ui_e2e_playwright.py
  test_openapi_contract.py
openapi.yaml              # API contract
```

### 5. Prerequisites
- PostgreSQL database
- Python 3.11+
- On Windows: PowerShell execution policy allowing venv activation (if needed)

### 6. Environment Variables
The app loads variables from `app/.env` (`load_dotenv("app/.env")`).

Recommended variables:
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `SERVER_ADDRESS` (default: `0.0.0.0:8080`)
- `ADMIN_LOGIN` (default: `admin`)
- `ADMIN_PASSWORD` (default: `admin123`)

Important:
- Do not commit real DB credentials.
- Rotate secrets if credentials were exposed in Git history.

### 7. Setup and Run

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\venv\Scripts\alembic.exe upgrade head
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir app --host 127.0.0.1 --port 8080
```

#### Linux/macOS
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn main:app --app-dir app --host 127.0.0.1 --port 8080
```

Open:
- UI: `http://127.0.0.1:8080/`
- API docs: `http://127.0.0.1:8080/docs`
- Health check: `http://127.0.0.1:8080/api/ping`

### 8. Migrations (Alembic)
Main commands:
```bash
alembic heads
alembic history
alembic upgrade head
alembic downgrade -1
```

In this repo, Alembic reads DB URL from `app/.env` through `alembic/env.py`, not from static `alembic.ini`.

### 9. API Notes
- All errors are normalized to:
```json
{ "message": "..." }
```
- JWT must be passed as:
```http
Authorization: Bearer <token>
```
- For attendance save, backend validates:
  - `presentCount <= totalStudents`
  - absent count equals `totalStudents - presentCount`
  - no empty names
  - no duplicate names in one submission
  - excused absence requires `reason`

Primary routes:
- `POST /api/v1/auth/login`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `PATCH /api/v1/users/{id}/credentials`
- `PATCH /api/v1/profile/credentials`
- `PATCH /api/v1/users/{id}/role`
- `GET /api/v1/classes`
- `POST /api/v1/classes`
- `PATCH /api/v1/classes/{id}/teacher`
- `DELETE /api/v1/classes/{id}`
- `GET /api/v1/attendance`
- `PUT /api/v1/attendance?date=YYYY-MM-DD`
- `GET /api/v1/attendance/unfilled-classes?date=YYYY-MM-DD`
- `GET /api/v1/statistics/daily?date=YYYY-MM-DD`

See full schema in `openapi.yaml`.

### 10. Tests
#### API smoke
```bash
python -m pytest -q tests/test_api_smoke.py
```

#### OpenAPI contract checks
```bash
python -m pytest -q tests/test_openapi_contract.py
```

#### UI e2e (Playwright)
Install browser once:
```bash
python -m playwright install chromium
```
Run tests:
```bash
python -m pytest -q tests/test_ui_e2e_playwright.py
```

Run all:
```bash
python -m pytest -q tests/test_api_smoke.py tests/test_ui_e2e_playwright.py tests/test_openapi_contract.py
```

### 11. Role and Security Rules
- Admin can promote/demote users.
- If an admin was appointed by another admin, they cannot change role of the admin who appointed them (`promoted_by` protection).
- Teachers can work only with classes assigned to them.

### 12. Troubleshooting
- `401 Unauthorized` on login:
  - check credentials
  - ensure users table exists (`alembic upgrade head`)
- Admin login fails after DB reset:
  - run migrations, then restart app (startup seeds default admin)
- Alembic upgrade fails:
  - verify `app/.env` DB vars
  - ensure DB is reachable and SSL requirements are supported
- Frontend changes not visible:
  - hard refresh browser (cache)
  - verify static asset version query (`?v=...`) in `frontend/index.html`

### 13. Docker
This repository now includes a working container setup:
- `Dockerfile` builds backend + frontend and runs `alembic upgrade head` on startup.
- `docker-compose.yml` starts:
  - `db` (`postgres:16-alpine`)
  - `app` (FastAPI + migrations)

Quick start:
```bash
docker compose up --build
```

Open:
- UI: `http://127.0.0.1:8080/`
- Swagger: `http://127.0.0.1:8080/docs`
- API ping: `http://127.0.0.1:8080/api/ping`

Stop:
```bash
docker compose down
```

Stop and remove DB volume:
```bash
docker compose down -v
```

Notes:
- Compose uses local DB settings:
  - `DB_HOST=db`, `DB_SSLMODE=disable`, `DB_CHANNEL_BINDING=prefer`
- For managed external DBs, provide full `DB_URL` or custom `DB_*` variables.

---

