from pydantic import BaseModel, EmailStr, ValidationInfo, field_validator, ValidationError

class Teacher(BaseModel):
    name: str | None = None
    email: EmailStr
    password: str
    
    @field_validator('name')
    def validate_name(cls, v: str, info: ValidationInfo) -> str:
        path = info.context.get("path") if info.context else None
        
        if path == "/api/register_teacher":
            if not v:
                raise ValidationError("Name is required for registration")
        return v