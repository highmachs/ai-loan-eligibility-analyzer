import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import './AdminReports.css';

const MONTH_COLORS = { approved: '#22c55e', rejected: '#ef4444', pending: '#f59e0b' };

function MonthlyChart({ data }) {
  if (!data || data.length === 0) return <p className="empty-text">No monthly data available.</p>;
  const max = Math.max(...data.map((d) => d.total), 1);
  return (
    <div className="monthly-chart">
      {data.map((item) => (
        <div key={`${item.year}-${item.month}`} className="monthly-col">
          <div className="monthly-bars">
            {[['approved', item.approved], ['rejected', item.rejected], ['pending', item.pending]].map(
              ([key, val]) => (
                <div
                  key={key}
                  className="monthly-bar-seg"
                  title={`${key}: ${val}`}
                  style={{
                    height: `${(val / max) * 120}px`,
                    background: MONTH_COLORS[key],
                  }}
                />
              )
            )}
          </div>
          <div className="monthly-label">{item.month_label}</div>
          <div className="monthly-total">{item.total}</div>
        </div>
      ))}
    </div>
  );
}

// Simple bar chart rendered with pure CSS/divs — no library dependency
function BarChart({ data, valueKey, labelKey, colorMap }) {
  if (!data || data.length === 0) return <p className="empty-text">No data available.</p>;
  const max = Math.max(...data.map((d) => d[valueKey]), 1);
  return (
    <div className="bar-chart">
      {data.map((item) => (
        <div key={item[labelKey]} className="bar-row">
          <span className="bar-label">{item[labelKey]}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{
                width: `${(item[valueKey] / max) * 100}%`,
                background: colorMap?.[item[labelKey]] || 'var(--accent)',
              }}
            />
          </div>
          <span className="bar-value">{item[valueKey]}</span>
        </div>
      ))}
    </div>
  );
}

export default function AdminReports() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [reports, setReports] = useState(null);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retraining, setRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState('');

  useEffect(() => {
    Promise.all([
      client.get('/api/admin/reports'),
      client.get('/api/admin/monthly-stats'),
    ])
      .then(([rptRes, mthRes]) => {
        setReports(rptRes.data);
        setMonthlyStats(mthRes.data);
      })
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load reports.'))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainMsg('');
    try {
      const res = await client.post('/api/admin/retrain');
      setRetrainMsg(`Model retrained successfully. Output: ${res.data.output.split('\n').pop()}`);
    } catch (err) {
      setRetrainMsg(err.response?.data?.detail || 'Retraining failed.');
    } finally {
      setRetraining(false);
    }
  };

  const riskColors = { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#ef4444' };
  const typeColors = { HOME: '#6366f1', PERSONAL: '#da291c', CAR: '#0ea5e9' };

  return (
    <div className="admin-root">
      <nav className="navbar">
        <div className="navbar-brand">Loan Eligibility Analyzer</div>
        <div className="navbar-right">
          <Link to="/dashboard" className="nav-link">← Dashboard</Link>
          <span className="navbar-user">{user.username} &mdash; {(user.role || '').replace(/_/g, ' ')}</span>
          <button id="logout-btn" className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <main className="admin-main">
        <div className="admin-header">
          <h1>{user.role === 'ADMIN' ? 'Admin Reports' : 'Executive Reports'}</h1>
          {user.role === 'ADMIN' && (
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <Link
                to="/admin/users"
                id="manage-users-btn"
                className="logout-btn"
                style={{ background: '#1a1a2e', border: '1px solid #444' }}
              >
                👥 Manage Users
              </Link>
              <Link
                to="/admin/audit-logs"
                id="audit-logs-btn"
                className="logout-btn"
                style={{ background: '#1a1a2e', border: '1px solid #444' }}
              >
                🔍 Audit Logs
              </Link>
              <button
                id="retrain-btn"
                className="retrain-btn"
                onClick={handleRetrain}
                disabled={retraining}
              >
                {retraining ? 'Retraining...' : 'Retrain ML Model'}
              </button>
            </div>
          )}
        </div>

        {retrainMsg && <div className="retrain-msg">{retrainMsg}</div>}
        {loading && <p className="loading-text">Loading reports...</p>}
        {error && <p className="result-error">{error}</p>}

        {reports && (
          <>
            {/* ── 1. Application Summary ─────────────────────────── */}
            <section className="report-section">
              <h2>Loan Application Summary</h2>
              <div className="stats-grid">
                <div className="stat-card stat-total">
                  <div className="stat-label">Total Applications</div>
                  <div className="stat-value">{reports.summary.total}</div>
                </div>
                <div className="stat-card stat-approved">
                  <div className="stat-label">Approved</div>
                  <div className="stat-value">{reports.summary.approved}</div>
                </div>
                <div className="stat-card stat-rejected">
                  <div className="stat-label">Rejected</div>
                  <div className="stat-value">{reports.summary.rejected}</div>
                </div>
                <div className="stat-card stat-pending">
                  <div className="stat-label">Pending</div>
                  <div className="stat-value">{reports.summary.pending}</div>
                </div>
              </div>
            </section>

            {/* ── 2 & 3. Risk Distribution + Loan Type ──────────── */}
            <div className="two-col">
              <section className="report-section">
                <h2>Risk Distribution</h2>
                <BarChart
                  data={reports.risk_distribution}
                  labelKey="risk_level"
                  valueKey="count"
                  colorMap={riskColors}
                />
              </section>

              <section className="report-section">
                <h2>Loan Type Breakdown</h2>
                <BarChart
                  data={reports.loan_type_breakdown}
                  labelKey="loan_type"
                  valueKey="count"
                  colorMap={typeColors}
                />
              </section>
            </div>

            {/* ── 4. Loan Amount Analysis ────────────────────────── */}
            <section className="report-section">
              <h2>Loan Amount Analysis</h2>
              <div className="amount-grid">
                <div className="amount-card">
                  <div className="amount-label">Total Requested</div>
                  <div className="amount-value">
                    ₹{Number(reports.amount_analysis.total_requested).toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="amount-card">
                  <div className="amount-label">Total Recommended</div>
                  <div className="amount-value green">
                    ₹{Number(reports.amount_analysis.total_recommended).toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="amount-card">
                  <div className="amount-label">Average Loan Size</div>
                  <div className="amount-value">
                    ₹{Number(reports.amount_analysis.average_loan).toLocaleString('en-IN')}
                  </div>
                </div>
              </div>
            </section>

            {/* ── Monthly Approvals ───────────────────────────────── */}
            <section className="report-section">
              <h2>Monthly Approvals Trend</h2>
              <div className="monthly-legend">
                <span style={{ color: '#22c55e' }}>&#9646; Approved</span>
                <span style={{ color: '#ef4444' }}>&#9646; Rejected</span>
                <span style={{ color: '#f59e0b' }}>&#9646; Pending</span>
              </div>
              <MonthlyChart data={monthlyStats} />
            </section>

            {/* ── 5. Officer Performance ─────────────────────────── */}
            <section className="report-section">
              <h2>Loan Officer Performance</h2>
              {reports.officer_performance.length === 0 ? (
                <p className="empty-text">No loan officers found.</p>
              ) : (
                <table className="apps-table">
                  <thead>
                    <tr>
                      <th>Officer</th>
                      <th>Total Applications</th>
                      <th>Approved</th>
                      <th>Rejected</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.officer_performance.map((o) => (
                      <tr key={o.username}>
                        <td>{o.username}</td>
                        <td>{o.applications}</td>
                        <td>
                          <span className="badge badge-approved">{o.approved}</span>
                        </td>
                        <td>
                          <span className="badge badge-rejected">{o.rejected}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
