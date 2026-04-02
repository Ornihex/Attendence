# Attendance Domain Model (Current)

## Core idea
The system does not manage a roster of students per class for daily attendance.
Teacher fills attendance per date and class with:
- `totalStudents`: how many students should be in class list
- `presentCount`: how many are present
- absent students by name:
  - `absentUnexcused[]`
  - `absentExcused[]` with `reason`

## Data model
- `attendance_fill`
  - one record per (`date`, `class_id`)
  - stores `total_students`, `present_count`, and `filled_at`
  - source of truth for `isFilled`, totals and weekly aggregates
- `attendance`
  - records absent students by `absent_name`
  - status is `unexcused` or `excused`
  - `reason` is required for `excused`

## API contract
- `PUT /api/v1/attendance?date=YYYY-MM-DD`
  - body:
    - `classId`
    - `totalStudents`
    - `presentCount`
    - `absentUnexcused` (array of strings)
    - `absentExcused` (array of `{ fullName, reason }`)
- `GET /api/v1/attendance`
  - returns class/day payload with `isFilled`, totals and absent lists
- `GET /api/v1/statistics/weekly`
  - aggregates totals from `attendance_fill`

## Legacy note
- `students` table remains in DB as legacy compatibility artifact.
- It is not used in active attendance workflows.
