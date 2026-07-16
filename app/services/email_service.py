from sqlalchemy.orm import Session

from app.models.institution import Institution


def get_institution(db: Session, institution_id: int):
    return (
        db.query(Institution)
        .filter(Institution.id == institution_id)
        .first()
    )