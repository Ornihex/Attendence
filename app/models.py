from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str
    password: str


class UpdateCredentialsRequest(BaseModel):
    login: str | None = None
    password: str | None = None


class UpdateRoleRequest(BaseModel):
    role: str


class CreateTeacherRequest(BaseModel):
    login: str
    password: str


class CreateClassRequest(BaseModel):
    name: str
    teacher_id: int = Field(alias="teacherId")


class UpdateClassTeacherRequest(BaseModel):
    teacher_id: int = Field(alias="teacherId")


class ExcusedAbsenceRequest(BaseModel):
    full_name: str = Field(alias="fullName")
    reason: str


class AttendanceRequest(BaseModel):
    class_id: int = Field(alias="classId")
    total_students: int = Field(alias="totalStudents")
    present_count: int = Field(alias="presentCount")
    absent_unexcused: list[str] = Field(default_factory=list, alias="absentUnexcused")
    absent_excused: list[ExcusedAbsenceRequest] = Field(default_factory=list, alias="absentExcused")
