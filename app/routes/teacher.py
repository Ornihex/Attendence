from fastapi import APIRouter, Response
from db import engine, TeacherBase
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from models import Teacher
from utils.jwt import create_jwt
from datetime import timedelta
from uuid import uuid4
import bcrypt

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