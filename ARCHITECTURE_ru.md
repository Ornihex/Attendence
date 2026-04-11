# Модель предметной области посещаемости (текущая)

## Ключевая идея
Система не ведёт поимённый список учеников класса для ежедневного заполнения посещаемости.
Учитель заполняет посещаемость за конкретную дату и класс через:
- `totalStudents`: сколько учеников должно быть по списку
- `presentCount`: сколько присутствует
- списки отсутствующих по фамилиям:
  - `absentUnexcused[]`
  - `absentExcused[]` с полем `reason`

## Модель данных
- `attendance_fill`
  - одна запись на пару (`date`, `class_id`)
  - хранит `total_students`, `present_count`, `filled_at`
  - источник истины для флага `isFilled` и численных итогов
- `attendance`
  - хранит отсутствующих по полю `absent_name`
  - `status`: `unexcused` или `excused`
  - для `excused` причина (`reason`) обязательна

## Контракт API
- `PUT /api/v1/attendance?date=YYYY-MM-DD`
  - body:
    - `classId`
    - `totalStudents`
    - `presentCount`
    - `absentUnexcused` (массив строк)
    - `absentExcused` (массив объектов `{ fullName, reason }`)
- `GET /api/v1/attendance`
  - возвращает данные по классу/дате: `isFilled`, численные показатели и списки отсутствующих
- `GET /api/v1/statistics/daily`
  - возвращает список отсутствующих за дату и общее число отсутствующих
- `GET /api/v1/attendance/unfilled-classes`
  - возвращает классы, по которым за дату нет отправленных данных

## Примечание по legacy
- Таблица `students` остаётся в БД как legacy-артефакт совместимости.
- В актуальных сценариях учёта посещаемости не используется.
