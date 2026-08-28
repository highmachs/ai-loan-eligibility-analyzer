import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [stats, setStats] = useState({ total: 0, approved: 0, rejected: 0, pending: 0 });
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState('');
  const [dupeMsg, setDupeMsg] = useState(null); // { type: 'success'|'error', text: string }
  const [dupeLoading, setDupeLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      client.get('/api/loans/stats'),
      client.get('/api/loans/'),
    ])
      .then(([statsRes, loansRes]) => {
        setStats(statsRes.data);
        setLoans(loansRes.data);
      })
      .catch((err) => {
        setFetchError(err.response?.data?.detail || 'Failed to load dashboard data.');
      })
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const refreshData = () =>
    Promise.all([client.get('/api/loans/stats'), client.get('/api/loans/')])
      .then(([statsRes, loansRes]) => {
        setStats(statsRes.data);
        setLoans(loansRes.data);
      });

  const handleDeleteDuplicates = async () => {
    if (!window.confirm('This will permanently delete all duplicate loan applications. Continue?')) return;
    setDupeLoading(true);
    setDupeMsg(null);
    try {
      const res = await client.delete('/api/loans/duplicates');
      const { message, deleted_count } = res.data;
      setDupeMsg({ type: 'success', text: deleted_count > 0 ? `✓ ${message}` : '✓ No duplicates found — table is clean.' });
      await refreshData();
    } catch (err) {
      setDupeMsg({ type: 'error', text: `✗ ${err.response?.data?.detail || 'Failed to delete duplicates.'}` });
    } finally {
      setDupeLoading(false);
    }
  };

  return (
    <div className="dashboard-root">
      <nav className="navbar">
        <div className="navbar-brand">Loan Eligibility Analyzer</div>
        <div className="navbar-right">
          <span className="navbar-user">{user.username} &mdash; {(user.role || '').replace(/_/g, ' ')}</span>
          {(user.role === 'ADMIN' || user.role === 'SENIOR_CREDIT_MANAGER') && (
            <Link to="/admin" id="admin-reports-btn" className="logout-btn" style={{ background: '#1a1a2e', border: '1px solid #444', marginRight: '0.5rem' }}>
              {user.role === 'ADMIN' ? 'Admin Reports' : 'Executive Reports'}
            </Link>
          )}
          <button id="logout-btn" className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <main className="dashboard-main">
        <div className="dashboard-header">
          <h1>Dashboard</h1>
          <Link to="/customers/new" id="new-application-btn" className="primary-btn">
            + New Application
          </Link>
        </div>

        {loading ? (
          <p className="loading-text">Loading applications...</p>
        ) : fetchError ? (
          <p className="result-error">{fetchError}</p>
        ) : (
          <>
            <div className="stats-grid">
              <div className="stat-card stat-total">
                <div className="stat-label">Total Applications</div>
                <div className="stat-value">{stats.total}</div>
              </div>
              <div className="stat-card stat-approved">
                <div className="stat-label">Approved</div>
                <div className="stat-value">{stats.approved}</div>
              </div>
              <div className="stat-card stat-rejected">
                <div className="stat-label">Rejected</div>
                <div className="stat-value">{stats.rejected}</div>
              </div>
              <div className="stat-card stat-pending">
                <div className="stat-label">Pending</div>
                <div className="stat-value">{stats.pending}</div>
              </div>
            </div>

            <div className="table-section">
              <div className="table-header-row">
                <h2>Recent Applications</h2>
                <button
                  id="delete-duplicates-btn"
                  className="danger-btn"
                  onClick={handleDeleteDuplicates}
                  disabled={dupeLoading}
                >
                  {dupeLoading ? 'Removing…' : '🗑 Delete Duplicates'}
                </button>
              </div>
              {dupeMsg && (
                <div className={`dupe-notification dupe-${dupeMsg.type}`}>
                  {dupeMsg.text}
                </div>
              )}
              {loans.length === 0 ? (
                <p className="empty-text">No applications yet. Start by creating a new one.</p>
              ) : (
                <table className="apps-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Applicant</th>
                      <th>Loan Type</th>
                      <th>Requested Amount</th>
                      <th>Tenure</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loans.map((loan) => (
                      <tr key={loan.id}>
                        <td>#{loan.id}</td>
                        <td style={{ fontWeight: 600, color: 'var(--text, #f8fafc)' }}>
                          {loan.customer?.full_name || '—'}
                        </td>
                        <td>{loan.loan_type}</td>
                        <td>₹{Number(loan.requested_amount).toLocaleString('en-IN')}</td>
                        <td>{loan.tenure_months} months</td>
                        <td>
                          <span className={`badge badge-${(loan.status || '').toLowerCase()}`}>
                            {loan.status}
                          </span>
                        </td>
                        <td>{new Date(loan.created_date).toLocaleDateString('en-IN')}</td>
                        <td style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <Link
                            to={`/prediction/${loan.id}`}
                            id={`view-btn-${loan.id}`}
                            className="link-btn"
                          >
                            AI Result
                          </Link>
                          {loan.customer_id && (
                            <Link
                              to={`/customers/${loan.customer_id}/history`}
                              id={`history-btn-${loan.id}`}
                              className="link-btn"
                              style={{ color: '#a78bfa' }}
                            >
                              History
                            </Link>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
