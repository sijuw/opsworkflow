from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionResponse

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.post("", response_model=InstitutionResponse)
def create_institution(
    institution: InstitutionCreate,
    db: Session = Depends(get_db)
):
    new = Institution(**institution.model_dump())

    db.add(new)
    db.commit()
    db.refresh(new)

    return new

@router.get("", response_model=list[InstitutionResponse])
def get_institutions(db: Session = Depends(get_db)):
    return db.query(Institution).all()