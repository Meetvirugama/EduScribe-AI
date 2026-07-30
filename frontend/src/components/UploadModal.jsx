import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function UploadModal({ onClose, onSuccess }) {
  const [tab, setTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [retentionDays, setRetentionDays] = useState(7);
  const { token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    
    try {
      let res;
      if (tab === 'upload') {
        if (!file) {
          setErrorMsg('Please select a file.');
          setLoading(false);
          return;
        }
        const formData = new FormData();
        formData.append('file', file);
        formData.append('retention_days', retentionDays);
        
        res = await fetch('http://localhost:5001/videos/upload', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData,
        });
      } else {
        if (!url) {
          setErrorMsg('Please enter a YouTube URL.');
          setLoading(false);
          return;
        }
        res = await fetch('http://localhost:5001/videos/youtube', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}` 
          },
          body: JSON.stringify({ url, retention_days: retentionDays }),
        });
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
    } catch (err) {
      console.error(err);
      setErrorMsg('A network error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: '#1F2937', padding: '2rem', borderRadius: '12px', width: '100%', maxWidth: '500px', color: 'white' }}>
        <h2 style={{ marginTop: 0 }}>Add Content</h2>
        
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid #374151', paddingBottom: '0.5rem' }}>
          <button 
            style={{ background: 'none', border: 'none', color: tab === 'upload' ? '#60A5FA' : '#9CA3AF', cursor: 'pointer', fontSize: '1rem', fontWeight: tab === 'upload' ? 'bold' : 'normal' }}
            onClick={() => setTab('upload')}
          >File Upload</button>
          <button 
            style={{ background: 'none', border: 'none', color: tab === 'youtube' ? '#60A5FA' : '#9CA3AF', cursor: 'pointer', fontSize: '1rem', fontWeight: tab === 'youtube' ? 'bold' : 'normal' }}
            onClick={() => setTab('youtube')}
          >YouTube URL</button>
        </div>

        <form onSubmit={handleSubmit}>
          {errorMsg && (
            <div style={{ padding: '0.75rem', marginBottom: '1rem', background: '#DC2626', color: 'white', borderRadius: '6px', fontSize: '0.9rem' }}>
              {errorMsg}
            </div>
          )}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#D1D5DB' }}>Retention Policy</label>
            <select 
              value={retentionDays} 
              onChange={(e) => setRetentionDays(parseInt(e.target.value))}
              style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #4B5563', background: '#374151', color: 'white' }}
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days (Maximum)</option>
            </select>
            <p style={{ fontSize: '0.8rem', color: '#9CA3AF', margin: '0.5rem 0 0 0' }}>Data will be automatically deleted after the selected duration.</p>
          </div>
          {tab === 'upload' ? (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem' }}>Select Video/Audio File</label>
              <input type="file" onChange={(e) => setFile(e.target.files[0])} accept="video/*,audio/*" style={{ width: '100%' }} />
            </div>
          ) : (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem' }}>YouTube URL</label>
              <input 
                type="url" 
                value={url} 
                onChange={(e) => setUrl(e.target.value)} 
                placeholder="https://youtube.com/watch?v=..." 
                style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #4B5563', background: '#374151', color: 'white' }} 
              />
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
            <button type="button" onClick={onClose} style={{ padding: '0.5rem 1rem', background: 'none', border: '1px solid #4B5563', color: 'white', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
            <button type="submit" disabled={loading} style={{ padding: '0.5rem 1rem', background: '#4F46E5', border: 'none', color: 'white', borderRadius: '6px', cursor: 'pointer' }}>
              {loading ? 'Processing...' : 'Add Content'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
