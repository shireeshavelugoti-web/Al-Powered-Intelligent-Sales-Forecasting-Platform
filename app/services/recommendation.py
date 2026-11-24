from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from ..database import get_db

from .. import models, schemas

from ..services.scoring_service import (
    calculate_score,
    predict_conversion_probability
)


router = APIRouter(
    prefix="/api/scoring",
    tags=["Lead Scoring"]
)


# CALCULATE LEAD SCORE

@router.post(
    "/predict/{lead_id}",
    response_model=schemas.ScoreOut
)
def score_lead(
    lead_id: int,
    payload: schemas.ScoreRequest,
    db: Session = Depends(get_db)
):

    lead = db.get(models.Lead, lead_id)

    if not lead:

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    factors = payload.model_dump()

    total, priority = calculate_score(factors)

    probability, source = predict_conversion_probability(
        factors
    )

    score = models.LeadScore(

        lead_id=lead_id,

        **factors,

        total_score=total,

        priority=priority,

        conversion_probability=probability,

        probability_source=source

    )

    db.add(score)

    db.commit()

    db.refresh(score)

    return score


# GET LATEST LEAD SCORE

@router.get(
    "/{lead_id}",
    response_model=schemas.ScoreOut
)
def get_score(
    lead_id: int,
    db: Session = Depends(get_db)
):

    if not db.get(models.Lead, lead_id):

        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    score = (

        db.query(models.LeadScore)

        .filter(
            models.LeadScore.lead_id == lead_id
        )

        .order_by(
            models.LeadScore.created_at.desc()
        )

        .first()

    )

    if not score:

        raise HTTPException(
            status_code=404,
            detail="Lead score not found"
        )

    return score