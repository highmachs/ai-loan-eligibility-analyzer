import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import './CustomerHistory.css';

export default function CustomerHistory() {
  const { customerId } = useParams();
  const [customer, setCustomer] = useState(null);
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      client.get(`/api/customers/${customerId}`),
      client.get(`/api/customers/${customerId}/loans`),
    ])
      .then(([custRes, loansRes]) => {
        setCustomer(custRes.data);
        setLoans(loansRes.data);
      })
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load customer history.'))
      .finally(() => setLoading(false));
  }, [customerId]);

  const totalRequested = loans.reduce((sum, l) => sum + Number(l.requested_amount), 0);
  const approved = loans.filter((l) => l.status === 'APPROVED').length;
  const rejected = loans.filter((l) => l.status === 'REJECTED').length;
  const pending = loans.filter((l) => l.status === 'PENDING').length;

  return (
    <div className="ch-root">
      <nav className="result-nav">
        <Link to="/dashboard" className="back-link">← Dashboard</Link>
        <span className="result-nav-title">
          Customer History — {customer ? customer.full_name : `#${customerId}`}
        </span>
      </nav>

      <div className="ch-container">
        {loading && <p className="loading-text">Loading history…</p>}
        {error && <p className="result-error">{error}</p>}

        {customer && (
          <>
            {/* ── Customer Profile Card ── */}
            <section className="ch-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                <h2 style={{ margin: 0 }}>Customer Profile & Intake Record</h2>
                <Link to={`/documents/${customerId}`} id="view-docs-from-history" className="link-btn">
                  📄 View KYC Documents
                </Link>
              </div>

              <div className="ch-profile-grid">
                <div className="ch-profile-item">
                  <span className="ch-label">Full Name</span>
                  <span className="ch-value">{customer.full_name}</span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Age</span>
                  <span className="ch-value">{customer.age} years</span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Gender</span>
                  <span className="ch-value">{customer.gender}</span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Marital Status</span>
                  <span className="ch-value">{customer.marital_status}</span>
                </div>

                <div className="ch-profile-item">
                  <span className="ch-label">Employment Type</span>
                  <span className="ch-value">{customer.employment_type?.replace('_', ' ')}</span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Occupation</span>
                  <span className="ch-value">{customer.occupation}</span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Company Name</span>
                  <span className="ch-value">{customer.company_name || '—'}</span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Work Experience</span>
                  <span className="ch-value">{customer.years_of_experience} years</span>
                </div>

                <div className="ch-profile-item">
                  <span className="ch-label">Monthly Salary</span>
                  <span className="ch-value" style={{ color: '#22c55e', fontWeight: 600 }}>
                    ₹{Number(customer.monthly_salary).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Other Income</span>
                  <span className="ch-value">
                    ₹{Number(customer.other_income || 0).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Existing Monthly EMI</span>
                  <span className="ch-value" style={{ color: '#f87171' }}>
                    ₹{Number(customer.existing_emi).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Active Loans Count</span>
                  <span className="ch-value">{customer.current_loans}</span>
                </div>

                <div className="ch-profile-item">
                  <span className="ch-label">Credit Score (CIBIL)</span>
                  <span className="ch-value" style={{ fontWeight: 600 }}>
                    {customer.credit_score}
                  </span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Missed Payments</span>
                  <span className="ch-value" style={{ color: customer.missed_payments > 0 ? '#ef4444' : 'inherit' }}>
                    {customer.missed_payments}
                  </span>
                </div>
                <div className="ch-profile-item">
                  <span className="ch-label">Repayment Track Record</span>
                  <span className="ch-value">
                    {customer.repayment_history || 'Good'}
                  </span>
                </div>
              </div>
            </section>

            {/* ── Loan Summary Stats ── */}
            {loans.length > 0 && (
              <section className="ch-section">
                <h2>Loan Summary</h2>
                <div className="stats-grid">
                  <div className="stat-card stat-total">
                    <div className="stat-label">Total Applications</div>
                    <div className="stat-value">{loans.length}</div>
                  </div>
                  <div className="stat-card stat-approved">
                    <div className="stat-label">Approved</div>
                    <div className="stat-value">{approved}</div>
                  </div>
                  <div className="stat-card stat-rejected">
                    <div className="stat-label">Rejected</div>
                    <div className="stat-value">{rejected}</div>
                  </div>
                  <div className="stat-card stat-pending">
                    <div className="stat-label">Pending</div>
                    <div className="stat-value">{pending}</div>
                  </div>
                </div>
                <div className="ch-total-row">
                  Total Amount Requested:{' '}
                  <strong>₹{totalRequested.toLocaleString('en-IN')}</strong>
                </div>
              </section>
            )}

            {/* ── Loan Applications Table ── */}
            <section className="ch-section">
              <h2>Loan Applications</h2>
              {loans.length === 0 ? (
                <p className="empty-text">No loan applications found for this customer.</p>
              ) : (
                <table className="apps-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Tenure</th>
                      <th>Status</th>
                      <th>Date</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loans.map((loan) => (
                      <tr key={loan.id}>
                        <td>#{loan.id}</td>
                        <td>{loan.loan_type}</td>
                        <td>₹{Number(loan.requested_amount).toLocaleString('en-IN')}</td>
                        <td>{loan.tenure_months} mo</td>
                        <td>
                          <span className={`badge badge-${(loan.status || '').toLowerCase()}`}>
                            {loan.status}
                          </span>
                        </td>
                        <td>{new Date(loan.created_date).toLocaleDateString('en-IN')}</td>
                        <td>
                          <Link
                            to={`/prediction/${loan.id}`}
                            id={`history-view-btn-${loan.id}`}
                            className="link-btn"
                          >
                            View AI
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
