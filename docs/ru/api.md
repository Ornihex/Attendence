# API и модель данных

## Базовые принципы
Система хранит посещаемость по дате и классу без ежедневного поименного реестра всех учеников.

Основные поля отправки:
- `classId`
- `totalStudents`
- `presentCount`
- `absentUnexcused[]`
- `absentExcused[{ fullName, reason }]`

## Ключевые эндпоинты
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

## Формат ошибок
Для всех ошибок возвращается единый формат:
```json
{ "message": "..." }
```

## OpenAPI
Полная спецификация: [`openapi.yaml`](../../openapi.yaml)
