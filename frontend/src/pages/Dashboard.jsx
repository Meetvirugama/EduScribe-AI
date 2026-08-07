import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import UploadModal from '../components/UploadModal';
import './Dashboard.css';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const [videos, setVideos] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { token } = useAuth();
  const navigate = useNavigate();

  const fetchVideos = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:5001/videos', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setVideos(data);
      }
    } catch (err) {
      console.error("Failed to fetch videos", err);
    }
  }, [token]);
  
  const fetchAnalytics = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:5001/videos/analytics', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error("Failed to fetch analytics", err);
    }
  }, [token]);

  const deleteVideo = async (id) => {
    if (!token) return;
    if (!confirm('Are you sure you want to delete this video?')) return;
    try {
      const res = await fetch(`http://localhost:5001/videos/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchVideos();
        fetchAnalytics();
      } else {
        alert('Failed to delete video');
      }
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  useEffect(() => {
    fetchVideos();
    fetchAnalytics();
  }, [fetchVideos, fetchAnalytics]);

  useEffect(() => {
    const hasPending = videos.some(v => ['PROCESSING', 'UPLOADING', 'EXTRACTING_AUDIO', 'TRANSCRIBING', 'EXTRACTING_FRAMES', 'RUNNING_OCR', 'CHUNKING', 'DETECTING_TOPICS', 'GENERATING_NOTES', 'EXPORTING'].includes(v.status));
    const delay = hasPending ? 3000 : 30000;
    const timer = setTimeout(() => {
      fetchVideos();
      fetchAnalytics();
    }, delay);
    return () => clearTimeout(timer);
  }, [videos, fetchVideos, fetchAnalytics]);

  return (
    <div className="dashboard-container" >
      <header className="dashboard-header">
        <h1>My Library</h1>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="btn-add-content"
        >
          Add Content
        </button>
      </header>

      {analytics && (
        <div className="analytics-grid">
            <div className="analytics-card">
              <h3 >Total Videos Processed</h3>
              <p >{analytics.total_videos}</p>
            </div>
            <div className="analytics-card">
              <h3 >Learning Minutes</h3>
              <p >{analytics.total_learning_minutes}</p>
            </div>
            <div className="analytics-card">
              <h3 >Words Transcribed</h3>
              <p >{analytics.total_words_generated.toLocaleString()}</p>
            </div>
        </div>
      )}

      <div className="video-grid" >
        {videos.map(v => (
          <div key={v.id} className="video-card" >
            <button 
              onClick={() => deleteVideo(v.id)}
              className="btn-delete"
            >
              Delete
            </button>
            <h3 >{v.title}</h3>
            <p className="video-card-type">Type: {v.source_type}</p>
            
            {['PROCESSING', 'UPLOADING', 'EXTRACTING_AUDIO', 'TRANSCRIBING', 'EXTRACTING_FRAMES', 'RUNNING_OCR', 'CHUNKING', 'DETECTING_TOPICS', 'GENERATING_NOTES', 'EXPORTING'].includes(v.status) ? (
              <div className="progress-container">
                <div className="progress-text">
                  <span>{v.current_step || 'Initializing'}</span>
                  <span>{v.progress_percent || 0}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{ width: `${v.progress_percent || 0}%` }}></div>
                </div>
                {v.estimated_time_remaining_seconds > 0 && (
                  <div className="progress-eta">
                    ETA: ~{v.estimated_time_remaining_seconds}s
                  </div>
                )}
              </div>
            ) : (
              <p className="video-card-type">Status: <strong>{v.status}</strong></p>
            )}

            {v.status === 'FAILED' && v.error_message && (
              <div className="video-error">
                <p >
                  {v.error_message.includes('youtube_bot_protection') || v.error_message.includes('Sign in to confirm')
                    ? 'This video is protected by YouTube and cannot be downloaded automatically. Please upload the video file manually to continue transcription.'
                    : `Error: ${v.error_message}`}
                </p>
              </div>
            )}
            <div className="video-actions">
              {v.status === 'COMPLETED' && (
                <button 
                  onClick={() => navigate(`/video/${v.id}`)}
                  className="btn-view-workspace"
                >
                  View Workspace
                </button>
              )}
            </div>
          </div>
        ))}
        {videos.length === 0 && (
          <p className="no-content">No content yet. Click "Add Content" to get started.</p>
        )}
      </div>

      {isModalOpen && (
        <UploadModal 
          onClose={() => setIsModalOpen(false)} 
          onSuccess={() => {
            setIsModalOpen(false);
            fetchVideos();
            fetchAnalytics();
          }} 
        />
      )}
    </div>
  );
}
