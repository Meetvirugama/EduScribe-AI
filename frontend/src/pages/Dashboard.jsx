import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import UploadModal from '../components/UploadModal';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const [videos, setVideos] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { token } = useAuth();
  const navigate = useNavigate();

  const fetchVideos = async () => {
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
  };
  
  const fetchAnalytics = async () => {
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
  };

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
    const interval = setInterval(() => {
        fetchVideos();
        fetchAnalytics();
    }, 5000); 
    return () => clearInterval(interval);
  }, [token]);

  return (
    <div className="dashboard-container" style={{ padding: '2rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>My Library</h1>
        <button 
          onClick={() => setIsModalOpen(true)}
          style={{ padding: '0.75rem 1.5rem', background: '#4F46E5', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
        >
          Add Content
        </button>
      </header>

      {analytics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151' }}>
              <h3 style={{ margin: 0, color: '#9CA3AF', fontSize: '0.875rem' }}>Total Videos Processed</h3>
              <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: 'white' }}>{analytics.total_videos}</p>
            </div>
            <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151' }}>
              <h3 style={{ margin: 0, color: '#9CA3AF', fontSize: '0.875rem' }}>Learning Minutes</h3>
              <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: 'white' }}>{analytics.total_learning_minutes}</p>
            </div>
            <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151' }}>
              <h3 style={{ margin: 0, color: '#9CA3AF', fontSize: '0.875rem' }}>Words Transcribed</h3>
              <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: 'white' }}>{analytics.total_words_generated.toLocaleString()}</p>
            </div>
        </div>
      )}

      <div className="video-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {videos.map(v => (
          <div key={v.id} className="video-card" style={{ padding: '1.5rem', background: '#1F2937', borderRadius: '12px', color: 'white', position: 'relative' }}>
            <button 
              onClick={() => deleteVideo(v.id)}
              style={{ position: 'absolute', top: '10px', right: '10px', background: '#EF4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', padding: '0.25rem 0.5rem' }}
            >
              Delete
            </button>
            <h3 style={{ marginTop: 0, paddingRight: '40px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.title}</h3>
            <p style={{ color: '#9CA3AF', margin: '0.5rem 0' }}>Type: {v.source_type}</p>
            
            {v.status === 'PROCESSING' || v.status === 'UPLOADING' || v.status === 'TRANSCRIBING' ? (
              <div style={{ marginTop: '1rem', background: '#374151', borderRadius: '8px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.5rem', color: '#D1D5DB' }}>
                  <span>{v.current_step || 'Initializing'}</span>
                  <span>{v.progress_percent || 0}%</span>
                </div>
                <div style={{ width: '100%', height: '8px', background: '#4B5563', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${v.progress_percent || 0}%`, height: '100%', background: '#4F46E5', transition: 'width 0.5s ease-in-out' }}></div>
                </div>
                {v.estimated_time_remaining_seconds > 0 && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#9CA3AF', textAlign: 'right' }}>
                    ETA: ~{v.estimated_time_remaining_seconds}s
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: '#9CA3AF', margin: '0.5rem 0' }}>Status: <strong>{v.status}</strong></p>
            )}

            {v.status === 'FAILED' && v.error_message && (
              <div style={{ marginTop: '0.5rem', padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #EF4444', borderRadius: '6px' }}>
                <p style={{ color: '#FCA5A5', margin: 0, fontSize: '0.875rem' }}>
                  {v.error_message.includes('youtube_bot_protection') || v.error_message.includes('Sign in to confirm')
                    ? 'This video is protected by YouTube and cannot be downloaded automatically. Please upload the video file manually to continue transcription.'
                    : `Error: ${v.error_message}`}
                </p>
              </div>
            )}
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              {v.status === 'COMPLETED' && (
                <button 
                  onClick={() => navigate(`/video/${v.id}`)}
                  style={{ padding: '0.5rem 1rem', background: '#10B981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                >
                  View Workspace
                </button>
              )}
            </div>
          </div>
        ))}
        {videos.length === 0 && (
          <p style={{ color: '#9CA3AF' }}>No content yet. Click "Add Content" to get started.</p>
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
