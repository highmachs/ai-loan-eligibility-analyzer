import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import './UserManagement.css';

const ROLE_LABELS = {
  ADMIN: 'Admin',
  SENIOR_CREDIT_MANAGER: 'Senior Credit Manager',
  LOAN_OFFICER: 'Loan Officer',
};

const ROLE_CLASS = {
  ADMIN: 'badge-approved',
  SENIOR_CREDIT_MANAGER: 'badge-pending',
  LOAN_OFFICER: 'badge-rejected',
};

export default function UserManagement() {
  const navigate = useNavigate();
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [form, setForm] = useState({ username: '', password: '', role: 'LOAN_OFFICER' });
  const [showUserPassword, setShowUserPassword] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [actionMsg, setActionMsg] = useState('');
  const [actionId, setActionId] = useState(null);

  const fetchUsers = () =>
    client
      .get('/api/admin/users')
      .then((res) => setUsers(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load users.'))
      .finally(() => setLoading(false));

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.username.trim() || !form.password.trim()) {
      setFormError('Username and password are required.');
      return;
    }
    setSubmitting(true);
    setFormError('');
    setFormSuccess('');
    try {
      await client.post('/api/admin/users', form);
      setFormSuccess(`User "${form.username}" created successfully.`);
      setForm({ username: '', password: '', role: 'LOAN_OFFICER' });
      await fetchUsers();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create user.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (userId, username) => {
    if (!window.confirm(`Delete user "${username}"? This cannot be undone.`)) return;
    setActionId(userId);
    setActionMsg('');
    try {
      await client.delete(`/api/admin/users/${userId}`);
      setActionMsg(`User "${username}" deleted.`);
      await fetchUsers();
    } catch (err) {
      setActionMsg(err.response?.data?.detail || 'Delete failed.');
    } finally {
      setActionId(null);
    }
  };

  const handleRoleChange = async (userId, currentRole) => {
    // B6: 3-tier cycle — LOAN_OFFICER → SENIOR_CREDIT_MANAGER → ADMIN → LOAN_OFFICER
    const next = currentRole === 'LOAN_OFFICER'
      ? 'SENIOR_CREDIT_MANAGER'
      : currentRole === 'SENIOR_CREDIT_MANAGER'
      ? 'ADMIN'
      : 'LOAN_OFFICER';
    if (!window.confirm(`Change role to ${ROLE_LABELS[next] || next}?`)) return;
    setActionId(userId);
    try {
      await client.patch(`/api/admin/users/${userId}/role`, { role: next });
      await fetchUsers();
    } catch (err) {
      setActionMsg(err.response?.data?.detail || 'Role change failed.');
    } finally {
      setActionId(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="um-root">
      <nav className="navbar">
        <div className="navbar-brand">Loan Eligibility Analyzer</div>
        <div className="navbar-right">
          <Link to="/admin" className="nav-link">← Admin Reports</Link>
          <span className="navbar-user">{currentUser.username} &mdash; ADMIN</span>
          <button id="logout-btn" className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <main className="um-main">
        <div className="admin-header">
          <h1>User Management</h1>
        </div>

        {/* ── Create User Form ── */}
        <section className="um-section">
          <h2>Create New User</h2>
          <form className="um-form" onSubmit={handleCreate}>
            <div className="um-form-row">
              <label htmlFor="um-username">Username</label>
              <input
                id="um-username"
                type="text"
                placeholder="e.g. officer2"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                minLength={3}
                maxLength={50}
                autoComplete="off"
              />
            </div>
            <div className="um-form-row">
              <label htmlFor="um-password">Password</label>
              <div className="password-input-wrapper">
                <input
                  id="um-password"
                  type={showUserPassword ? 'text' : 'password'}
                  placeholder="Min 6 characters"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  minLength={6}
                  maxLength={72}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowUserPassword(!showUserPassword)}
                  aria-label={showUserPassword ? 'Hide password' : 'Show password'}
                  title={showUserPassword ? 'Hide password' : 'Show password'}
                >
                  {showUserPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            <div className="um-form-row">
              <label htmlFor="um-role">Role</label>
              <select
                id="um-role"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
                <option value="LOAN_OFFICER">Loan Officer</option>
                <option value="SENIOR_CREDIT_MANAGER">Senior Credit Manager</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
            {formError && <p className="result-error">{formError}</p>}
            {formSuccess && <p className="um-success">{formSuccess}</p>}
            <button id="create-user-btn" type="submit" className="primary-btn" disabled={submitting}>
              {submitting ? 'Creating…' : '+ Create User'}
            </button>
          </form>
        </section>

        {/* ── Users Table ── */}
        <section className="um-section">
          <h2>All Users</h2>
          {actionMsg && <p className="um-action-msg">{actionMsg}</p>}
          {loading ? (
            <p className="loading-text">Loading users…</p>
          ) : error ? (
            <p className="result-error">{error}</p>
          ) : (
            <table className="apps-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className={u.id === currentUser.id ? 'um-self-row' : ''}>
                    <td>{u.id}</td>
                    <td>
                      {u.username}
                      {u.id === currentUser.id && <span className="um-you-tag"> (you)</span>}
                    </td>
                    <td>
                      <span className={`badge ${ROLE_CLASS[u.role] || ''}`}>
                        {ROLE_LABELS[u.role] || u.role}
                      </span>
                    </td>
                    <td className="um-actions">
                      {u.id !== currentUser.id ? (
                        <>
                          <button
                            id={`role-btn-${u.id}`}
                            className="action-btn approve-btn doc-action-btn"
                            onClick={() => handleRoleChange(u.id, u.role)}
                            disabled={actionId === u.id}
                          >
                            {u.role === 'ADMIN'
                              ? '↓ To SCM'
                              : u.role === 'SENIOR_CREDIT_MANAGER'
                              ? '↑ To Admin'
                              : '↑ To SCM'}
                          </button>
                          <button
                            id={`delete-user-btn-${u.id}`}
                            className="action-btn reject-btn doc-action-btn"
                            onClick={() => handleDelete(u.id, u.username)}
                            disabled={actionId === u.id}
                          >
                            Delete
                          </button>
                        </>
                      ) : (
                        <span className="doc-actioned">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
}
