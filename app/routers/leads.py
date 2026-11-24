from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from sqlalchemy import or_

from ..database import get_db

from .. import models, schemas


router = APIRouter(
    prefix="/api/leads",
    tags=["Lead Management"]
)


# CREATE LEAD

@router.post("/", response_model=schemas.LeadOut)
def create_lead(
    payload: schemas.LeadCreate,
    db: Session = Depends(get_db)
):

    lead = models.Lead(
        **payload.model_dump()
    )

    db.add(lead)

    db.commit()

    db.refresh(lead)

    return lead


# GET ALL LEADS

@router.get("/", response_model=list[schemas.LeadOut])
def get_leads(
    search: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):

    query = db.query(models.Lead)

    if search:

        term = f"%{search}%"

        query = query.filter(
            or_(
                models.Lead.company_name.ilike(term),
                models.Lead.industry.ilike(term),
                models.Lead.contact_person.ilike(term)
            )
        )

    if status:

        query = query.filter(
            models.Lead.status == status
        )

    return (
        query
        .order_by(models.Lead.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# GET SINGLE LEAD

@router.get("/{lead_id}", response_model=schemas.LeadOut)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):

    lead = db.get(models.Lead, lead_id)

    if not lead:

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    return lead


# UPDATE LEAD

@router.put("/{lead_id}", response_model=schemas.LeadOut)
def update_lead(
    lead_id: int,
    payload: schemas.LeadUpdate,
    db: Session = Depends(get_db)
):

    lead = db.get(models.Lead, lead_id)

    if not lead:

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    data = payload.model_dump(
        exclude_unset=True
    )

    for key, value in data.items():

        setattr(lead, key, value)

    db.commit()

    db.refresh(lead)

    return lead


# DELETE LEAD

@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):

    lead = db.get(models.Lead, lead_id)

    if not lead:

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    db.delete(lead)

    db.commit()

    return {
        "message": "Lead deleted successfully"
    }