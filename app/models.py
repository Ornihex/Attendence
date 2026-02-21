from datetime import date

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str
    password: str


class UpdateCredentialsRequest(BaseModel):
    login: str | None = None
    password: str | None = None


class CreateTeacherRequest(BaseModel):
    login: str
    password: str


class CreateClassRequest(BaseModel):
    name: str
    teacher_id: int = Field(alias="teacherId")


class CreateStudentRequest(BaseModel):
    full_name: str = Field(alias="fullName")


class UpdateStudentRequest(BaseModel):
    full_name: str | None = Field(default=None, alias="fullName")
    is_active: bool | None = Field(default=None, alias="isActive")


class AttendanceRecordRequest(BaseModel):
    student_id: int = Field(alias="studentId")
    status: str


class AttendanceRequest(BaseModel):
    class_id: int = Field(alias="classId")
    records: list[AttendanceRecordRequest]


class WeeklyStatisticsQuery(BaseModel):
    start_date: date = Field(alias="startDate")
    class_id: int | None = Field(default=None, alias="classId")
