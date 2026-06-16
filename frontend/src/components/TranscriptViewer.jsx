import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function TranscriptViewer({ video, onClose }) {
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    fetch(`http://localhost:5001/videos/${video.id}/transcript`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setTranscript(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [video.id, token]);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '2rem' }}>
      <div style={{ background: '#1F2937', padding: '2rem', borderRadius: '12px', width: '100%', maxWidth: '800px', maxHeight: '80vh', display: 'flex', flexDirection: 'column', color: 'white' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>Transcript: {video.title}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9CA3AF', cursor: 'pointer', fontSize: '1.5rem' }}>×</button>
        </div>

        {video.source_type === 'YOUTUBE' && video.youtube_url && (
          <div style={{ marginBottom: '1.5rem' }}>
            <iframe 
              width="100%" 
              height="315" 
              src={`https://www.youtube.com/embed/${video.youtube_url.split('v=')[1]?.split('&')[0]}`} 
              frameBorder="0" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowFullScreen 
              style={{ borderRadius: '8px' }}
            />
          </div>
        )}

        {video.source_type === 'UPLOAD' && video.video_path && (
          <div style={{ marginBottom: '1.5rem' }}>
            {video.video_path.match(/\.(mp3|wav|m4a)$/i) ? (
              <audio controls style={{ width: '100%' }}>
                <source src={`http://localhost:5001/${video.video_path}`} />
              </audio>
            ) : (
              <video controls style={{ width: '100%', maxHeight: '315px', background: 'black', borderRadius: '8px' }}>
                <source src={`http://localhost:5001/${video.video_path}`} />
              </video>
            )}
          </div>
        )}
        
        <div style={{ flex: 1, overflowY: 'auto', background: '#111827', padding: '1.5rem', borderRadius: '8px', lineHeight: '1.6' }}>
          {loading ? (
            <p>Loading transcript...</p>
          ) : transcript ? (
            <div>
              {(Array.isArray(transcript) ? transcript : transcript.segments)?.map((seg, i) => (
                <p key={i} style={{ marginBottom: '1rem' }}>
                  <span style={{ color: '#60A5FA', marginRight: '0.5rem' }}>
                    [{new Date((seg.start || 0) * 1000).toISOString().substr(14, 5)}]
                  </span>
                  {seg.text}
                </p>
              ))}
              {!Array.isArray(transcript) && !transcript.segments && <p>{transcript.text}</p>}
            </div>
          ) : (
            <p>Failed to load transcript.</p>
          )}
        </div>
      </div>
    </div>
  );
}
