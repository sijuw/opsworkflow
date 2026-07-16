from pydantic import BaseModel, EmailStr


class InstitutionCreate(BaseModel):
    name: str
    bank_id: int
    email_to: str
    email_cc: str | None = None


class InstitutionResponse(InstitutionCreate):
    id: int
    # active: bool

    class Config:
        from_attributes = True