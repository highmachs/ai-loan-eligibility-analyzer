import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import './CustomerForm.css';

// B11: max loan amount ₹10 crore
const MAX_LOAN_AMOUNT = 100_000_000;

const INITIAL_FORM = {
  full_name: '', age: '', gender: '', marital_status: '',
  occupation: '', company_name: '', employment_type: '', years_of_experience: '',
  monthly_salary: '', other_income: '', existing_emi: '', current_loans: '',
  credit_score: '', missed_payments: '', repayment_history: '',
  loan_type: '', requested_amount: '', tenure_months: '',
};

function Field({ label, name, type = 'text', min, max, required = true, value, onChange, error }) {
  return (
    <div className="field-group">
      <label htmlFor={name}>{label}{required && <span className="req">*</span>}</label>
      <input
        id={name}
        name={name}
        type={type}
        min={min}
        max={max}
        value={value}
        onChange={onChange}
        className={error ? 'input-error' : ''}
      />
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}

function Select({ label, name, options, required = true, value, onChange, error }) {
  return (
    <div className="field-group">
      <label htmlFor={name}>{label}{required && <span className="req">*</span>}</label>
      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        className={error ? 'input-error' : ''}
      >
        <option value="">-- Select --</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}

export default function CustomerForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState(INITIAL_FORM);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
    setApiError('');
  };

  // B5: safe numeric parser — handles raw digits, spaces, and commas without error
  const safeInt = (v) => {
    if (v === '' || v === null || v === undefined) return null;
    const clean = String(v).replace(/,/g, '').trim();
    const val = parseInt(clean, 10);
    return isNaN(val) ? null : val;
  };
  const safeFloat = (v) => {
    if (v === '' || v === null || v === undefined) return null;
    const clean = String(v).replace(/,/g, '').trim();
    const val = parseFloat(clean);
    return isNaN(val) ? null : val;
  };

  const validate = () => {
    const errs = {};
    if (!form.full_name.trim()) errs.full_name = 'Required';
    const age = safeInt(form.age);
    if (age === null || age < 18 || age > 75) errs.age = 'Age must be 18–75';
    if (!form.gender) errs.gender = 'Required';
    if (!form.marital_status) errs.marital_status = 'Required';
    if (!form.occupation.trim()) errs.occupation = 'Required';
    if (!form.employment_type) errs.employment_type = 'Required';
    if (safeInt(form.years_of_experience) === null) errs.years_of_experience = 'Required';
    const salary = safeFloat(form.monthly_salary);
    if (!salary || salary <= 0) errs.monthly_salary = 'Must be > 0';
    if (safeFloat(form.existing_emi) === null) errs.existing_emi = 'Required';
    if (safeInt(form.current_loans) === null) errs.current_loans = 'Required';
    const credit = safeInt(form.credit_score);
    if (credit === null || credit < 300 || credit > 900) errs.credit_score = 'Must be 300–900';
    if (safeInt(form.missed_payments) === null) errs.missed_payments = 'Required';
    if (!form.loan_type) errs.loan_type = 'Required';
    // B11: max amount validation
    const amount = safeFloat(form.requested_amount);
    if (!amount || amount <= 0) errs.requested_amount = 'Must be > 0';
    else if (amount > MAX_LOAN_AMOUNT) errs.requested_amount = 'Cannot exceed ₹10,00,00,000 (₹10 Crore)';
    const tenure = safeInt(form.tenure_months);
    if (!tenure || tenure < 6 || tenure > 360) errs.tenure_months = 'Must be 6–360 months';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }

    setLoading(true);
    try {
      // B5: All numeric fields use safeInt/safeFloat — no NaN sent to backend
      const customerPayload = {
        full_name: form.full_name.trim(),
        age: safeInt(form.age),
        gender: form.gender,
        marital_status: form.marital_status,
        occupation: form.occupation.trim(),
        company_name: form.company_name.trim() || null,
        employment_type: form.employment_type,
        years_of_experience: safeInt(form.years_of_experience),
        monthly_salary: safeFloat(form.monthly_salary),
        other_income: safeFloat(form.other_income) ?? 0,
        existing_emi: safeFloat(form.existing_emi) ?? 0,
        current_loans: safeInt(form.current_loans) ?? 0,
        credit_score: safeInt(form.credit_score),
        missed_payments: safeInt(form.missed_payments) ?? 0,
        repayment_history: form.repayment_history || null,  // B12: enum value or null
      };

      const customerRes = await client.post('/api/customers/', customerPayload);
      const customerId = customerRes.data.id;

      const loanPayload = {
        customer_id: customerId,
        loan_type: form.loan_type,
        requested_amount: safeFloat(form.requested_amount),
        tenure_months: safeInt(form.tenure_months),
      };

      const loanRes = await client.post('/api/loans/', loanPayload);
      navigate(`/prediction/${loanRes.data.id}`);
    } catch (err) {
      setApiError(err.response?.data?.detail || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const f = (name) => ({ name, value: form[name], onChange: handleChange, error: errors[name] });

  return (
    <div className="form-root">
      <nav className="form-nav">
        <Link to="/dashboard" className="back-link">← Dashboard</Link>
        <span className="form-nav-title">New Loan Application</span>
      </nav>

      <div className="form-container">
        <form id="customer-loan-form" onSubmit={handleSubmit} noValidate>

          <section className="form-section">
            <h2 className="section-title">Personal Information</h2>
            <div className="fields-grid">
              <Field label="Full Name" {...f('full_name')} />
              <Field label="Age" type="number" min={18} max={75} {...f('age')} />
              <Select label="Gender" options={[
                { value: 'MALE', label: 'Male' },
                { value: 'FEMALE', label: 'Female' },
                { value: 'OTHER', label: 'Other' },
              ]} {...f('gender')} />
              <Select label="Marital Status" options={[
                { value: 'SINGLE', label: 'Single' },
                { value: 'MARRIED', label: 'Married' },
                { value: 'DIVORCED', label: 'Divorced' },
              ]} {...f('marital_status')} />
            </div>
          </section>

          <section className="form-section">
            <h2 className="section-title">Employment Information</h2>
            <div className="fields-grid">
              <Field label="Occupation" {...f('occupation')} />
              <Field label="Company Name" required={false} {...f('company_name')} />
              <Select label="Employment Type" options={[
                { value: 'SALARIED', label: 'Salaried' },
                { value: 'SELF_EMPLOYED', label: 'Self-Employed' },
              ]} {...f('employment_type')} />
              <Field label="Years of Experience" type="number" min={0} {...f('years_of_experience')} />
            </div>
          </section>

          <section className="form-section">
            <h2 className="section-title">Financial Information</h2>
            <div className="fields-grid">
              <Field label="Monthly Salary (₹)" type="number" min={0} {...f('monthly_salary')} />
              <Field label="Other Income (₹)" type="number" min={0} required={false} {...f('other_income')} />
              <Field label="Existing Monthly EMI (₹)" type="number" min={0} {...f('existing_emi')} />
              <Field label="Number of Current Loans" type="number" min={0} {...f('current_loans')} />
            </div>
          </section>

          <section className="form-section">
            <h2 className="section-title">Credit Information</h2>
            <div className="fields-grid">
              <Field label="Credit Score (300–900)" type="number" min={300} max={900} {...f('credit_score')} />
              <Field label="Missed Payments (count)" type="number" min={0} {...f('missed_payments')} />
              {/* B12: repayment_history is now a dropdown enum (GOOD/FAIR/POOR/NONE) */}
              <Select label="Repayment History" required={false} options={[
                { value: 'GOOD', label: 'Good — consistent on-time payments' },
                { value: 'FAIR', label: 'Fair — occasional delays' },
                { value: 'POOR', label: 'Poor — frequent defaults/delays' },
                { value: 'NONE', label: 'None — no prior credit history' },
              ]} {...f('repayment_history')} />
            </div>
          </section>

          <section className="form-section">
            <h2 className="section-title">Loan Details</h2>
            <div className="fields-grid">
              <Select label="Loan Type" options={[
                { value: 'HOME', label: 'Home Loan' },
                { value: 'PERSONAL', label: 'Personal Loan' },
                { value: 'CAR', label: 'Car Loan' },
              ]} {...f('loan_type')} />
              {/* B11: max ₹10 crore */}
              <Field label="Requested Loan Amount (₹)" type="number" min={0} max={MAX_LOAN_AMOUNT} {...f('requested_amount')} />
              <Field label="Loan Tenure (months)" type="number" min={6} max={360} {...f('tenure_months')} />
            </div>
          </section>

          {apiError && <div className="api-error">{apiError}</div>}

          <div className="form-actions">
            <Link to="/dashboard" className="cancel-btn">Cancel</Link>
            <button
              id="submit-application-btn"
              type="submit"
              className="submit-btn"
              disabled={loading}
            >
              {loading ? 'Submitting...' : 'Submit & Get AI Prediction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
