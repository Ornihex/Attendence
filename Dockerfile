FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY frontend ./frontend
COPY openapi.yaml ./openapi.yaml

EXPOSE 8080

CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn main:app --app-dir app --host 0.0.0.0 --port 8080"]
