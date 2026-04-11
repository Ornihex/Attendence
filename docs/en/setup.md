# Setup and Run

## Local run
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\venv\Scripts\alembic.exe upgrade head
.\venv\Scripts\python.exe -m uvicorn main:app --app-dir app --host 127.0.0.1 --port 8080
```

## Docker run
```bash
docker compose up --build
```

Services:
- UI: `http://127.0.0.1:8080/`
- Swagger: `http://127.0.0.1:8080/docs`
- API ping: `http://127.0.0.1:8080/api/ping`

Stop:
```bash
docker compose down
```

Remove DB volume:
```bash
docker compose down -v
```

## Environment variables
Main vars:
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_URL` (optional full DSN)
- `DB_SSLMODE`
- `DB_CHANNEL_BINDING`
- `ADMIN_LOGIN`
- `ADMIN_PASSWORD`
- `SERVER_ADDRESS`

## Alembic migrations
```bash
alembic heads
alembic history
alembic upgrade head
alembic downgrade -1
```
