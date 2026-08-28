"""
DB Migration Script — Bug Fixes B1, B2, B6
=============================================
Run this once against the live PostgreSQL DB to:
  1. Add SENIOR_CREDIT_MANAGER to the userrole enum  (B6)
  2. Drop + recreate FK constraints with ON DELETE SET NULL  (B1/B2)

Safe to run multiple times (idempotent for step 1 via pg_enum check).
"""
import os, psycopg2

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://loanadmin:loanpass123@localhost:5499/loan_eligibility_db"
)

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True        # DDL inside a normal tx is fine for these ops
cur = conn.cursor()

print("=== DB Migration: Bug fixes B1, B2, B6 ===")

# ── Step 1: Add SENIOR_CREDIT_MANAGER to userrole enum (B6) ──────────────────
cur.execute("""
    SELECT EXISTS (
        SELECT 1 FROM pg_enum
        JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
        WHERE pg_type.typname = 'userrole'
          AND pg_enum.enumlabel = 'SENIOR_CREDIT_MANAGER'
    );
""")
already_exists = cur.fetchone()[0]
if not already_exists:
    cur.execute("ALTER TYPE userrole ADD VALUE 'SENIOR_CREDIT_MANAGER';")
    print("[OK] Added SENIOR_CREDIT_MANAGER to userrole enum")
else:
    print("[SKIP] SENIOR_CREDIT_MANAGER already in userrole enum")

# ── Step 2: Fix audit_logs.user_id FK → ON DELETE SET NULL (B1) ──────────────
cur.execute("""
    SELECT constraint_name
    FROM information_schema.table_constraints
    WHERE table_name = 'audit_logs'
      AND constraint_type = 'FOREIGN KEY'
      AND constraint_name LIKE '%user_id%';
""")
fk_user = cur.fetchone()
if fk_user:
    cur.execute(f"ALTER TABLE audit_logs DROP CONSTRAINT {fk_user[0]};")
    cur.execute("""
        ALTER TABLE audit_logs
        ADD CONSTRAINT audit_logs_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    """)
    print("[OK] audit_logs.user_id FK updated to ON DELETE SET NULL")
else:
    print("[SKIP] audit_logs.user_id FK not found (may already be correct)")

# ── Step 3: Fix audit_logs.application_id FK → ON DELETE SET NULL (B1) ───────
cur.execute("""
    SELECT constraint_name
    FROM information_schema.table_constraints
    WHERE table_name = 'audit_logs'
      AND constraint_type = 'FOREIGN KEY'
      AND constraint_name LIKE '%application_id%';
""")
fk_app = cur.fetchone()
if fk_app:
    cur.execute(f"ALTER TABLE audit_logs DROP CONSTRAINT {fk_app[0]};")
    cur.execute("""
        ALTER TABLE audit_logs
        ADD CONSTRAINT audit_logs_application_id_fkey
        FOREIGN KEY (application_id) REFERENCES loan_applications(id) ON DELETE SET NULL;
    """)
    print("[OK] audit_logs.application_id FK updated to ON DELETE SET NULL")
else:
    print("[SKIP] audit_logs.application_id FK not found (may already be correct)")

# ── Step 4: Fix loan_applications.submitted_by_user_id FK → ON DELETE SET NULL (B2) ──
cur.execute("""
    SELECT constraint_name
    FROM information_schema.table_constraints
    WHERE table_name = 'loan_applications'
      AND constraint_type = 'FOREIGN KEY'
      AND constraint_name LIKE '%submitted_by%';
""")
fk_sub = cur.fetchone()
if fk_sub:
    cur.execute(f"ALTER TABLE loan_applications DROP CONSTRAINT {fk_sub[0]};")
    cur.execute("""
        ALTER TABLE loan_applications
        ADD CONSTRAINT loan_applications_submitted_by_user_id_fkey
        FOREIGN KEY (submitted_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
    """)
    print("[OK] loan_applications.submitted_by_user_id FK updated to ON DELETE SET NULL")
else:
    print("[SKIP] loan_applications.submitted_by_user_id FK not found")

cur.close()
conn.close()
print("\n=== Migration complete ===")
