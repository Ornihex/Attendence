# Документация (RU)

## О проекте
Система предназначена для учета посещаемости с моделью:
- численность класса (`totalStudents`)
- количество присутствующих (`presentCount`)
- список отсутствующих (`absentUnexcused`, `absentExcused`)

## Стек
- FastAPI + Uvicorn
- SQLAlchemy + Alembic
- PostgreSQL
- Frontend SPA (`frontend/index.html`, `frontend/app.js`)
- Docker / Docker Compose

## Разделы
- [Запуск и настройка](setup.md)
- [API и модель данных](api.md)
- [Деплой сайта документации на GitHub Pages](pages.md)
