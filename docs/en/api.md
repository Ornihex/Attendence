# API and Data Model

## Core model
Attendance is stored by class and date without a daily full student roster.

Main payload fields:
- `classId`
- `totalStudents`
- `presentCount`
- `absentUnexcused[]`
- `absentExcused[{ fullName, reason }]`

## Main endpoints
- `POST /api/v1/auth/login`
- `GET /api/v1/users`
- `POST /api/v1/users` (disabled, returns `410`)
- `PATCH /api/v1/users/{id}/credentials`
- `PATCH /api/v1/profile/credentials`
- `GET /api/v1/classes`
- `POST /api/v1/classes`
- `PATCH /api/v1/classes/{id}/credentials`
- `DELETE /api/v1/classes/{id}`
- `GET /api/v1/attendance`
- `PUT /api/v1/attendance?date=YYYY-MM-DD`
- `GET /api/v1/attendance/unfilled-classes?date=YYYY-MM-DD`
- `GET /api/v1/statistics/daily?date=YYYY-MM-DD`

## Error shape
All errors are normalized to:
```json
{ "message": "..." }
```

## OpenAPI
Full contract: [`openapi.yaml`](https://github.com/Ornihex/Attendence/blob/main/openapi.yaml)
