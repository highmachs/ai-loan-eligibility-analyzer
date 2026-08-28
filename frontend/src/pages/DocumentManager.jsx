import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import './DocumentManager.css';

const DOC_TYPES = ['PAN_CARD', 'AADHAAR', 'FORM_16', 'BANK_STATEMENT'];

const DOC_LABELS = {
  PAN_CARD: 'PAN Card',
  AADHAAR: 'Masked Aadhaar',
  FORM_16: 'Form 16 / ITR',
  BANK_STATEMENT: '6-Month Bank Statement',
};

const STATUS_CLASS = {
  PENDING: 'badge-pending',
  VERIFIED: 'badge-approved',
  REJECTED: 'badge-rejected',
};

export default function DocumentManager() {
  const { customerId } = useParams();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const canVerify = user.role === 'ADMIN' || user.role === 'SENIOR_CREDIT_MANAGER';

  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ document_type: DOC_TYPES[0], document_number: '' });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  const [verifyingId, setVerifyingId] = useState(null);

  const fetchDocs = () =>
    client
      .get(`/api/documents/customer/${customerId}`)
      .then((res) => setDocs(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load documents.'))
      .finally(() => setLoading(false));

  useEffect(() => {
    fetchDocs();
  }, [customerId]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.document_number.trim()) {
      setFormError('Document number is required.');
      return;
    }
    setSubmitting(true);
    setFormError('');
    setFormSuccess('');
    try {
      await client.post('/api/documents/', {
        customer_id: parseInt(customerId),
        document_type: form.document_type,
        document_number: form.document_number.trim(),
      });
      setFormSuccess('Document added successfully.');
      setForm({ document_type: DOC_TYPES[0], document_number: '' });
      await fetchDocs();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to add document.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (docId, verificationStatus) => {
    setVerifyingId(docId);
    try {
      await client.patch(`/api/documents/${docId}/verify`, { verification_status: verificationStatus });
      await fetchDocs();
    } catch (err) {
      alert(err.response?.data?.detail || 'Verification failed.');
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="doc-root">
      <nav className="result-nav">
        <Link to="/dashboard" className="back-link">← Dashboard</Link>
        <span className="result-nav-title">Document Manager — Customer #{customerId}</span>
      </nav>

      <div className="doc-container">
        {/* ── Add Document Form ── */}
        <section className="doc-section">
          <h2>Upload Document Record</h2>
          <form className="doc-form" onSubmit={handleAdd}>
            <div className="doc-form-row">
              <label htmlFor="doc-type-select">Document Type</label>
              <select
                id="doc-type-select"
                value={form.document_type}
                onChange={(e) => setForm({ ...form, document_type: e.target.value })}
              >
                {DOC_TYPES.map((t) => (
                  <option key={t} value={t}>{DOC_LABELS[t]}</option>
                ))}
              </select>
            </div>
            <div className="doc-form-row">
              <label htmlFor="doc-number-input">Document Number</label>
              <input
                id="doc-number-input"
                type="text"
                placeholder="e.g. ABCDE1234F"
                value={form.document_number}
                onChange={(e) => setForm({ ...form, document_number: e.target.value })}
                maxLength={50}
              />
            </div>
            {formError && <p className="result-error">{formError}</p>}
            {formSuccess && <p className="doc-success">{formSuccess}</p>}
            <button
              id="add-doc-btn"
              type="submit"
              className="primary-btn"
              disabled={submitting}
            >
              {submitting ? 'Adding…' : '+ Add Document'}
            </button>
          </form>
        </section>

        {/* ── Document List ── */}
        <section className="doc-section">
          <h2>Document Records</h2>
          {loading ? (
            <p className="loading-text">Loading documents…</p>
          ) : error ? (
            <p className="result-error">{error}</p>
          ) : docs.length === 0 ? (
            <p className="empty-text">No documents uploaded for this customer yet.</p>
          ) : (
            <table className="apps-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Number</th>
                  <th>Status</th>
                  <th>Added</th>
                  {canVerify && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {docs.map((doc) => (
                  <tr key={doc.id}>
                    <td>{DOC_LABELS[doc.document_type] || doc.document_type}</td>
                    <td className="doc-number">{doc.document_number}</td>
                    <td>
                      <span className={`badge ${STATUS_CLASS[doc.verification_status] || ''}`}>
                        {doc.verification_status}
                      </span>
                    </td>
                    <td>{new Date(doc.created_at).toLocaleDateString('en-IN')}</td>
                    {canVerify && (
                      <td className="doc-actions">
                        {doc.verification_status === 'PENDING' ? (
                          <>
                            <button
                              id={`verify-btn-${doc.id}`}
                              className="action-btn approve-btn doc-action-btn"
                              onClick={() => handleVerify(doc.id, 'VERIFIED')}
                              disabled={verifyingId === doc.id}
                            >
                              Verify
                            </button>
                            <button
                              id={`reject-doc-btn-${doc.id}`}
                              className="action-btn reject-btn doc-action-btn"
                              onClick={() => handleVerify(doc.id, 'REJECTED')}
                              disabled={verifyingId === doc.id}
                            >
                              Reject
                            </button>
                          </>
                        ) : (
                          <span className="doc-actioned">
                            {doc.verification_status === 'VERIFIED' ? '✓ Verified' : '✕ Rejected'}
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <Link
            to={`/customers/${customerId}/history`}
            id="view-customer-history-btn"
            className="link-btn"
            style={{ display: 'inline-block' }}
          >
            📊 View Customer Lifetime History →
          </Link>
        </div>
      </div>
    </div>
  );
}
