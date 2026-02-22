from datetime import date, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from db import AttendanceBase, AttendanceStatusEnum, ClassBase, RoleEnum, StudentBase, UserBase, engine
from models import (
    AttendanceRequest,
    CreateClassRequest,
    CreateStudentRequest,
    CreateTeacherRequest,
    LoginRequest,
    UpdateCredentialsRequest,
    UpdateRoleRequest,
    UpdateStudentRequest,
)
from utils.jwt import RANDOM_SECRET, create_jwt

router = APIRouter()
session = sessionmaker(engine)


def _role_value(role: RoleEnum | str) -> str:
    return role.value if isinstance(role, RoleEnum) else str(role)


def _get_token_payload(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        return jwt.decode(parts[1], RANDOM_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def _require_role(payload: dict, allowed: set[str]) -> None:
    role = payload.get("role")
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _get_current_user(s, payload: dict) -> UserBase:
    user = s.query(UserBase).filter(UserBase.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


def _resolve_class_for_user(payload: dict, requested_class_id: int | None) -> int:
    if requested_class_id is not None:
        return requested_class_id
    if payload["role"] == RoleEnum.admin.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="classId is required for admin")
    with session() as s:
        owned_class = (
            s.query(ClassBase)
            .filter(ClassBase.teacher_id == int(payload["sub"]))
            .order_by(ClassBase.id.asc())
            .first()
        )
        if not owned_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        return owned_class.id


def _attendance_for_class(s, current_date: date, class_id: int) -> dict:
    students = s.query(StudentBase).filter(StudentBase.class_id == class_id).all()
    attendance_rows = (
        s.query(AttendanceBase)
        .filter(and_(AttendanceBase.class_id == class_id, AttendanceBase.date == current_date))
        .all()
    )
    is_filled = len(attendance_rows) > 0
    status_by_student = {row.student_id: row.status.value for row in attendance_rows}
    records = [
        {
            "studentId": student.id,
            "fullName": student.full_name,
            "status": status_by_student.get(student.id, AttendanceStatusEnum.unexcused.value),
        }
        for student in students
    ]
    return {"date": current_date.isoformat(), "classId": class_id, "isFilled": is_filled, "records": records}


def _weekly_stats_for_class(s, class_id: int, start_date: date) -> dict:
    end_date = start_date + timedelta(days=6)
    students = s.query(StudentBase).filter(StudentBase.class_id == class_id).all()
    attendance_rows = (
        s.query(AttendanceBase)
        .filter(
            and_(
                AttendanceBase.class_id == class_id,
                AttendanceBase.date >= start_date,
                AttendanceBase.date <= end_date,
            )
        )
        .all()
    )
    by_student = {
        student.id: {
            "studentId": student.id,
            "fullName": student.full_name,
            "present": 0,
            "excused": 0,
            "unexcused": 0,
        }
        for student in students
    }
    summary = {"present": 0, "excused": 0, "unexcused": 0}
    for row in attendance_rows:
        key = row.status.value
        summary[key] += 1
        if row.student_id in by_student:
            by_student[row.student_id][key] += 1
    return {
        "classId": class_id,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "summary": summary,
        "students": list(by_student.values()),
    }


@router.post("/auth/login")
def login(credentials: LoginRequest):
    with session() as s:
        user = s.query(UserBase).filter(UserBase.login == credentials.login).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        try:
            password_ok = bcrypt.checkpw(credentials.password.encode("utf-8"), user.password.encode("utf-8"))
        except ValueError:
            # Hash in DB has invalid format; return auth error instead of 500.
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not password_ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        role = _role_value(user.role)
        access_token = create_jwt({"sub": str(user.id), "role": role}, timedelta(days=7))
        return {"accessToken": access_token, "role": role, "userId": user.id}


@router.get("/users")
def get_users(request: Request):
    payload = _get_token_payload(request)
    _require_role(payload, {RoleEnum.admin.value})
    with session() as s:
        users = s.query(UserBase).order_by(UserBase.id.asc()).all()
        class_rows = s.query(ClassBase.teacher_id, ClassBase.id).all()
        class_map = {teacher_id: class_id for teacher_id, class_id in class_rows}
        return [
            {
                "id": user.id,
                "login": user.login,
                "role": _role_value(user.role),
                "classId": class_map.get(user.id),
                "promotedBy": user.promoted_by,
            }
            for user in users
        ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def register_teacher(request: Request, payload: CreateTeacherRequest):
    token_payload = _get_token_payload(request)
    _require_role(token_payload, {RoleEnum.admin.value})
    with session() as s:
        hashed_password = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        teacher = UserBase(login=payload.login, password=hashed_password, role=RoleEnum.teacher)
        s.add(teacher)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login already exists")
        s.refresh(teacher)
        return {"id": teacher.id, "login": teacher.login, "role": _role_value(teacher.role), "classId": None}


@router.patch("/users/{id}/credentials")
def update_credentials(id: int, request: Request, payload: UpdateCredentialsRequest):
    token_payload = _get_token_payload(request)
    _require_role(token_payload, {RoleEnum.admin.value})
    if payload.login is None and payload.password is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided")
    with session() as s:
        teacher = s.query(UserBase).filter(and_(UserBase.id == id, UserBase.role == RoleEnum.teacher)).first()
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
        if payload.login is not None:
            teacher.login = payload.login
        if payload.password is not None:
            teacher.password = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login already exists")
        return {"message": "Updated"}


@router.patch("/profile/credentials")
def update_my_credentials(request: Request, payload: UpdateCredentialsRequest):
    token_payload = _get_token_payload(request)
    if payload.login is None and payload.password is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided")
    with session() as s:
        current_user = _get_current_user(s, token_payload)
        if payload.login is not None:
            current_user.login = payload.login
        if payload.password is not None:
            current_user.password = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login already exists")
        return {"message": "Updated"}


@router.patch("/users/{id}/role")
def update_user_role(id: int, request: Request, payload: UpdateRoleRequest):
    token_payload = _get_token_payload(request)
    _require_role(token_payload, {RoleEnum.admin.value})
    if payload.role not in {RoleEnum.teacher.value, RoleEnum.admin.value}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    with session() as s:
        actor = _get_current_user(s, token_payload)
        target = s.query(UserBase).filter(UserBase.id == id).first()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Appointed admin cannot change role of the admin who appointed them.
        if actor.promoted_by == target.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        new_role = RoleEnum(payload.role)
        target.role = new_role
        if new_role == RoleEnum.admin:
            target.promoted_by = actor.id
        else:
            target.promoted_by = None
        s.commit()
        return {"message": "Updated"}


@router.get("/classes")
def get_classes(request: Request):
    payload = _get_token_payload(request)
    with session() as s:
        if payload["role"] == RoleEnum.admin.value:
            class_rows = s.query(ClassBase).all()
        else:
            class_rows = s.query(ClassBase).filter(ClassBase.teacher_id == int(payload["sub"])).all()
        return [{"id": row.id, "name": row.name, "teacherId": row.teacher_id} for row in class_rows]


@router.post("/classes", status_code=status.HTTP_201_CREATED)
def create_class(request: Request, payload: CreateClassRequest):
    token_payload = _get_token_payload(request)
    _require_role(token_payload, {RoleEnum.admin.value})
    with session() as s:
        teacher = s.query(UserBase).filter(and_(UserBase.id == payload.teacher_id, UserBase.role == RoleEnum.teacher)).first()
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
        class_row = ClassBase(name=payload.name, teacher_id=payload.teacher_id)
        s.add(class_row)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Class name already exists")
        return {"message": "Class created"}


@router.get("/classes/{classId}/students")
def get_class_students(classId: int, request: Request):
    payload = _get_token_payload(request)
    with session() as s:
        class_row = s.query(ClassBase).filter(ClassBase.id == classId).first()
        if not class_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        if payload["role"] == RoleEnum.teacher.value and class_row.teacher_id != int(payload["sub"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        students = s.query(StudentBase).filter(StudentBase.class_id == classId).all()
        return [{"id": row.id, "fullName": row.full_name, "isActive": row.is_active} for row in students]


@router.post("/classes/{classId}/students", status_code=status.HTTP_201_CREATED)
def add_student(classId: int, request: Request, payload: CreateStudentRequest):
    token_payload = _get_token_payload(request)
    with session() as s:
        class_row = s.query(ClassBase).filter(ClassBase.id == classId).first()
        if not class_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        if token_payload["role"] == RoleEnum.teacher.value and class_row.teacher_id != int(token_payload["sub"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        student = StudentBase(class_id=classId, full_name=payload.full_name)
        s.add(student)
        s.commit()
        return {"message": "Student created"}


@router.patch("/students/{id}")
def update_student(id: int, request: Request, payload: UpdateStudentRequest):
    token_payload = _get_token_payload(request)
    with session() as s:
        student = s.query(StudentBase).filter(StudentBase.id == id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        class_row = s.query(ClassBase).filter(ClassBase.id == student.class_id).first()
        if token_payload["role"] == RoleEnum.teacher.value and class_row.teacher_id != int(token_payload["sub"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if payload.full_name is not None:
            student.full_name = payload.full_name
        if payload.is_active is not None:
            student.is_active = payload.is_active
        s.commit()
        return {"message": "Updated"}


@router.get("/attendance")
def get_attendance(date: date, request: Request, classId: int | None = None):
    token_payload = _get_token_payload(request)
    with session() as s:
        if classId is None and token_payload["role"] == RoleEnum.admin.value:
            class_rows = s.query(ClassBase).order_by(ClassBase.id.asc()).all()
            return [_attendance_for_class(s, date, row.id) for row in class_rows]

        resolved_class_id = _resolve_class_for_user(token_payload, classId)
        class_row = s.query(ClassBase).filter(ClassBase.id == resolved_class_id).first()
        if not class_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        if token_payload["role"] == RoleEnum.teacher.value and class_row.teacher_id != int(token_payload["sub"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return _attendance_for_class(s, date, resolved_class_id)


@router.put("/attendance")
def put_attendance(date: date, request: Request, payload: AttendanceRequest):
    token_payload = _get_token_payload(request)
    with session() as s:
        class_row = s.query(ClassBase).filter(ClassBase.id == payload.class_id).first()
        if not class_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        if token_payload["role"] == RoleEnum.teacher.value and class_row.teacher_id != int(token_payload["sub"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        valid_student_ids = {
            student_id
            for (student_id,) in s.query(StudentBase.id).filter(StudentBase.class_id == payload.class_id).all()
        }
        for record in payload.records:
            if record.student_id not in valid_student_ids:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid studentId")
            if record.status not in {x.value for x in AttendanceStatusEnum}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attendance status")
            row = (
                s.query(AttendanceBase)
                .filter(
                    and_(
                        AttendanceBase.date == date,
                        AttendanceBase.class_id == payload.class_id,
                        AttendanceBase.student_id == record.student_id,
                    )
                )
                .first()
            )
            if row:
                row.status = AttendanceStatusEnum(record.status)
            else:
                s.add(
                    AttendanceBase(
                        date=date,
                        class_id=payload.class_id,
                        student_id=record.student_id,
                        status=AttendanceStatusEnum(record.status),
                    )
                )
        s.commit()
        return {"message": "Saved"}


@router.get("/statistics/weekly")
def get_weekly_statistics(startDate: date, request: Request, classId: int | None = None):
    token_payload = _get_token_payload(request)
    with session() as s:
        if classId is None and token_payload["role"] == RoleEnum.admin.value:
            class_rows = s.query(ClassBase).order_by(ClassBase.id.asc()).all()
            return [_weekly_stats_for_class(s, row.id, startDate) for row in class_rows]

        resolved_class_id = _resolve_class_for_user(token_payload, classId)
        class_row = s.query(ClassBase).filter(ClassBase.id == resolved_class_id).first()
        if not class_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        if token_payload["role"] == RoleEnum.teacher.value and class_row.teacher_id != int(token_payload["sub"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return _weekly_stats_for_class(s, resolved_class_id, startDate)
