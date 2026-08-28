"""
Database Reset and Fresh Seed Script
====================================
Clears all application data, customer data, audit logs, and document records,
then re-seeds the standard test accounts with known credentials:

1. admin          / admin123    (Role: ADMIN)
2. scm_lead       / scm123      (Role: SENIOR_CREDIT_MANAGER)
3. scm1           / scm123      (Role: SENIOR_CREDIT_MANAGER)
4. officer_retail / officer123  (Role: LOAN_OFFICER)
5. officer1       / officer123  (Role: LOAN_OFFICER)
"""
import os
import psycopg2
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://loanadmin:loanpass123@localhost:5499/loan_eligibility_db"
)

def hash_pw(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")

def reset_and_seed():
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    print("Truncating tables (cleaning database)...")
    cur.execute("""
        TRUNCATE TABLE 
            audit_logs, 
            customer_documents, 
            ai_predictions, 
            loan_applications, 
            customers, 
            users 
        RESTART IDENTITY CASCADE;
    """)

    print("Seeding fresh test accounts...")
    accounts = [
        ("admin", "admin123", "ADMIN"),
        ("scm_lead", "scm123", "SENIOR_CREDIT_MANAGER"),
        ("scm1", "scm123", "SENIOR_CREDIT_MANAGER"),
        ("officer_retail", "officer123", "LOAN_OFFICER"),
        ("officer1", "officer123", "LOAN_OFFICER"),
    ]

    for username, plain_pw, role in accounts:
        hashed = hash_pw(plain_pw)
        cur.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s);",
            (username, hashed, role)
        )
        print(f"  [+] Created account: {username:<15} | Role: {role:<22} | Password: {plain_pw}")

    cur.close()
    conn.close()
    print("\nDatabase reset and seed complete! Ready for fresh walkthrough.")

if __name__ == "__main__":
    reset_and_seed()
