import { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../lib/api';
import { Upload, Link2, X, Loader } from 'lucide-react';
import './UploadModal.css';

export default function UploadModal({ onClose, onSuccess }) {
  const [tab, setTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [retentionDays, setRetentionDays] = useState(7);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef(null);
  const { token } = useAuth();

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      let res;
      if (tab === 'upload') {
        if (!file) { setErrorMsg('Please select a file.'); setLoading(false); return; }
        const formData = new FormData();
        formData.append('file', file);
        formData.append('retention_days', retentionDays);
        res = await apiFetch('/videos/upload', { method: 'POST', body: formData }, token);
      } else {
        if (!url) { setErrorMsg('Please enter a YouTube URL.'); setLoading(false); return; }
        res = await apiFetch('/videos/youtube', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, retention_days: retentionDays }),
        }, token);
      }

      if (res.ok) {
        onSuccess();
      } else {
        if (res.status === 401) {
          setErrorMsg('Your session has expired. Please log out and log back in.');
        } else {
          const data = await res.json().catch(() => ({}));
          setErrorMsg(data.detail || 'Failed to add content. Please try again.');
        }
      }
    } catch {
      setErrorMsg('A network error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-card">
        {/* Header */}
        <div className="modal-header">
          <h2>Add Content</h2>
          <button id="modal-close-btn" className="modal-close-btn" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="modal-tabs">
          <button
            id="tab-file-upload"
            className={`modal-tab ${tab === 'upload' ? 'modal-tab--active' : ''}`}
            onClick={() => setTab('upload')}
          >
            <Upload size={16} /> File Upload
          </button>
          <button
            id="tab-youtube-url"
            className={`modal-tab ${tab === 'youtube' ? 'modal-tab--active' : ''}`}
            onClick={() => setTab('youtube')}
          >
            <Link2 size={16} /> YouTube URL
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {errorMsg && (
            <div className="modal-error">
              <span>⚠️</span> {errorMsg}
            </div>
          )}

          {/* Retention */}
          <div className="modal-field">
            <label className="modal-label">Retention Policy</label>
            <select
              id="retention-days-select"
              value={retentionDays}
              onChange={(e) => setRetentionDays(parseInt(e.target.value))}
              className="modal-select"
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days (Maximum)</option>
            </select>
            <p className="modal-hint">Data is automatically deleted after the selected duration.</p>
          </div>

          {/* File Upload Tab */}
          {tab === 'upload' ? (
            <div className="modal-field">
              <label className="modal-label">Video / Audio File</label>
              <div
                className={`modal-dropzone ${dragging ? 'modal-dropzone--drag' : ''} ${file ? 'modal-dropzone--has-file' : ''}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
              >
                <input
                  id="file-input"
                  ref={fileInputRef}
                  type="file"
                  accept="video/*,audio/*"
                  onChange={(e) => setFile(e.target.files[0])}
                  style={{ display: 'none' }}
                />
                {file ? (
                  <div className="modal-dropzone-file">
                    <span className="modal-dropzone-file-icon">🎬</span>
                    <div>
                      <p className="modal-dropzone-filename">{file.name}</p>
                      <p className="modal-dropzone-size">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                    </div>
                    <button
                      type="button"
                      className="modal-dropzone-remove"
                      onClick={(e) => { e.stopPropagation(); setFile(null); }}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ) : (
                  <div className="modal-dropzone-empty">
                    <Upload size={28} className="modal-dropzone-icon" />
                    <p className="modal-dropzone-text">
                      <strong>Click to browse</strong> or drag &amp; drop
                    </p>
                    <p className="modal-dropzone-hint">MP4, MKV, MOV, AVI, WEBM, MP3, WAV</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="modal-field">
              <label className="modal-label" htmlFor="youtube-url-input">YouTube URL</label>
              <div className="modal-url-wrap">
                <Link2 size={16} className="modal-url-icon" />
                <input
                  id="youtube-url-input"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://youtube.com/watch?v=..."
                  className="modal-url-input"
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="modal-actions">
            <button
              type="button"
              id="modal-cancel-btn"
              onClick={onClose}
              className="modal-btn modal-btn--cancel"
            >
              Cancel
            </button>
            <button
              type="submit"
              id="modal-submit-btn"
              disabled={loading}
              className="modal-btn modal-btn--submit"
            >
              {loading ? <><Loader size={16} className="modal-spinner" /> Processing…</> : 'Add Content'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
