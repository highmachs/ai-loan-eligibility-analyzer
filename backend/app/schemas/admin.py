from pydantic import BaseModel
from typing import List
from decimal import Decimal


class LoanApplicationSummary(BaseModel):
    total: int
    approved: int
    rejected: int
    pending: int


class RiskDistributionItem(BaseModel):
    risk_level: str
    count: int


class LoanTypeItem(BaseModel):
    loan_type: str
    count: int


class LoanAmountAnalysis(BaseModel):
    total_requested: Decimal
    total_recommended: Decimal
    average_loan: Decimal


class OfficerPerformanceItem(BaseModel):
    username: str
    applications: int
    approved: int
    rejected: int


class MonthlyStatItem(BaseModel):
    year: int
    month: int
    month_label: str   # e.g. "Aug 2026"
    total: int
    approved: int
    rejected: int
    pending: int


class AdminReportsResponse(BaseModel):
    summary: LoanApplicationSummary
    risk_distribution: List[RiskDistributionItem]
    loan_type_breakdown: List[LoanTypeItem]
    amount_analysis: LoanAmountAnalysis
    officer_performance: List[OfficerPerformanceItem]


class RetrainResponse(BaseModel):
    status: str
    output: str


class UserRoleUpdate(BaseModel):
    role: str  # "ADMIN" or "LOAN_OFFICER"
