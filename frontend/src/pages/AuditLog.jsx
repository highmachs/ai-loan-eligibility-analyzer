import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import './AuditLog.css';

const ACTION_CLASS = {
  CREATED: 'badge-pending',
  AI_SCORED: 'badge-ai',
  APPROVED: 'badge-approved',
  REJECTED: 'badge-rejected',
  DOCUMENT_VERIFIED: 'badge-approved',
  DOCUMENT_REJECTED: 'badge-rejected',
};

export default function AuditLog() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterAppId, setFilterAppId] = useState('');

  const fetchLogs = (appId) => {
    const url = appId
      ? `/api/audit-logs/?application_id=${appId}`
      : '/api/audit-logs/';
    setLoading(true);
    client
      .get(url)
      .then((res) => setLogs(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load audit logs.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs('');
  }, []);

  const handleFilter = (e) => {
    e.preventDefault();
    fetchLogs(filterAppId.trim());
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="audit-root">
      <nav className="navbar">
        <div className="navbar-brand">Loan Eligibility Analyzer</div>
        <div className="navbar-right">
          <Link to="/admin" className="nav-link">← Admin Reports</Link>
          <span className="navbar-user">{user.username} &mdash; ADMIN</span>
          <button id="logout-btn" className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <main className="audit-main">
        <div className="admin-header">
          <h1>System Audit Logs</h1>
          <form className="filter-form" onSubmit={handleFilter}>
            <input
              id="filter-app-id"
              type="number"
              placeholder="Filter by Application ID…"
              value={filterAppId}
              onChange={(e) => setFilterAppId(e.target.value)}
              min={1}
            />
            <button id="filter-btn" type="submit" className="primary-btn">Filter</button>
            {filterAppId && (
              <button
                id="clear-filter-btn"
                type="button"
                className="logout-btn"
                onClick={() => { setFilterAppId(''); fetchLogs(''); }}
              >
                Clear
              </button>
            )}
          </form>
        </div>

        {loading && <p className="loading-text">Loading audit trail…</p>}
        {error && <p className="result-error">{error}</p>}

        {!loading && !error && (
          <>
            {logs.length === 0 ? (
              <p className="empty-text">No audit entries found.</p>
            ) : (
              <div className="table-section">
                <table className="apps-table audit-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>User ID</th>
                      <th>App ID</th>
                      <th>Action</th>
                      <th>Previous</th>
                      <th>New</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td className="audit-ts">
                          {new Date(log.timestamp).toLocaleString('en-IN')}
                        </td>
                        <td>{log.user_id}</td>
                        <td>
                          {log.application_id ? (
                            <Link to={`/prediction/${log.application_id}`} className="link-btn">
                              #{log.application_id}
                            </Link>
                          ) : '—'}
                        </td>
                        <td>
                          <span className={`badge ${ACTION_CLASS[log.action] || ''}`}>
                            {log.action.replace('_', ' ')}
                          </span>
                        </td>
                        <td>{log.previous_status || '—'}</td>
                        <td>{log.new_status || '—'}</td>
                        <td>{log.ip_address || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
