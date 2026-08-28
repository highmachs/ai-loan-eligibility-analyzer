from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
import app.models  # noqa: F401

from app.routers import auth, customers, loans, predictions, admin, documents, audit_logs

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intelligent Loan Eligibility Analyzer API",
    description="AI-powered loan risk evaluation system for Indian banking operations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(loans.router)
app.include_router(predictions.router)
app.include_router(admin.router)
app.include_router(documents.router)
app.include_router(audit_logs.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Loan Eligibility Analyzer API is running."}
