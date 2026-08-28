# Phase 3 Technical & Capability Report: Intelligent Loan Eligibility Analyzer

**Project Name:** Intelligent Loan Eligibility Analyzer  
**Phase:** Phase 3 — Enterprise Governance, Multi-Tier Approval Hierarchy, Document Verification & Compliance Audit  
**Author:** Samarjeeth  
**Technology Stack:** FastAPI (Python 3.10+), PostgreSQL 15, React 18, scikit-learn & SHAP, JWT Bearer RBAC, bcrypt  
**Target Specification:** `LoanEligibilityAnalyzer.md`  
**Status:** Verification Completed & Production Ready  

---

## 1. System Overview & Functional Architecture

The **Intelligent Loan Eligibility Analyzer** is a multi-tier banking credit evaluation and loan workflow automation platform. Following the implementation of Phase 1 (Rule-Based Decisioning & FOIR) and Phase 2 (Machine Learning with Random Forest & SHAP Feature Explanations), **Phase 3** implements the enterprise governance, regulatory audit compliance, multi-tiered credit committee approval hierarchies, and customer document tracking layers.

```

                                       SYSTEM ARCHITECTURE                                        

                                                 
                                 
                                    React 18 Single Page App    
                                   • Strict Form Validation     
                                   • Role-Based Dynamic Views   
                                   • Pure CSS Time-Series Viz   
                                 
                                                  REST API / JWT Bearer Tokens
                                 
                                      FastAPI Gateway Server    
                                   • RBAC Route Guards (401/403)
                                   • Strict Pydantic Contracts  
                                   • SQL Parameterization (ORM) 
                                 
                                                 
                   
                                                                             
     
       PostgreSQL 15 Database        ML & Decisioning Core       Audit & Compliance Engine   
    • Users & 3-Tier Roles          • RandomForestClassifier   • Immutable Action Trail      
    • Customers & Portfolios        • TreeExplainer (SHAP)     • State-Change Deltas         
    • Loan Applications             • FOIR Headroom Engine     • Actor Attribution & IPs     
    • Document Verification Logs    • Dynamic In-Memory Sync   • Cascading Integrity Guards  
     
```

---

## 2. Comprehensive Functional Capabilities

### 2.1 Multi-Tier Credit Committee Approval Hierarchy
To align with Indian banking credit committee policies, loan approval limits are enforced across three distinct operational tiers. Approval checks are executed both at the backend API layer (`PATCH /api/loans/{id}/status`) and dynamically reflected on the client UI:

| Approval Tier | User Role | Maximum Approval Limit | Operational Scope & Escalation Policy |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `LOAN_OFFICER` | Up to **₹5,00,000** (₹5 Lakhs) | Can auto-approve standard retail applications up to ₹5 Lakhs. Applications above ₹5 Lakhs require escalation to Senior Credit Manager or Admin. |
| **Tier 2** | `SENIOR_CREDIT_MANAGER` | Up to **₹25,00,000** (₹25 Lakhs) | Authorized to evaluate and approve medium-to-large loans up to ₹25 Lakhs. Applications above ₹25 Lakhs escalate to Credit Committee / Admin. |
| **Tier 3** | `ADMIN` / Credit Committee | **Unlimited** (Up to ₹10 Crore cap) | Final institutional signing authority for high-value applications or policy exception reviews. |

#### Backend Validation & Security Rules:
* If a `LOAN_OFFICER` attempts to approve a loan $> ₹5,00,000$, the backend raises an `HTTP 403 Forbidden` with a detailed error:  
  `"Loan Officers can only approve loans up to ₹5,00,000. This application (₹X) requires a Senior Credit Manager or Admin."`
* If a `SENIOR_CREDIT_MANAGER` attempts to approve a loan $> ₹25,00,000$, the backend raises an `HTTP 403 Forbidden`:  
  `"Senior Credit Managers can only approve loans up to ₹25,00,000. This application (₹X) requires Admin / Credit Committee approval."`

---

### 2.2 User Management & Role-Based Access Control (RBAC)
An administrative portal allowing designated Admins to manage system credentials, assign operational roles, and enforce security policies:

* **Endpoints:**
  * `GET /api/admin/users` — List all registered operators, system IDs, usernames, and role assignments.
  * `POST /api/admin/users` — Provision new user accounts with encrypted passwords (bcrypt) and specified roles.
  * `PATCH /api/admin/users/{id}/role` — Promote or demote an operator (`LOAN_OFFICER` $\leftrightarrow$ `SENIOR_CREDIT_MANAGER` $\leftrightarrow$ `ADMIN`).
  * `DELETE /api/admin/users/{id}` — Decommission operator accounts.
* **Database Referential Integrity:**
  * Deleting a user account executes an automatic foreign key nullification (`ON DELETE SET NULL`) across `loan_applications.submitted_by_user_id` and `audit_logs.user_id`, ensuring historical loan and audit records remain intact without violating foreign key constraints.
  * Self-deletion and self-demotion guards prevent administrators from locking themselves out of the system.

---

### 2.3 Customer Historical Portfolio & Lifetime Metrics
Provides credit underwriters and branch managers with visibility into an applicant's complete borrowing history across all past loan applications:

* **Endpoint:** `GET /api/customers/{customer_id}/loans`
* **Underwriter Metrics:**
  * Total Applications Submitted
  * Approved Loans Count
  * Rejected Applications Count
  * Pending Applications Count
  * Aggregate Requested Amount vs. Cumulative Borrowed Exposure
* **Business Purpose:** Allows underwriters to identify recurring borrowing patterns, previous loan rejections, and cumulative institutional debt exposure before making credit decisions.

---

### 2.4 Customer Document Verification Workflow
Tracks Know-Your-Customer (KYC) and income verification documents under the `customer_documents` database entity without requiring external cloud storage dependencies:

* **Supported Document Types:**
  1. `PAN_CARD` — Permanent Account Number verification.
  2. `AADHAAR` — Masked Aadhaar identity verification.
  3. `FORM_16` — Employer tax deduction & annual income certificate (ITR).
  4. `BANK_STATEMENT` — 6-Month transactional banking history.
* **Verification Status States:** `PENDING` $\rightarrow$ `VERIFIED` or `REJECTED`.
* **Traceability Metadata:** Each document record stores the document identification number, verification status, verifying operator ID, and timestamp.

---

### 2.5 Regulatory Compliance Audit Trail
Maintains an immutable, sequential audit ledger recording all significant state mutations across the application lifecycle:

* **Logged System Actions:**
  * `CREATED` — Initial loan application creation.
  * `AI_SCORED` — Real-time risk scoring and SHAP explanation generation.
  * `APPROVED` — Application approval action.
  * `REJECTED` — Application rejection action.
  * `DOCUMENT_VERIFIED` — Verification of KYC or financial document.
  * `DOCUMENT_REJECTED` — Rejection of invalid document submission.
* **Audit Record Schema:**
  * `user_id` — Operator ID who executed the action.
  * `application_id` — Associated loan application reference.
  * `action` — Specific action enum.
  * `previous_status` — Pre-mutation status.
  * `new_status` — Post-mutation status.
  * `ip_address` — Client IP address captured from HTTP request.
  * `timestamp` — Server-generated UTC timestamp.
* **Search & Filter:** Admin interface provides instant filtering by Application ID.

---

### 2.6 Monthly Approvals Trend & Business Analytics
Provides management reporting on business volume, portfolio risk, and application throughput over a rolling 12-month window:

* **Rolling 12-Month Query Filter:** `created_date >= NOW() - INTERVAL '365 days'` ensures accurate time-series reporting.
* **Aggregated Metrics:**
  * Total Applications per Month
  * Approved Volume per Month
  * Rejected Volume per Month
  * Pending Volume per Month
* **Visual Representation:** CSS-driven stacked column visualization rendering volume distribution per calendar month without third-party charting package bloat.

---

### 2.7 Application Deduplication Engine
An automated database maintenance utility that scans for duplicate loan applications submitted for the same customer, loan type, requested amount, and tenure:

* **Endpoint:** `DELETE /api/loans/duplicates`
* **Canonical Preservation Rule:** Identifies unique combinations of `(customer_id, loan_type, requested_amount, tenure_months)` and preserves the earliest record (lowest primary key ID) while permanently removing redundant duplicate rows and their associated prediction records.

---

## 3. Database Schema & Data Contracts

### 3.1 PostgreSQL Database Schema Definitions

```sql
-- USERS TABLE
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    role VARCHAR NOT NULL DEFAULT 'LOAN_OFFICER'
);

-- CUSTOMERS TABLE
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 18 AND age <= 75),
    gender VARCHAR NOT NULL,
    marital_status VARCHAR NOT NULL,
    occupation VARCHAR NOT NULL,
    company_name VARCHAR,
    employment_type VARCHAR NOT NULL,
    years_of_experience INTEGER NOT NULL CHECK (years_of_experience >= 0),
    monthly_salary NUMERIC(12, 2) NOT NULL CHECK (monthly_salary > 0),
    other_income NUMERIC(12, 2) DEFAULT 0,
    existing_emi NUMERIC(12, 2) NOT NULL CHECK (existing_emi >= 0),
    current_loans INTEGER NOT NULL CHECK (current_loans >= 0),
    credit_score INTEGER NOT NULL CHECK (credit_score >= 300 AND credit_score <= 900),
    missed_payments INTEGER NOT NULL CHECK (missed_payments >= 0),
    repayment_history VARCHAR
);

-- LOAN APPLICATIONS TABLE
CREATE TABLE loan_applications (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    loan_type VARCHAR NOT NULL,
    requested_amount NUMERIC(14, 2) NOT NULL CHECK (requested_amount > 0 AND requested_amount <= 100000000),
    tenure_months INTEGER NOT NULL CHECK (tenure_months >= 6 AND tenure_months <= 360),
    status VARCHAR NOT NULL DEFAULT 'PENDING',
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    submitted_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- AI PREDICTIONS TABLE
CREATE TABLE ai_predictions (
    id SERIAL PRIMARY KEY,
    application_id INTEGER UNIQUE NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    approval_probability NUMERIC(5, 2) NOT NULL,
    risk_level VARCHAR NOT NULL,
    recommended_amount NUMERIC(14, 2) NOT NULL,
    foir NUMERIC(5, 2) NOT NULL,
    reason TEXT NOT NULL
);

-- CUSTOMER DOCUMENTS TABLE
CREATE TABLE customer_documents (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    document_type VARCHAR NOT NULL,
    document_number VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'PENDING',
    verified_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AUDIT LOGS TABLE
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    application_id INTEGER REFERENCES loan_applications(id) ON DELETE SET NULL,
    action VARCHAR NOT NULL,
    previous_status VARCHAR,
    new_status VARCHAR,
    ip_address VARCHAR,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Visual Interface Walkthrough & Screenshots

Below is the verified visual evidence documenting each Phase 3 user interface component. All images are hosted within the project codebase under `./docs/images/phase3/`.

### 4.1 User Management Portal (`/admin/users`)
*Interface for creating accounts, assigning roles (`LOAN_OFFICER`, `SENIOR_CREDIT_MANAGER`, `ADMIN`), and managing user access.*

![User Management](./docs/images/phase3/01_user_management.png)

---

### 4.2 System Audit Logs Portal (`/admin/audit-logs`)
*Immutable event history tracking full application lifecycles from creation (`CREATED`) to AI scoring (`AI_SCORED`), document verifications (`DOCUMENT_VERIFIED`), and decisioning (`APPROVED`/`REJECTED`).*

![System Audit Logs](./docs/images/phase3/02_audit_logs.png)

---

### 4.3 Admin Reports & 12-Month Approvals Trend (`/admin`)
*Consolidated analytics covering application summaries, risk distribution, amount metrics, rolling 12-month approval trends, and officer performance.*

![Admin Reports](./docs/images/phase3/03_admin_reports_trends.png)

---

### 4.4 Customer Historical Portfolio (`/customers/:id/history`)
*Customer profile summary, aggregate loan performance counters, and complete historical applications ledger.*

![Customer History](./docs/images/phase3/04_customer_history.png)

---

### 4.5 Customer Document Verification Portal (`/documents/:customerId`)
*KYC and income documentation verification interface with status badges and officer attribution.*

![Document Manager](./docs/images/phase3/05_document_manager.png)

---

### 4.6 AI Prediction & 3-Tier Approval Gate (`/prediction/:loanId`)
*AI approval probability, SHAP feature impact reasons, FOIR calculation, and 3-tier decisioning buttons.*

![AI Prediction Result - Pending](./docs/images/phase3/06_ai_prediction_3tier_approval.png)

---

### 4.7 Approved Application State (`/prediction/:loanId`)
*Application updated to Approved state with audit log record generated.*

![AI Prediction Result - Approved](./docs/images/phase3/07_ai_prediction_approved.png)

---

### 4.8 Loan Officer Dashboard (`/dashboard`)
*Real-time statistics grid, multi-tenant application isolation, deduplication cleanup tool, and direct navigation links.*

![Dashboard Overview](./docs/images/phase3/08_dashboard_portfolio.png)

---

## 5. Technical Cross-Verification Against Specification

Every functional requirement and accepted enhancement from `LoanEligibilityAnalyzer.md` has been cross-checked and verified:

| Specification Section | Functional Requirement | Technical Implementation | Status |
| :--- | :--- | :--- | :---: |
| **§ 1.1** | Customer Information Screen (13 Intake Fields) | Full schema validation across Personal, Employment, Financial, Credit, and Loan Details |  **Verified** |
| **§ 1.2** | AI Prediction Module | Dual-mode prediction: Random Forest with SHAP feature explanations + Rule-based fallback |  **Verified** |
| **§ 1.3** | User Roles & Access Control | `ADMIN`, `SENIOR_CREDIT_MANAGER`, `LOAN_OFFICER` with JWT Bearer token authentication |  **Verified** |
| **§ 2.1** | Application Summary Report | Aggregated counts for Total, Approved, Rejected, and Pending applications |  **Verified** |
| **§ 2.2** | Risk Distribution Report | Grouped breakdown across Low, Medium, and High risk categories |  **Verified** |
| **§ 2.3** | Loan Amount Analysis | Aggregated calculations for Total Requested, Total Recommended, and Average Loan Size |  **Verified** |
| **§ 2.4** | Loan Type Report | Breakdown by Home, Personal, and Car loans |  **Verified** |
| **§ 2.5** | Loan Officer Performance Report | Operator audit tracking individual application counts, approvals, and rejections |  **Verified** |
| **Enhancement 1** | FOIR (Fixed Obligation to Income Ratio) | 50% Salaried / 60% Self-Employed caps with auto-high-risk override on cap breach |  **Verified** |
| **Enhancement 2** | SHAP Decision Explanations | `shap.TreeExplainer` feature contribution percentage generator |  **Verified** |
| **Enhancement 3** | Multi-Level Approval Hierarchy | 3-tier limits (≤₹5L Officer, ≤₹25L SCM, >₹25L Admin) with 403 API guards |  **Verified** |
| **Enhancement 4** | Customer Document Tracking | `customer_documents` table for PAN, Aadhaar, Form 16, and Bank Statements |  **Verified** |
| **Enhancement 5** | System Audit Logs | Full audit trail (`CREATED`, `AI_SCORED`, `APPROVED`, `REJECTED`, etc.) with IP tracking |  **Verified** |
| **Enhancement 6** | Security Implementation | bcrypt password hashing, JWT HS256 tokens, parameterized SQL queries, XSS sanitization |  **Verified** |
| **Enhancements 7-8** | Background Jobs & Mock CIBIL | Explicitly designated as *Future Phase* in specification document |  **Deferred** |

---

## 6. Live Multi-Tier Approval & Credentials Verification Proof

### 6.1 Verified Test Environment Credentials
| Account Username | Password | Assigned Role | Approval Threshold | Accessible Modules |
| :--- | :--- | :--- | :---: | :--- |
| `admin` | `admin123` | `ADMIN` | **Unlimited** (Up to ₹10 Crore) | Full System: Portfolio, User Admin, Audit Logs, ML Retraining |
| `scm_lead` / `scm1` | `scm123` | `SENIOR_CREDIT_MANAGER` | **Up to ₹25,00,000** | Portfolio, SCM Approvals, Document Verification, Admin Reports |
| `officer_retail` / `officer1` | `officer123` | `LOAN_OFFICER` | **Up to ₹5,00,000** | Intake, AI Predictions, Officer Approvals (≤₹5L), Customer History |

### 6.2 Empirical Live Test Execution Output
```text
================================================================================
LIVE MULTI-TIER APPROVAL & CREDENTIALS VERIFICATION SUITE
Author: Samarjeeth R | Modus Information Systems
================================================================================
[1] Admin Authentication Verified: Successfully logged in as 'admin' (Role: ADMIN)
    - Verified account 'officer_retail' (Role: LOAN_OFFICER)
    - Verified account 'scm_lead' (Role: SENIOR_CREDIT_MANAGER)
[2] Loan Officer Authentication Verified: 'officer_retail' (Role: LOAN_OFFICER)
[3] Senior Credit Manager Authentication Verified: 'scm_lead' (Role: SENIOR_CREDIT_MANAGER)

[4] Customer Profile Created: ID #50 (Rajesh Varma, Salary Rs. 1.8L, Score 810)

--------------------------------------------------------------------------------
3-TIER APPROVAL THRESHOLD VERIFICATION MATRIX
--------------------------------------------------------------------------------
CASE A [Loan #63 - Rs. 3,50,000 (<= 5L Limit)]: Officer Approval Attempt
       -> HTTP 200 APPROVED (Allowed: Within Officer Rs. 5L limit)

CASE B [Loan #64 - Rs. 12,00,000 (> 5L Limit)]: Officer Approval Attempt
       -> HTTP 403 FORBIDDEN (Blocked: Loan Officers can only approve loans up to Rs. 5,00,000. This application requires a Senior Credit Manager or Admin.)

CASE C [Loan #64 - Rs. 12,00,000 (<= 25L Limit)]: SCM Approval Attempt
       -> HTTP 200 APPROVED (Allowed: Within SCM Rs. 25L limit)

CASE D [Loan #65 - Rs. 35,00,000 (> 25L Limit)]: SCM Approval Attempt
       -> HTTP 403 FORBIDDEN (Blocked: Senior Credit Managers can only approve loans up to Rs. 25,00,000. This application requires Admin / Credit Committee approval.)

CASE E [Loan #65 - Rs. 35,00,000 (> 25L)]: Admin Approval Attempt
       -> HTTP 200 APPROVED (Allowed: Admin institutional authority)

--------------------------------------------------------------------------------
CUSTOMER DOCUMENT VERIFICATION AUDIT
--------------------------------------------------------------------------------
[5] Document Record #8: Type=PAN_CARD, Status=VERIFIED, VerifiedBy=User #55 (SCM)

--------------------------------------------------------------------------------
REGULATORY AUDIT TRAIL EVIDENCE (Application #65)
--------------------------------------------------------------------------------
  - Action: CREATED    | Prev: None    | New: PENDING  | UserID: 54 | IP: 127.0.0.1
  - Action: AI_SCORED  | Prev: None    | New: MEDIUM   | UserID: 54 | IP: 127.0.0.1
  - Action: APPROVED   | Prev: PENDING | New: APPROVED | UserID: 17 | IP: 127.0.0.1

================================================================================
ALL LIVE EMPIRICAL TESTS PASSED SUCCESSFULLY (100% VERIFIED)
================================================================================
```

---

## 7. Summary & Conclusion

Phase 3 delivers the enterprise governance, auditability, and regulatory compliance required for banking loan underwriting. The platform features robust role-based security, foreign-key cascade safety, explainable AI scoring, and verifiable end-to-end data integrity.
