# Intelligent Loan Eligibility Analyzer
**AI-Powered Retail Credit Risk Evaluation & Decisioning Platform**

---

## 1. System Overview

The **Intelligent Loan Eligibility Analyzer** is an enterprise banking application designed to automate, standardize, and accelerate retail loan underwriting for Indian banking workflows. The system integrates machine learning credit scoring, Explainable AI (SHAP), a three-tier discretionary approval hierarchy, digital KYC verification, and regulatory compliance audit trails.

### Core Objectives
* **Automated Risk Assessment:** Evaluate applicant creditworthiness and categorize risk tiers (Low, Medium, High) using machine learning inference.
* **Explainable Underwriting:** Provide granular transparency into scoring decisions via SHAP (SHapley Additive exPlanations) marginal feature importance.
* **Regulatory Compliance & Debt Caps:** Enforce statutory Fixed Obligation to Income Ratio (FOIR) limits (50% for Salaried, 60% for Self-Employed) and estimate borrowing headroom.
* **Role-Based Discretionary Ceilings:** Enforce strict organizational approval tiers across Loan Officers, Senior Credit Managers, and Administrators.
* **Operational Auditing:** Maintain an immutable, chronological audit trail recording state transitions, actor identifiers, timestamps, and client IP addresses.

---

## 2. Technical Architecture & Stack

```
                              +---------------------------------------+
                              |         React 18 SPA Frontend         |
                              |               (Port 3900)             |
                              +-------------------+-------------------+
                                                  |
                                                  | REST API (Axios + JWT)
                                                  v
                              +---------------------------------------+
                              |            FastAPI Backend            |
                              |               (Port 8090)             |
                              +---------+-------------------+---------+
                                        |                   |
                     SQLAlchemy 2.0 ORM |                   | In-Memory Inference
                                        v                   v
                     +----------------------+   +-----------------------+
                     | PostgreSQL 15 Engine |   |  Random Forest Model  |
                     |      (Port 5499)     |   |   + SHAP Explainer    |
                     +----------------------+   +-----------------------+
```

### Component Details
* **Frontend:** React 18, React Router v6, Axios, Pure CSS design tokens.
* **Backend:** FastAPI, Python 3.10+, SQLAlchemy ORM, Pydantic V2, Uvicorn ASGI server.
* **Database:** PostgreSQL 15 (Docker container), Connection Pooling, Foreign Key cascade safeguards.
* **Machine Learning:** Scikit-Learn (Random Forest Classifier), SHAP TreeExplainer, Joblib serialization.
* **Security & Auth:** JSON Web Tokens (JWT), `bcrypt` password hashing, Role-Based Access Control (RBAC).

---

## 3. System Requirements & Setup Guide

### Prerequisites
* Windows 10/11, macOS, or Linux
* Docker Desktop (running)
* Python 3.10 or higher
* Node.js v18 or higher

---

### Quick Start (Windows Single-Click)

1. Ensure Docker Desktop is installed.
2. Execute `start.bat` from the project root.
   ```cmd
   start.bat
   ```
   The script automatically verifies the Docker daemon, spins up PostgreSQL, starts the FastAPI backend on port 8090, and launches the React frontend on port 3900.

3. Open your browser and navigate to:
   * **Web Application:** `http://localhost:3900`
   * **Interactive API Documentation (Swagger):** `http://localhost:8090/docs`
   * **Alternative API Documentation (ReDoc):** `http://localhost:8090/redoc`

---

### Manual Setup & Execution

#### 1. Database Service
```bash
docker compose up -d
```

#### 2. Backend Service
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8090
```

#### 3. Frontend Service
```bash
cd frontend
npm install
npm run dev
```

#### 4. Database Reset & Test Seed Utility
To reset all operational tables to a clean state with standard test accounts:
```bash
cd backend
python reset_and_seed_db.py
```

#### 5. Provisioning Custom User Accounts (`create_account.bat`)
To create new staff accounts manually and append them directly to the database:
* **Interactive Mode:** Double-click `create_account.bat` or run from terminal:
  ```cmd
  create_account.bat
  ```
  The prompt will ask for the Username, Password, and Role selection (1. Loan Officer, 2. Senior Credit Manager, 3. Admin).
* **CLI Parameterized Mode:**
  ```cmd
  create_account.bat -u custom_officer -p pass123 -r LOAN_OFFICER
  ```

---

## 4. User Roles & Access Control

The application implements a 3-tier Role-Based Access Control (RBAC) governance model:

| Role | Username | Password | Discretionary Approval Limit | Functional Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Loan Officer** | `officer_retail` | `officer123` | Up to **INR 5,00,000** | Customer intake, risk scoring, direct approval for small-ticket retail loans. |
| **Senior Credit Manager** | `scm_lead` | `scm123` | Up to **INR 25,00,000** | Mid-tier loan approvals, KYC document verification, customer lifetime history review, portfolio reports. |
| **Administrator** | `admin` | `admin123` | **Above INR 25,00,000** (Unlimited) | Institutional committee approvals, staff user management, dynamic model retraining, audit logs. |

New accounts can be appended at any time using `create_account.bat` or via the Administrator portal (`/admin/users`).

---

## 5. End-to-End User Guide

### 5.1. Authentication
1. Navigate to `http://localhost:3900/login`.
2. Enter your credentials. Click the eye icon to toggle password visibility if needed.
3. Click **Sign In**. The system validates your credentials and issues a secure JWT token.

---

### 5.2. Dashboard Navigation
* **Key Performance Indicators (KPIs):** View active counts for Total, Approved, Rejected, and Pending applications.
* **Recent Applications Table:** View recent submissions with Application ID, Applicant Name, Loan Type, Requested Amount, Tenure, Status, and Created Date.
* **Actions:**
  * **AI Result:** Open the detailed risk evaluation and decision card.
  * **History:** Open the customer's aggregated lifetime borrowing history.
  * **Delete Duplicates:** Automatically detect and remove redundant duplicate submissions while retaining canonical records.
* **Escape Key Navigation:** Pressing `Esc` on any form or sub-page returns you directly to the Dashboard.

---

### 5.3. Submitting a New Loan Application
1. Click **+ New Application** from the Dashboard navbar or header.
2. Complete the 18 required intake fields across 5 sections:
   * **Section 1: Personal Information:** Full Name, Age (18-75), Gender, Marital Status.
   * **Section 2: Employment Information:** Occupation, Company Name, Employment Type (Salaried / Self-Employed), Years of Experience.
   * **Section 3: Financial Information:** Monthly Salary (INR), Other Income (INR), Existing Monthly EMI (INR), Number of Current Active Loans.
   * **Section 4: Credit Information:** Credit Score (300-900), Missed Payments Count, Repayment Track Record.
   * **Section 5: Loan Details:** Loan Type (Home / Personal / Car), Requested Loan Amount (INR), Tenure in Months (6-360).
3. Click **Submit & Get AI Prediction**.
4. The system validates all inputs, records the customer profile, registers the loan, executes the machine learning model, and redirects to the Prediction Result view.

---

### 5.4. Reviewing AI Risk Predictions & Decisioning
The Prediction Result view displays:
* **Approval Probability & Risk Badge:** Low Risk (Green), Medium Risk (Amber), or High Risk (Red).
* **Financial Metrics:** Requested Amount, Recommended Headroom (safe borrowing ceiling), and Calculated FOIR (Fixed Obligation to Income Ratio).
* **SHAP Explainability Breakdown:** Individual feature contributions showing precisely which financial attributes increased or decreased approval probability.
* **Application Summary:** Core loan terms and linked applicant metadata.
* **Approval Action Panel:**
  * If the loan amount is within the user's discretionary threshold, the **Approve Application** button is active.
  * If the loan amount exceeds the threshold, a policy warning card is displayed, indicating the required authorization level (e.g., Senior Credit Manager or Admin).
  * Authorized users can click **Approve Application** or **Reject Application** to record an immutable status update.

---

### 5.5. KYC Document Verification
1. From an application result or customer history, click **View / Manage Documents**.
2. Senior Credit Managers and Administrators can inspect uploaded KYC documents (PAN Card, Aadhaar, Bank Statements).
3. Click **Verify** or **Reject** on each document. The system stamps the verifier's user identity and timestamp immutably in the database.

---

### 5.6. Customer Lifetime Credit Ledger
1. Click **History** from any loan row on the Dashboard.
2. The view displays:
   * **Customer Profile:** Complete 15-field profile record including income, active debts, employment, and credit score.
   * **Loan Summary:** Cumulative borrowing amount, approved loans count, and pending exposure.
   * **Loan Applications Table:** Full historical ledger of all loans requested by this customer across their relationship with the institution.

---

### 5.7. Executive Reports & ML Model Retraining (Admin / SCM)
1. Click **Admin Reports** (or **Executive Reports**) in the top navigation bar.
2. Review portfolio distributions:
   * Loan Application Summary (Total, Approved, Rejected, Pending).
   * Portfolio Risk Distribution (Low, Medium, High counts).
   * Product Breakdown by Loan Type (Home, Personal, Car).
   * Loan Amount Analysis (Total Requested Volume vs. Recommended Volume).
   * Officer Underwriting Performance metrics.
   * 12-Month Rolling Approvals Trend Chart.
3. **Dynamic ML Retraining (Admin Only):** Click **Retrain ML Model** to re-fit the Random Forest estimator on updated credit cohorts. The updated model is hot-swapped in memory with zero backend downtime.

---

### 5.8. User Administration & Audit Logs (Admin Only)
* **User Management (`/admin/users`):** Create new staff accounts, cycle RBAC roles (Loan Officer -> Senior Credit Manager -> Admin), and safely delete accounts with foreign key cascade safeguards (`ON DELETE SET NULL`).
* **Audit Logs (`/admin/audit-logs`):** Access the chronological regulatory compliance trail. Inspect events (`CREATED`, `AI_SCORED`, `APPROVED`, `DOCUMENT_VERIFIED`, `REJECTED`) with timestamps, actor IDs, state deltas, and client IP addresses.

---

## 6. Demonstration Profiles & Test Scenarios

The following three applicant profiles demonstrate the core operational flows:

| Attribute | Profile 1: Rajesh Sharma | Profile 2: Priya Sundaram | Profile 3: Vikram Malhotra |
| :--- | :--- | :--- | :--- |
| **Operational Goal** | Low-Risk Direct Approval | Multi-Level SCM Escalation | High-Risk FOIR Breach & Rejection |
| **Target Role** | Loan Officer (`officer_retail`) | SCM (`scm_lead`) | Admin (`admin`) |
| **Full Name** | `Rajesh Sharma` | `Priya Sundaram` | `Vikram Malhotra` |
| **Age / Gender** | `32` / `Male` | `38` / `Female` | `45` / `Male` |
| **Marital Status** | `Married` | `Married` | `Single` |
| **Occupation / Co.** | `Software Engineer` / `TCS` | `Retail Store Owner` / `Sundaram Enterprises` | `Consultant` / `Self` |
| **Employment Type** | `Salaried` (7 years experience) | `Self-Employed` (10 years experience) | `Salaried` (3 years experience) |
| **Monthly Salary** | `120000` (Other: `0`) | `180000` (Other: `20000`) | `100000` (Other: `0`) |
| **Existing EMI** | `15000` (1 active loan) | `30000` (1 active loan) | `65000` (3 active loans) |
| **Credit Score** | `790` (0 missed payments, Good) | `730` (0 missed payments, Good) | `620` (2 missed payments, Poor) |
| **Loan Details** | Home Loan: INR `350000` (36 months) | Personal Loan: INR `1200000` (60 months) | Personal Loan: INR `3500000` (84 months) |
| **AI Evaluation** | **Low Risk (99.86%)** | **Low Risk (92.40%)** | **High Risk (1.00%)** |
| **FOIR Metric** | 20.60% (Within safe threshold) | 25.00% (Within safe threshold) | 106.67% (Severe 50% Cap Breach) |
| **Outcome** | Approved directly by Loan Officer | Blocked for Officer; Approved by SCM | Blocked for SCM; Rejected by Admin |

---

## 7. REST API Reference

| HTTP Method | Endpoint | Description | Authorization |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate staff credentials and issue JWT bearer token | Public |
| `POST` | `/api/customers/` | Create or update customer record | Any Staff |
| `GET` | `/api/customers/{id}` | Retrieve customer profile details | Any Staff |
| `GET` | `/api/customers/{id}/loans` | List all historical applications for a customer | SCM / Admin |
| `POST` | `/api/loans/` | Create loan application and trigger immediate AI risk scoring | Any Staff |
| `GET` | `/api/loans/{id}` | Retrieve loan application details and linked customer profile | Authorized Staff |
| `PATCH` | `/api/loans/{id}/status` | Update status (Approved / Rejected) with discretionary ceiling check | Role-Restricted |
| `DELETE`| `/api/loans/duplicates` | Identify and remove duplicate loan application records | Any Staff |
| `GET` | `/api/predictions/{id}` | Fetch AI prediction, probability, FOIR, and SHAP reason string | Authorized Staff |
| `POST` | `/api/predictions/analyze`| Manually re-score a loan application | Authorized Staff |
| `POST` | `/api/documents/` | Register uploaded KYC document metadata | Any Staff |
| `PATCH` | `/api/documents/{id}/verify`| Mark document as Verified or Rejected | SCM / Admin |
| `GET` | `/api/admin/reports` | Retrieve executive KPIs and portfolio risk distribution | SCM / Admin |
| `GET` | `/api/admin/monthly-stats` | Retrieve 12-month rolling application trends | SCM / Admin |
| `POST` | `/api/admin/retrain` | Trigger on-demand retraining of the machine learning model | Admin Only |
| `GET` | `/api/admin/users` | List all registered staff accounts | Admin Only |
| `POST` | `/api/admin/users` | Provision a new staff user account | Admin Only |
| `PATCH` | `/api/admin/users/{id}/role`| Update user role permissions | Admin Only |
| `DELETE`| `/api/admin/users/{id}` | Remove user account with safe foreign key nullification | Admin Only |
| `GET` | `/api/audit-logs/` | Query chronological regulatory audit trail | Admin Only |

---

## 8. Repository Layout

```
.
|-- backend/
|   |-- app/
|   |   |-- models/            # SQLAlchemy database entities
|   |   |-- routers/           # Modular FastAPI routing endpoints
|   |   |-- schemas/           # Pydantic validation contracts
|   |   |-- services/          # Business logic, auth, and SHAP inference
|   |   |-- config.py          # Centralized configuration & settings
|   |   |-- database.py        # Database engine & session management
|   |   `-- main.py            # FastAPI application entrypoint
|   |-- create_user.py         # Standalone user account creation utility
|   |-- reset_and_seed_db.py   # Database truncate and fresh seed script
|   `-- requirements.txt       # Python backend dependencies
|-- frontend/
|   |-- src/
|   |   |-- api/               # Axios instance and JWT interceptors
|   |   |-- pages/             # React application views and CSS modules
|   |   |-- App.jsx            # Routing and global Escape key listener
|   |   `-- main.jsx           # Application entrypoint
|   |-- package.json           # Frontend dependencies and scripts
|   `-- vite.config.js         # Vite bundler configuration
|-- ml/
|   |-- train_model.py         # Synthetic cohort training & model pipeline
|   |-- model.pkl              # Serialized Random Forest classifier
|   `-- feature_cols.pkl       # Feature column serialization
|-- reports/                   # Technical demonstration reports (MD & DOCX)
|-- docker-compose.yml         # Containerized PostgreSQL & pgAdmin services
|-- start.bat                  # Automated Windows startup script
|-- create_account.bat         # Standalone custom account creation script
|-- QUICK_DEMO_GUIDE.md        # Mobile companion walkthrough cheat sheet
`-- README.md                  # Master documentation and user guide
```

---

## 9. Troubleshooting & FAQ

#### 1. Port Conflict on 8090 or 3900
* Ensure no existing processes are occupying ports 8090 (Backend) or 3900 (Frontend).
* Run `taskkill /F /IM python.exe` or `npx kill-port 3900` if necessary.

#### 2. Database Connection Error
* Verify that the Docker container `loan_analyzer_db` is running via `docker ps`.
* If stopped, restart via `docker compose up -d`.

#### 3. Resetting Test Data
* To clear all demonstration loans and return to the baseline seeded state, execute:
  ```cmd
  cd backend
  python reset_and_seed_db.py
  ```

---

## 10. License & Institutional Attribution

Developed for **Modus Information Systems** by **Samarjeeth R**.  
This software is designed for retail banking credit risk analysis and decision automation.
