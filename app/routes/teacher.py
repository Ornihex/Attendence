from fastapi import APIRouter, Response, Request
from db import engine, TeacherBase, PupilBase, ClassBase, AttendanceBase
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from models import Teacher, Pupil, Class, Attendance
from utils.jwt import create_jwt, RANDOM_SECRET
from datetime import timedelta
from uuid import uuid4
import bcrypt
import jwt

router = APIRouter()
session = sessionmaker(engine)

@router.post("/api/register_teacher")
def register_teacher(teacher: Teacher, response: Response):
    teacher = teacher.model_validate(teacher.model_dump(), context={"path": "/api/register_teacher"})
    try:
        with session() as s:
            idx = str(uuid4())
            access_token = create_jwt({
                'sub': idx,
                'role': 'teacher'
            }, timedelta(days=7))
            hashed_password = bcrypt.hashpw(teacher.password.encode('utf-8'), bcrypt.gensalt())
            new_teacher = TeacherBase(
                id=idx,
                name=teacher.name,
                email=teacher.email,
                password=hashed_password.decode('utf-8')
            )
            s.add(new_teacher)
            s.commit()
        response.status_code = 201
        return {"message": "Teacher registered successfully",
                "access_token": access_token}
    except Exception as e:
        print(e)
        response.status_code = 500
        return {"message": "Internal server error"}
    
@router.post("/api/login_teacher")
def login_teacher(teacher: Teacher, response: Response):
    teacher = teacher.model_validate(teacher.model_dump(), context={"path": "/api/login_teacher"})
    try:
        with session() as s:
            statement = select(TeacherBase).where(TeacherBase.email == teacher.email)
            db_object = s.scalars(statement).one()
            if db_object:
                if bcrypt.checkpw(teacher.password.encode('utf-8'), db_object.password.encode('utf-8')):
                    access_token = create_jwt({
                        'sub': db_object.id,
                        'role': 'teacher'
                    }, timedelta(days=7))
                    response.status_code = 200
                    return {"message": "Teacher logged in successfully",
                            "access_token": access_token}
                else:
                    response.status_code = 401
                    return {"message": "Invalid credentials"}
            else:
                response.status_code = 404
                return {"message": "Teacher not found"}
    except Exception as e:
        print(e)
        response.status_code = 500
        return {"message": "Internal server error"}
    
@router.post("/api/add_pupil")
def add_pupil(pupil: Pupil, response: Response, request: Request):
    try:
        token = request.headers.get('Authorization').split()[1]
    except Exception as e:
        print(e)
        response.status_code = 401
        return {"message": "Unauthorized"}
    pupil = pupil.model_validate(pupil.model_dump(), context={"path": "/api/add_pupil"})
    try:
        data = jwt.decode(token, RANDOM_SECRET, algorithms=["HS256"])
        if data['role'] != 'teacher' and data["role"] != "admin":
            response.status_code = 403
            return {"message": "Forbidden"}
        with session() as s:
            idx = str(uuid4())
            new_pupil = PupilBase(
                id=idx,
                name=pupil.name,
                class_id=pupil.class_id,
            )
            s.add(new_pupil)
            s.commit()
        response.status_code = 201
        return {"message": "Pupil added successfully"}
    except Exception as e:
        print(e)
        response.status_code = 500
        return {"message": "Internal server error"}
    

@router.post("/api/add_class")
def add_class(class_: Class, response: Response, request: Request):
    try:
        token = request.headers.get('Authorization').split()[1]
    except Exception as e:
        print(e)
        response.status_code = 401
        return {"message": "Unauthorized"}
    class_ = class_.model_validate(class_.model_dump(), context={"path": "/api/add_class"})
    try:
        data = jwt.decode(token, RANDOM_SECRET, algorithms=["HS256"])
        if data['role'] != 'teacher' and data["role"] != "admin":
            response.status_code = 403
            return {"message": "Forbidden"}
        with session() as s:
            idx = str(uuid4())
            new_class = ClassBase(
                id=idx,
                name=class_.name,
                teacher_id=class_.teacher_id if data["role"] == "admin" else data["sub"],
            )
            s.add(new_class)
            s.commit()
        response.status_code = 201
        return {"message": "Class added successfully"}
    except Exception as e:
        print(e)
        response.status_code = 500
        return {"message": "Internal server error"}
    
    
@router.post("/api/add_attendance")
def add_attendance(attendance: Attendance, response: Response, request: Request):
    try:
        token = request.headers.get('Authorization').split()[1]
    except Exception as e:
        print(e)
        response.status_code = 401
        return {"message": "Unauthorized"}
    attendance = attendance.model_validate(attendance.model_dump(), context={"path": "/api/add_attendance"})
    try:
        data = jwt.decode(token, RANDOM_SECRET, algorithms=["HS256"])
        if data['role'] != 'teacher' and data["role"] != "admin":
            response.status_code = 403
            return {"message": "Forbidden"}
        with session() as s:
            idx = str(uuid4())
            new_attendance = AttendanceBase(
                id=idx,
                class_id=attendance.class_id,
                pupils=attendance.pupils,
            )
            s.add(new_attendance)
            s.commit()
        response.status_code = 201
        return {"message": "Attendance added successfully"}
    except Exception as e:
        print(e)
        response.status_code = 500
        return {"message":e}