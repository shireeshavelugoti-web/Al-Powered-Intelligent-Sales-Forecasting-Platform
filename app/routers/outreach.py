from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from ..database import get_db

from .. import models, schemas

from ..services.ai_service import (
    generate_email,
    generate_recommendation
)


router = APIRouter(
    prefix="/api/outreach",
    tags=["Outreach Generation"]
)


def get_lead_data(lead):

    return {
        "company_name": lead.company_name,
        "industry": lead.industry,
        "contact_person": lead.contact_person,
        "email": lead.email,
        "website": lead.website,
        "employee_count": lead.employee_count,
        "location": lead.location,
        "description": lead.description,
        "technology_stack": lead.technology_stack
    }


# GENERATE PERSONALIZED EMAIL

@router.post(
    "/generate/{lead_id}",
    response_model=schemas.EmailOut
)
def create_email(
    lead_id: int,
    payload: schemas.EmailGenerationRequest,
    db: Session = Depends(get_db)
):

    lead = db.get(models.Lead, lead_id)

    if not lead:

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    try:

        result = generate_email(
            get_lead_data(lead),
            payload.service_offered,
            payload.tone,
            payload.additional_context
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Email generation failed: {str(exc)}"
        )

    email = models.OutreachEmail(

        lead_id=lead.id,

        recipient=lead.email,

        subject=result["subject"],

        body=result["body"],

        tone=payload.tone

    )

    db.add(email)

    db.commit()

    db.refresh(email)

    return email


# GET GENERATED EMAILS

@router.get(
    "/{lead_id}",
    response_model=list[schemas.EmailOut]
)
def get_emails(
    lead_id: int,
    db: Session = Depends(get_db)
):

    if not db.get(models.Lead, lead_id):

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    return (
        db.query(models.OutreachEmail)
        .filter(models.OutreachEmail.lead_id == lead_id)
        .order_by(models.OutreachEmail.created_at.desc())
        .all()
    )


# GENERATE OUTREACH RECOMMENDATION

@router.post(
    "/recommend/{lead_id}",
    response_model=schemas.RecommendationOut
)
def create_recommendation(
    lead_id: int,
    db: Session = Depends(get_db)
):

    lead = db.get(models.Lead, lead_id)

    if not lead:

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    score = (
        db.query(models.LeadScore)
        .filter(models.LeadScore.lead_id == lead_id)
        .order_by(models.LeadScore.created_at.desc())
        .first()
    )

    if not score:

        raise HTTPException(
            status_code=400,
            detail="Calculate lead score first"
        )

    try:

        result = generate_recommendation(
            get_lead_data(lead),
            score.total_score,
            score.priority
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Recommendation failed: {str(exc)}"
        )

    recommendation = models.OutreachRecommendation(

        lead_id=lead_id,

        channel=result["channel"],

        follow_up_timing=result["follow_up_timing"],

        strategy=result["strategy"],

        next_action=result["next_action"]

    )

    db.add(recommendation)

    db.commit()

    db.refresh(recommendation)

    return recommendation