import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import UploadModal from '../components/UploadModal';
import ConfirmModal from '../components/ConfirmModal';
import './Dashboard.css';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../lib/api';
import { useProgressStream } from '../hooks/useProgressStream';

const PROCESSING_STATUSES = [
  'PROCESSING', 'UPLOADING', 'EXTRACTING_AUDIO', 'TRANSCRIBING',
  'EXTRACTING_FRAMES', 'RUNNING_OCR', 'CHUNKING', 'DETECTING_TOPICS',
  'GENERATING_NOTES', 'EXPORTING',
];

const STATUS_COLORS = {
  COMPLETED: '#10B981',
  FAILED: '#EF4444',
  default: '#F59E0B',
};

const STATUS_LABELS = {
  COMPLETED: 'Completed',
  FAILED: 'Failed',
  UPLOADING: 'Uploading…',
  EXTRACTING_AUDIO: 'Extracting Audio…',
  TRANSCRIBING: 'Transcribing…',
  EXTRACTING_FRAMES: 'Extracting Frames…',
  RUNNING_OCR: 'Running OCR…',
  CHUNKING: 'Chunking…',
  DETECTING_TOPICS: 'Detecting Topics…',
  GENERATING_NOTES: 'Generating Notes…',
  EXPORTING: 'Exporting…',
  PROCESSING: 'Processing…',
};

// Individual card that hooks into SSE when processing
function VideoCard({ video, onDelete, onNavigate }) {
  const { token } = useAuth();
  const isProcessing = PROCESSING_STATUSES.includes(video.status);
  const { progress } = useProgressStream(isProcessing ? video.id : null, token);

  // Live values: prefer SSE data while processing, else fall back to DB data
  const liveProgress = progress?.progress ?? video.progress_percent ?? 0;
  const liveStep = progress?.step || video.current_step || 'Initializing…';
  const liveStatus = progress?.status || video.status;
  const isLiveProcessing = PROCESSING_STATUSES.includes(liveStatus);

  const statusColor = STATUS_COLORS[video.status] ?? STATUS_COLORS.default;

  return (
    <div className={`video-card ${isProcessing ? 'video-card--processing' : ''}`}>
      {/* Status pill */}
      <div className="video-card-status-pill" style={{ background: `${statusColor}22`, color: statusColor, borderColor: `${statusColor}44` }}>
        <span className={`status-dot ${isLiveProcessing ? 'status-dot--pulse' : ''}`} style={{ background: statusColor }} />
        {STATUS_LABELS[liveStatus] || liveStatus}
      </div>

      <button
        id={`delete-video-${video.id}`}
        onClick={() => onDelete(video.id)}
        className="btn-delete"
        aria-label="Delete video"
      >✕</button>

      <div className="video-card-body">
        <div className="video-card-icon">
          {video.source_type === 'YOUTUBE' ? '▶' : '🎬'}
        </div>
        <h3>{video.title || 'Untitled'}</h3>
        <span className="video-card-source">{video.source_type}</span>
      </div>

      {isLiveProcessing ? (
        <div className="progress-container">
          <div className="progress-text">
            <span>{liveStep}</span>
            <span>{liveProgress}%</span>
          </div>
          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ width: `${liveProgress}%` }} />
          </div>
          {video.estimated_time_remaining_seconds > 0 && (
            <div className="progress-eta">ETA: ~{video.estimated_time_remaining_seconds}s</div>
          )}
        </div>
      ) : (
        <div className="video-card-footer">
          {video.status === 'FAILED' && video.error_message && (
            <div className="video-error">
              <p>
                {video.error_message.includes('youtube_bot_protection') || video.error_message.includes('Sign in to confirm')
                  ? '⚠️ YouTube bot protection blocked this video. Please upload the file manually.'
                  : `⚠️ ${video.error_message}`}
              </p>
            </div>
          )}
          {video.status === 'COMPLETED' && (
            <button
              id={`view-workspace-${video.id}`}
              onClick={() => onNavigate(video.id)}
              className="btn-view-workspace"
            >
              Open Workspace →
            </button>
          )}
          {video.duration_seconds > 0 && (
            <span className="video-card-duration">
              {Math.round(video.duration_seconds / 60)} min
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [videos, setVideos] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState(null);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const navigate = useNavigate();

  const fetchVideos = useCallback(async () => {
    if (!token) return;
    try {
      const res = await apiFetch('/videos', {}, token);
      if (res.ok) setVideos(await res.json());
    } catch (err) { console.error('Failed to fetch videos', err); }
  }, [token]);

  const fetchAnalytics = useCallback(async () => {
    if (!token) return;
    try {
      const res = await apiFetch('/videos/analytics', {}, token);
      if (res.ok) setAnalytics(await res.json());
    } catch (err) { console.error('Failed to fetch analytics', err); }
  }, [token]);

  const requestDeleteVideo = (id) => {
    setVideoToDelete(id);
  };

  const confirmDeleteVideo = async () => {
    if (!videoToDelete) return;
    const id = videoToDelete;
    setVideoToDelete(null);
    try {
      const res = await apiFetch(`/videos/${id}`, { method: 'DELETE' }, token);
      if (res.ok) { fetchVideos(); fetchAnalytics(); }
      else alert('Failed to delete video');
    } catch (err) { console.error('Delete failed', err); }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await Promise.all([fetchVideos(), fetchAnalytics()]);
      setLoading(false);
    })();
  }, [fetchVideos, fetchAnalytics]);

  // Background polling for non-processing states (SSE handles the rest)
  useEffect(() => {
    const hasPending = videos.some(v => PROCESSING_STATUSES.includes(v.status));
    const delay = hasPending ? 15000 : 45000; // SSE is primary; polling is fallback
    const timer = setTimeout(() => { fetchVideos(); fetchAnalytics(); }, delay);
    return () => clearTimeout(timer);
  }, [videos, fetchVideos, fetchAnalytics]);

  const stats = [
    { label: 'Videos Processed', value: analytics?.total_videos ?? '—', icon: '🎬' },
    { label: 'Learning Minutes', value: analytics?.total_learning_minutes ?? '—', icon: '⏱️' },
    { label: 'Words Transcribed', value: analytics ? (analytics.total_words_generated).toLocaleString() : '—', icon: '📝' },
  ];

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div>
          <h1>My Library</h1>
          <p className="dashboard-subtitle">
            {loading ? 'Loading…' : `${videos.length} video${videos.length !== 1 ? 's' : ''} in your library`}
          </p>
        </div>
        <button
          id="add-content-btn"
          onClick={() => setIsModalOpen(true)}
          className="btn-add-content"
        >
          + Add Content
        </button>
      </header>

      {/* Analytics Row */}
      <div className="analytics-grid">
        {stats.map(s => (
          <div key={s.label} className="analytics-card">
            <span className="analytics-card-icon">{s.icon}</span>
            <div>
              <p className="analytics-card-value">{s.value}</p>
              <h3 className="analytics-card-label">{s.label}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* Video Grid */}
      {loading ? (
        <div className="dashboard-loading">
          <div className="dashboard-spinner" />
          <p>Loading your library…</p>
        </div>
      ) : videos.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎓</div>
          <h2>Your library is empty</h2>
          <p>Upload a video or paste a YouTube link to get AI-generated study notes.</p>
          <button id="empty-add-content-btn" onClick={() => setIsModalOpen(true)} className="btn-add-content">
            + Add Your First Video
          </button>
        </div>
      ) : (
        <div className="video-grid">
          {videos.map(v => (
            <VideoCard
              key={v.id}
              video={v}
              onDelete={requestDeleteVideo}
              onNavigate={(id) => navigate(`/video/${id}`)}
            />
          ))}
        </div>
      )}

      {isModalOpen && (
        <UploadModal
          onClose={() => setIsModalOpen(false)}
          onSuccess={() => { setIsModalOpen(false); fetchVideos(); fetchAnalytics(); }}
        />
      )}

      {videoToDelete && (
        <ConfirmModal
          title="Delete Video"
          message="Are you sure you want to delete this video and all its data? This action cannot be undone."
          confirmText="Delete Video"
          onConfirm={confirmDeleteVideo}
          onCancel={() => setVideoToDelete(null)}
          isDestructive={true}
        />
      )}
    </div>
  );
}
