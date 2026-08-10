import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../lib/api';
import { User, HardDrive, Clock, LogOut, Shield } from 'lucide-react';
import './Settings.css';

const sortByExpiration = (videos) =>
  [...videos].sort((a, b) => {
    const da = new Date(a.created_at).getTime() + a.retention_days * 86400000;
    const db = new Date(b.created_at).getTime() + b.retention_days * 86400000;
    return da - db;
  });

const formatBytes = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default function Settings() {
  const { token, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [storage, setStorage] = useState(null);
  const [videos, setVideos] = useState([]);

  useEffect(() => {
    if (!token) return;
    apiFetch('/auth/me', {}, token).then(r => r.json()).then(setProfile).catch(console.error);
    apiFetch('/videos/storage', {}, token).then(r => r.json()).then(setStorage).catch(console.error);
    apiFetch('/videos', {}, token).then(r => r.json()).then(data => setVideos(sortByExpiration(data))).catch(console.error);
  }, [token]);

  const handleRetentionChange = async (videoId, newDays) => {
    try {
      const res = await apiFetch(`/videos/${videoId}/retention`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ retention_days: newDays }),
      }, token);
      if (res.ok) {
        const updated = await res.json();
        setVideos(prev => sortByExpiration(prev.map(v => v.id === updated.id ? updated : v)));
      }
    } catch (err) { console.error(err); }
  };

  const storagePercent = storage
    ? Math.min(Math.round((storage.total_used_bytes / (10 * 1024 * 1024 * 1024)) * 100), 100)
    : 0;

  return (
    <div className="settings-container">
      <header className="settings-header">
        <h1>Settings &amp; Analytics</h1>
        <p className="settings-subtitle">Manage your profile, storage, and data retention</p>
      </header>

      <div className="settings-grid">
        {/* ── Left Column ── */}
        <div className="settings-left">

          {/* Profile Card */}
          <div className="settings-card">
            <div className="settings-card-header">
              <div className="settings-card-icon settings-card-icon--blue">
                <User size={18} />
              </div>
              <h2>User Profile</h2>
            </div>
            {profile ? (
              <div className="settings-profile-body">
                <div className="settings-avatar-wrap">
                  {profile.picture
                    ? <img src={profile.picture} alt="Avatar" className="settings-avatar" />
                    : <div className="settings-avatar-placeholder">{(profile.name || '?')[0].toUpperCase()}</div>
                  }
                  <div className="settings-profile-badge">
                    <Shield size={10} /> Verified
                  </div>
                </div>
                <div className="settings-profile-info">
                  <h3>{profile.name}</h3>
                  <p>{profile.email}</p>
                  <p className="settings-profile-joined">
                    Joined {profile.join_date ? new Date(profile.join_date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : '—'}
                  </p>
                </div>
              </div>
            ) : (
              <p className="settings-loading-text">Loading profile…</p>
            )}
            <button
              id="sign-out-btn"
              onClick={logout}
              className="settings-signout-btn"
            >
              <LogOut size={16} /> Sign Out
            </button>
          </div>

          {/* Storage Card */}
          <div className="settings-card">
            <div className="settings-card-header">
              <div className="settings-card-icon settings-card-icon--green">
                <HardDrive size={18} />
              </div>
              <h2>Storage Consumption</h2>
            </div>
            {storage ? (
              <div className="settings-storage-body">
                <div className="settings-storage-total">
                  <span>{formatBytes(storage.total_used_bytes)}</span>
                  <span className="settings-storage-limit">/ 10 GB</span>
                </div>
                <div className="settings-storage-bar-bg">
                  <div
                    className="settings-storage-bar-fill"
                    style={{ width: `${storagePercent}%` }}
                  />
                </div>
                <p className="settings-storage-percent">{storagePercent}% used</p>
                <div className="settings-storage-breakdown">
                  <div className="settings-storage-row">
                    <span>Videos &amp; Audio</span>
                    <strong>{formatBytes(storage.videos_bytes)}</strong>
                  </div>
                  <div className="settings-storage-row">
                    <span>Transcripts &amp; Notes</span>
                    <strong>{formatBytes(storage.transcripts_bytes)}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <p className="settings-loading-text">Loading storage…</p>
            )}
          </div>
        </div>

        {/* ── Right Column — Retention Center ── */}
        <div className="settings-card settings-retention-card">
          <div className="settings-card-header">
            <div className="settings-card-icon settings-card-icon--amber">
              <Clock size={18} />
            </div>
            <h2>Retention Center</h2>
          </div>

          <div className="settings-retention-list">
            {videos.length === 0 ? (
              <p className="settings-loading-text">No content in retention.</p>
            ) : (
              videos.map(v => {
                const expiresAt = new Date(new Date(v.created_at).getTime() + v.retention_days * 86400000);
                const daysLeft = Math.ceil((expiresAt.getTime() - Date.now()) / 86400000);
                const isUrgent = daysLeft <= 2;
                const accentColor = isUrgent ? '#EF4444' : '#10B981';

                return (
                  <div
                    key={v.id}
                    className="settings-retention-item"
                    style={{ borderLeftColor: accentColor }}
                  >
                    <div className="settings-retention-info">
                      <p className="settings-retention-title">{v.title}</p>
                      <span className="settings-retention-source">{v.source_type}</span>
                    </div>
                    <div className="settings-retention-controls">
                      <div className="settings-retention-expiry" style={{ color: isUrgent ? '#EF4444' : '#E5E7EB' }}>
                        <strong>{daysLeft > 0 ? `${daysLeft}d left` : 'Expired'}</strong>
                        <span>{expiresAt.toLocaleDateString()}</span>
                      </div>
                      <select
                        id={`retention-select-${v.id}`}
                        value={v.retention_days}
                        onChange={e => handleRetentionChange(v.id, parseInt(e.target.value))}
                        className="settings-retention-select"
                      >
                        <option value={7}>7 Days</option>
                        <option value={14}>14 Days</option>
                        <option value={30}>30 Days</option>
                      </select>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
