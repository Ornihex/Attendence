from fastapi import APIRouter
from db import engine
from sqlalchemy.orm import sessionmaker


router = APIRouter()
session = sessionmaker(engine)


@router.post("/api/add_teacher")
async def add_teacher():
    pass