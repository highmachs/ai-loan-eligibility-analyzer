from pydantic import BaseModel
from decimal import Decimal
from app.models.ai_prediction import RiskLevel


class PredictionRequest(BaseModel):
    application_id: int


class PredictionResponse(BaseModel):
    application_id: int
    approval_probability: Decimal
    risk_level: RiskLevel
    recommended_amount: Decimal
    foir: Decimal
    reason: str

    class Config:
        from_attributes = True
