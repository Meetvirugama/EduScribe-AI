import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { token, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [storage, setStorage] = useState(null);
  const [videos, setVideos] = useState([]);

  useEffect(() => {
    if (!token) return;

    fetch('http://localhost:5001/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setProfile(data))
    .catch(console.error);

    fetch('http://localhost:5001/videos/storage', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setStorage(data))
    .catch(console.error);

    fetch('http://localhost:5001/videos', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
      // Sort by soonest expiration
      const sorted = [...data].sort((a, b) => {
         const dateA = new Date(a.created_at).getTime() + (a.retention_days * 86400000);
         const dateB = new Date(b.created_at).getTime() + (b.retention_days * 86400000);
         return dateA - dateB;
      });
      setVideos(sorted);
    })
    .catch(console.error);
  }, [token]);

  const formatBytes = (bytes) => {
    if (bytes === 0 || !bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div style={{ padding: '2rem', color: 'white' }}>
      <h1 style={{ marginBottom: '2rem' }}>Settings & Analytics</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* User Profile */}
          <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#9CA3AF' }}>User Profile</h3>
            {profile ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {profile.picture ? (
                  <img src={profile.picture} alt="Avatar" style={{ width: '64px', height: '64px', borderRadius: '50%' }} />
                ) : (
                  <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#4B5563' }}></div>
                )}
                <div>
                  <h4 style={{ margin: '0 0 0.25rem 0', fontSize: '1.25rem' }}>{profile.name}</h4>
                  <p style={{ margin: 0, color: '#9CA3AF' }}>{profile.email}</p>
                </div>
              </div>
            ) : <p>Loading profile...</p>}
            <button onClick={logout} style={{ marginTop: '1.5rem', background: '#EF4444', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer' }}>
              Sign Out
            </button>
          </div>

          {/* Storage Dashboard */}
          <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#9CA3AF' }}>Storage Consumption</h3>
            {storage ? (
              <div>
                <p style={{ margin: '0.5rem 0', fontSize: '1.5rem', fontWeight: 'bold', color: 'white' }}>{formatBytes(storage.total_used_bytes)}</p>
                <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#D1D5DB', paddingBottom: '0.5rem', borderBottom: '1px solid #374151' }}>
                    <span>Videos & Audio</span>
                    <strong style={{ color: 'white' }}>{formatBytes(storage.videos_bytes)}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#D1D5DB' }}>
                    <span>Transcripts</span>
                    <strong style={{ color: 'white' }}>{formatBytes(storage.transcripts_bytes)}</strong>
                  </div>
                </div>
              </div>
            ) : <p>Loading storage...</p>}
          </div>
        </div>

        {/* Retention Center */}
        <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151', overflowY: 'auto', maxHeight: 'calc(100vh - 8rem)' }}>
          <h3 style={{ margin: '0 0 1.5rem 0', color: '#9CA3AF' }}>Retention Center</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {videos.length > 0 ? videos.map(v => {
              const expiresDate = new Date(new Date(v.created_at).getTime() + (v.retention_days * 86400000));
              // eslint-disable-next-line react-hooks/purity
              const daysLeft = Math.ceil((expiresDate.getTime() - Date.now()) / 86400000);
              const isUrgent = daysLeft <= 2;
              
              return (
                <div key={v.id} style={{ padding: '1rem', background: '#111827', borderRadius: '8px', borderLeft: `4px solid ${isUrgent ? '#EF4444' : '#10B981'}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ margin: '0 0 0.5rem 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '300px' }}>{v.title}</h4>
                    <span style={{ fontSize: '0.85rem', color: '#9CA3AF', background: '#374151', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
                      {v.source_type}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ textAlign: 'right' }}>
                      <p style={{ margin: '0 0 0.25rem 0', color: isUrgent ? '#EF4444' : '#E5E7EB', fontWeight: 'bold' }}>
                        Expires In: {daysLeft} Days
                      </p>
                      <p style={{ margin: 0, fontSize: '0.85rem', color: '#9CA3AF' }}>
                        {expiresDate.toLocaleDateString()}
                      </p>
                    </div>
                    <select
                      value={v.retention_days}
                      onChange={async (e) => {
                        const newDays = parseInt(e.target.value);
                        try {
                          const res = await fetch(`http://localhost:5001/videos/${v.id}/retention`, {
                            method: 'PATCH',
                            headers: { 
                              'Content-Type': 'application/json',
                              'Authorization': `Bearer ${token}` 
                            },
                            body: JSON.stringify({ retention_days: newDays })
                          });
                          if (res.ok) {
                             const updatedVideo = await res.json();
                             setVideos(prev => {
                               const newVideos = prev.map(vid => vid.id === updatedVideo.id ? updatedVideo : vid);
                               return newVideos.sort((a, b) => {
                                 const dateA = new Date(a.created_at).getTime() + (a.retention_days * 86400000);
                                 const dateB = new Date(b.created_at).getTime() + (b.retention_days * 86400000);
                                 return dateA - dateB;
                               });
                             });
                          }
                        } catch (err) {
                          console.error(err);
                        }
                      }}
                      style={{ background: '#374151', color: 'white', border: '1px solid #4B5563', borderRadius: '4px', padding: '0.5rem', cursor: 'pointer', outline: 'none' }}
                    >
                      <option value={7}>7 Days</option>
                      <option value={14}>14 Days</option>
                      <option value={30}>30 Days</option>
                    </select>
                  </div>
                </div>
              );
            }) : (
               <p style={{ color: '#9CA3AF' }}>No content in retention.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
