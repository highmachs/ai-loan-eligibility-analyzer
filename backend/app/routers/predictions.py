from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog, AuditAction
from app.models.loan_application import LoanApplication
from app.models.ai_prediction import AIPrediction, RiskLevel
from app.models.user import User
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.auth_service import get_current_user
from app.services.prediction_service import evaluate_risk

router = APIRouter(prefix="/api/predictions", tags=["AI Predictions"])


@router.get("/{application_id}", response_model=PredictionResponse)
def get_prediction(
    application_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    prediction = db.query(AIPrediction).filter(
        AIPrediction.application_id == application_id
    ).first()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction found for this application.",
        )
    return PredictionResponse(
        application_id=prediction.application_id,
        approval_probability=prediction.approval_probability,
        risk_level=prediction.risk_level,
        recommended_amount=prediction.recommended_amount,
        foir=prediction.foir,
        reason=prediction.reason,
    )


@router.post("/analyze", response_model=PredictionResponse)
def analyze_application(
    payload: PredictionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.query(LoanApplication).filter(
        LoanApplication.id == payload.application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application with id {payload.application_id} not found.",
        )

    customer = application.customer
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Application has no linked customer record.",
        )

    risk_level_str, approval_probability, reason, recommended_amount, foir = evaluate_risk(
        customer, application
    )

    existing = db.query(AIPrediction).filter(
        AIPrediction.application_id == payload.application_id
    ).first()

    if existing:
        existing.approval_probability = approval_probability
        existing.risk_level = RiskLevel(risk_level_str)
        existing.recommended_amount = recommended_amount
        existing.foir = foir
        existing.reason = reason
        prediction = existing
    else:
        prediction = AIPrediction(
            application_id=payload.application_id,
            approval_probability=approval_probability,
            risk_level=RiskLevel(risk_level_str),
            recommended_amount=recommended_amount,
            foir=foir,
            reason=reason,
        )
        db.add(prediction)

    db.commit()
    db.refresh(prediction)

    return PredictionResponse(
        application_id=prediction.application_id,
        approval_probability=prediction.approval_probability,
        risk_level=prediction.risk_level,
        recommended_amount=prediction.recommended_amount,
        foir=prediction.foir,
        reason=prediction.reason,
    )
