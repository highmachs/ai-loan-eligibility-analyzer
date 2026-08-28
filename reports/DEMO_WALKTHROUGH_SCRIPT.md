# Master Video Walkthrough Cheat Sheet & Live Demo Script
**Project:** Intelligent Loan Eligibility Analyzer  
**Author:** Samarjeeth R | Modus Information Systems  
**Purpose:** Comprehensive, exact-field walkthrough guide to follow on mobile/split-screen while recording on PC.

---

## Pre-Flight Checklist

1. **Verify Services Running:**
   * **Frontend Portal:** `http://localhost:3900`
   * **Backend REST API:** `http://localhost:8090` (Docs: `http://localhost:8090/docs`)
   * **Database:** PostgreSQL 15 container `loan_analyzer_db` is running on port `5499` and freshly seeded.
2. **Demo User Accounts:**
   *  **Loan Officer:** `officer_retail` / `officer123` (Intake & approvals $\le ₹5,00,000$)
   *  **Senior Credit Manager:** `scm_lead` / `scm123` (Document verification & approvals $\le ₹25,00,000$)
   *  **Admin:** `admin` / `admin123` (Full system, approvals $> ₹25,00,000$, user management, audit logs, ML retraining)

---

# STEP-BY-STEP RECORDING FLOW

---

## SCENE 1: Loan Officer Intake & ₹3.5L Low-Risk Approval
* **Login Account:** `officer_retail` / `officer123`
* **Action:** Click **"+ New Application"** in navbar.
* **Fill ALL 18 Form Fields Exactly as Shown Below:**

### Section 1: Personal Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Full Name** | `Rajesh Sharma` |
| **Age** | `32` |
| **Gender** | Select `Male` |
| **Marital Status** | Select `Married` |

### Section 2: Employment Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Occupation** | `Software Engineer` |
| **Company Name** | `TCS` |
| **Employment Type** | Select `Salaried` |
| **Years of Experience** | `7` |

### Section 3: Financial Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Monthly Salary (₹)** | `120000` |
| **Other Income (₹)** | `0` |
| **Existing Monthly EMI (₹)** | `15000` |
| **Number of Current Loans** | `1` |

### Section 4: Credit Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Credit Score (300–900)** | `790` |
| **Missed Payments (count)** | `0` |
| **Repayment History** | Select `Good — consistent on-time payments` |

### Section 5: Loan Details
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Loan Type** | Select `Home Loan` |
| **Requested Loan Amount (₹)** | `350000` |
| **Loan Tenure (months)** | `36` |

* **Click:** `"Submit & Get AI Prediction"`
* **What to Show on Screen:**
  *  **Approval Probability:** `~99%` with `LOW RISK` badge (Green).
  *  **Recommended Amount:** Calculated headroom (~₹16.20 Lakhs).
  *  **FOIR:** Low debt-to-income (`20.60%`).
  *  **Evaluation Reasons:** SHAP explainability breakdown (Credit score, Debt-to-income, Payment history).
  *  **Direct Signing Authority:** Loan Officer has direct approval power because ₹3.5L is $\le ₹5,00,000$.
* **Click:** **"Approve Application"** $\rightarrow$ Status changes to `APPROVED`.
* **Click:** **"← Dashboard"** to show updated counters (Total: 1, Approved: 1).

---

## SCENE 2: ₹12 Lakh Loan & 3-Tier Multi-Level SCM Escalation
* **Still logged in as Loan Officer (`officer_retail`):** Click **"+ New Application"**.
* **Fill ALL 18 Form Fields for Applicant 2:**

### Section 1: Personal Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Full Name** | `Priya Sundaram` |
| **Age** | `38` |
| **Gender** | Select `Female` |
| **Marital Status** | Select `Married` |

### Section 2: Employment Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Occupation** | `Retail Store Owner` |
| **Company Name** | `Sundaram Enterprises` |
| **Employment Type** | Select `Self-Employed` |
| **Years of Experience** | `10` |

### Section 3: Financial Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Monthly Salary (₹)** | `180000` |
| **Other Income (₹)** | `20000` |
| **Existing Monthly EMI (₹)** | `30000` |
| **Number of Current Loans** | `1` |

### Section 4: Credit Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Credit Score (300–900)** | `730` |
| **Missed Payments (count)** | `0` |
| **Repayment History** | Select `Good — consistent on-time payments` |

### Section 5: Loan Details
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Loan Type** | Select `Personal Loan` |
| **Requested Loan Amount (₹)** | `1200000` |
| **Loan Tenure (months)** | `60` |

* **Click:** `"Submit & Get AI Prediction"`
* **What to Show on Screen:**
  *  **3-Tier Approval Gate:** Point out the Discretionary Notice Card:
    *" This loan exceeds ₹5,00,000. Requires Senior Credit Manager or Admin approval."*
  * The Approve button is disabled/restricted for the Loan Officer.
* **Escalation Step:**
  * Click **"Logout"** in top navbar.
  * Log in as Senior Credit Manager: **Username:** `scm_lead` | **Password:** `scm123`.
  * Click on Priya Sundaram's loan from the Dashboard list.
  * Show that SCM is authorized ($\le ₹25,00,000$).
  * Click **"Approve Application"** $\rightarrow$ Status changes to `APPROVED`.

---

## SCENE 3: Customer Document Verification & Lifetime History
* **Still logged in as SCM (`scm_lead`):**
  * Click **" VIEW / MANAGE DOCUMENTS"** on Priya Sundaram's application (or visit `http://localhost:3900/documents/2`).
  * **Verify KYC Documents:**
    * Click **"Verify"** on `PAN_CARD` $\rightarrow$ Status badge turns green `VERIFIED`.
    * Click **"Verify"** on `BANK_STATEMENT` $\rightarrow$ Status badge turns green `VERIFIED`.
    * Point out verifier attribution: *Verified by: scm_lead*.
  * **View Customer Lifetime History:**
    * Click **"Customer History"** (or visit `http://localhost:3900/customers/2/history`).
    * Point out aggregated borrowing metrics: Total Borrowed: ₹12,00,000, 1 Active Loan, clean payment history.

---

## SCENE 4: High-Risk FOIR Breach & ₹35L Admin Committee Escalation
* **As SCM (`scm_lead`):** Click **"+ New Application"**.
* **Fill ALL 18 Form Fields for Applicant 3:**

### Section 1: Personal Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Full Name** | `Vikram Malhotra` |
| **Age** | `45` |
| **Gender** | Select `Male` |
| **Marital Status** | Select `Single` |

### Section 2: Employment Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Occupation** | `Consultant` |
| **Company Name** | `Self` |
| **Employment Type** | Select `Salaried` |
| **Years of Experience** | `3` |

### Section 3: Financial Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Monthly Salary (₹)** | `100000` |
| **Other Income (₹)** | `0` |
| **Existing Monthly EMI (₹)** | `65000` *(65% FOIR — Exceeds 50% Cap!)* |
| **Number of Current Loans** | `3` |

### Section 4: Credit Information
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Credit Score (300–900)** | `620` *(Subprime)* |
| **Missed Payments (count)** | `2` |
| **Repayment History** | Select `Poor — frequent defaults/delays` |

### Section 5: Loan Details
| Field on Screen | Exact Value to Enter / Select |
| :--- | :--- |
| **Loan Type** | Select `Personal Loan` |
| **Requested Loan Amount (₹)** | `3500000` |
| **Loan Tenure (months)** | `84` |

* **Click:** `"Submit & Get AI Prediction"`
* **What to Show on Screen:**
  *  **Risk Badge:** `HIGH RISK` (Red) with low approval probability.
  *  **Headroom:** Dropped to `₹0` due to financial over-leverage.
  *  **FOIR:** High debt ratio (`106.67%`).
  *  **3-Tier Gate:** SCM cannot approve ₹35 Lakhs (exceeds ₹25L limit).
* **Escalation Step:**
  * Click **"Logout"** and log in as Admin: **Username:** `admin` | **Password:** `admin123`.
  * Open Vikram Malhotra's loan from the Dashboard.
  * Click **"Reject Application"** (or show Admin overriding institutional authority).

---

## SCENE 5: Executive Admin Analytics & Runtime ML Retraining
* **As Admin (`admin`):**
  * Click **"Admin Reports"** in the top navbar (`http://localhost:3900/admin`).
  * Show Executive KPIs: Approval rate %, Total Disbursed Volume, Average Risk Score.
  * Show the **12-Month Approvals Trend Chart** (Pure CSS monthly stacked data bars).
  * Click **"Retrain AI Risk Model"** button at top right:
    * Modal/Toast confirms: *Model re-fitted on 3,000 synthetic banking records with 100% accuracy and hot-swapped in memory with zero backend downtime.*

---

## SCENE 6: User Management, RBAC & Regulatory Audit Logs
* **As Admin (`admin`):**
  * Click **"User Management"** (`http://localhost:3900/admin/users`):
    * View existing accounts (`admin`, `scm_lead`, `officer_retail`).
    * Create a new staff user:
      * **Username:** `officer_demo`
      * **Password:** `demo123`
      * **Role:** `LOAN_OFFICER`
    * Click **"Change Role"** to cycle: `LOAN_OFFICER` $\rightarrow$ `SENIOR_CREDIT_MANAGER` $\rightarrow$ `ADMIN`.
    * Click **"Delete"** to show safe cascading removal with `ON DELETE SET NULL`.
  * Click **"Audit Logs"** in top navbar (`http://localhost:3900/admin/audit-logs`):
    * Showcase complete chronological regulatory trail:
    * `CREATED` $\rightarrow$ `AI_SCORED` $\rightarrow$ `APPROVED` $\rightarrow$ `DOCUMENT_VERIFIED` $\rightarrow$ `REJECTED`.
    * Point out recorded User IDs, timestamps, status deltas, and client IP addresses (`127.0.0.1`).

---
*(End of Walkthrough Guide — All 18 fields and all 6 modules are 100% covered and verified!)*
