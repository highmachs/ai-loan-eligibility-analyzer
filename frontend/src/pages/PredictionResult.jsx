import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import './PredictionResult.css';

const OFFICER_LIMIT = 500_000;   // ₹5 Lakhs
const SCM_LIMIT    = 2_500_000; // ₹25 Lakhs

export default function PredictionResult() {
  const { loanId } = useParams();
  const navigate = useNavigate();
  const user   = JSON.parse(localStorage.getItem('user') || '{}');
  const role   = user.role;
  const isAdmin  = role === 'ADMIN';
  const isSCM    = role === 'SENIOR_CREDIT_MANAGER';
  const isOfficer = role === 'LOAN_OFFICER';

  const [result, setResult] = useState(null);
  const [loan, setLoan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState('');

  useEffect(() => {
    let isMounted = true;
    const run = async () => {
      setError('');
      setLoading(true);
      try {
        const loanRes = await client.get(`/api/loans/${loanId}`);
        if (!isMounted) return;
        setLoan(loanRes.data);

        try {
          const existing = await client.get(`/api/predictions/${loanId}`);
          if (!isMounted) return;
          setResult(existing.data);
        } catch (predErr) {
          if (predErr.response?.status === 404) {
            const fresh = await client.post('/api/predictions/analyze', {
              application_id: parseInt(loanId),
            });
            if (!isMounted) return;
            setResult(fresh.data);
          } else {
            throw predErr;
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail || 'Failed to load prediction. Please try again.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    run();
    return () => { isMounted = false; };
  }, [loanId]);

  const handleStatusUpdate = async (newStatus) => {
    setSubmitting(true);
    setActionError('');
    try {
      await client.patch(`/api/loans/${loanId}/status`, { status: newStatus });
      navigate('/dashboard');
    } catch (err) {
      setActionError(err.response?.data?.detail || `Failed to ${newStatus.toLowerCase()} application.`);
      setSubmitting(false);
    }
  };

  const riskClass = result?.risk_level?.toLowerCase();
  const requestedAmount = loan ? Number(loan.requested_amount) : 0;

  // 3-tier approval gate (mirrors backend B6 logic)
  const canApprove =
    isAdmin ||
    (isSCM    && requestedAmount <= SCM_LIMIT) ||
    (isOfficer && requestedAmount <= OFFICER_LIMIT);

  const approvalNotice = (() => {
    if (canApprove || !loan || loan.status !== 'PENDING') return null;
    if (isOfficer && requestedAmount > SCM_LIMIT)
      return '⚠️ This loan exceeds ₹25,00,000. Only Admin / Credit Committee can approve.';
    if (isOfficer)
      return '⚠️ This loan exceeds ₹5,00,000. Requires Senior Credit Manager or Admin approval.';
    if (isSCM)
      return '⚠️ This loan exceeds ₹25,00,000. Only Admin / Credit Committee can approve.';
    return null;
  })();

  return (
    <div className="result-root">
      <nav className="result-nav">
        <Link to="/dashboard" className="back-link">← Dashboard</Link>
        <span className="result-nav-title">AI Prediction Result — Application #{loanId}</span>
      </nav>

      <div className="result-container">
        {loading && <p className="loading-text">Running AI evaluation...</p>}
        {error && !result && <div className="result-error">{error}</div>}

        {result && loan && (
          <>
            <div className={`score-card risk-${riskClass}`}>
              <div className="score-left">
                <div className="score-label">Approval Probability</div>
                <div className="score-value">{result.approval_probability}%</div>
                <div className={`risk-badge risk-badge-${riskClass}`}>
                  {result.risk_level} RISK
                </div>
              </div>
              <div className="score-right">
                <div className="amount-row">
                  <span className="amount-label">Requested Amount</span>
                  <span className="amount-value">
                    ₹{requestedAmount.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="amount-row highlight">
                  <span className="amount-label">Recommended Amount</span>
                  <span className="amount-value green">
                    ₹{Number(result.recommended_amount).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="amount-row">
                  <span className="amount-label">FOIR</span>
                  <span className="amount-value">{result.foir}%</span>
                </div>
              </div>
            </div>

            <div className="reasons-card">
              <h3>Evaluation Reasons</h3>
              <ul className="reasons-list">
                {result.reason.split('; ').flatMap((r) => r.split(', ')).filter(Boolean).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>

            <div className="summary-card">
              <h3>Application Summary</h3>
              <div className="summary-grid">
                <div className="summary-item">
                  <span className="s-label">Loan Type</span>
                  <span className="s-value">{loan.loan_type}</span>
                </div>
                <div className="summary-item">
                  <span className="s-label">Tenure</span>
                  <span className="s-value">{loan.tenure_months} months</span>
                </div>
                <div className="summary-item">
                  <span className="s-label">Status</span>
                  <span className={`badge badge-${(loan.status || '').toLowerCase()}`}>{loan.status}</span>
                </div>
                <div className="summary-item">
                  <span className="s-label">Customer</span>
                  <span className="s-value">{loan.customer?.full_name || '—'}</span>
                </div>
              </div>

              {/* Document Manager link */}
              {loan.customer_id && (
                <div style={{ marginTop: '1rem' }}>
                  <Link
                    to={`/documents/${loan.customer_id}`}
                    id="view-docs-btn"
                    className="link-btn"
                  >
                    📄 View / Manage Documents
                  </Link>
                </div>
              )}
            </div>

            {actionError && <div className="result-error">{actionError}</div>}

            {/* Multi-level approval notice — 3-tier hierarchy */}
            {approvalNotice && (
              <div className="approval-notice">{approvalNotice}</div>
            )}

            {loan.status === 'PENDING' && (
              <div className="action-row">
                <button
                  id="reject-btn"
                  className="action-btn reject-btn"
                  onClick={() => handleStatusUpdate('REJECTED')}
                  disabled={submitting}
                >
                  Reject Application
                </button>
                <button
                  id="approve-btn"
                  className="action-btn approve-btn"
                  onClick={() => handleStatusUpdate('APPROVED')}
                  disabled={submitting || !canApprove}
                  title={!canApprove ? approvalNotice : ''}
                >
                  Approve Application
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
