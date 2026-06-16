import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProjectWorkspace() {
  const { id } = useParams();
  const { token } = useAuth();
  const [details, setDetails] = useState(null);
  const [transcript, setTranscript] = useState(null);

  useEffect(() => {
    if (!token) return;
    
    fetch(`http://localhost:5001/videos/${id}/details`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setDetails(data))
    .catch(err => console.error(err));

    fetch(`http://localhost:5001/videos/${id}/transcript`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setTranscript(data))
    .catch(err => console.error(err));
  }, [id, token]);

  if (!details) return <div style={{ padding: '2rem', color: 'white' }}>Loading Workspace...</div>;

  const { video, transcript_meta } = details;

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', height: '100vh', boxSizing: 'border-box' }}>
      <header style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Link to="/dashboard" style={{ color: '#9CA3AF', textDecoration: 'none' }}>← Back to Library</Link>
        <h1 style={{ margin: 0, color: 'white' }}>{video.title}</h1>
      </header>

      <div style={{ display: 'flex', gap: '2rem', flex: 1, minHeight: 0 }}>
        {/* Left Column: Video & Metadata */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingRight: '1rem' }}>
          {/* Video Player */}
          <div style={{ background: 'black', borderRadius: '12px', overflow: 'hidden' }}>
            {video.source_type === 'YOUTUBE' && video.youtube_url ? (
              <iframe 
                width="100%" 
                height="400" 
                src={`https://www.youtube.com/embed/${
                  video.youtube_url.includes('youtu.be/') 
                    ? video.youtube_url.split('youtu.be/')[1].split('?')[0] 
                    : video.youtube_url.split('v=')[1]?.split('&')[0]
                }`} 
                frameBorder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowFullScreen 
              />
            ) : video.video_path ? (
              video.video_path.match(/\.(mp3|wav|m4a)$/i) ? (
                <div style={{ padding: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <audio controls style={{ width: '100%' }}>
                      <source src={`http://localhost:5001/${video.video_path}`} />
                    </audio>
                </div>
              ) : (
                <video controls style={{ width: '100%', maxHeight: '400px' }}>
                  <source src={`http://localhost:5001/${video.video_path}`} />
                </video>
              )
            ) : null}
          </div>

          {/* Metadata Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151', color: 'white' }}>
              <h3 style={{ margin: '0 0 1rem 0', color: '#E5E7EB' }}>Video Intelligence</h3>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Channel: <strong style={{ color: 'white' }}>{video.channel_name || 'N/A'}</strong></p>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Duration: <strong style={{ color: 'white' }}>{video.duration_seconds ? Math.round(video.duration_seconds/60) + ' mins' : 'Unknown'}</strong></p>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Source: <strong style={{ color: 'white' }}>{video.source_type}</strong></p>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Uploaded: <strong style={{ color: 'white' }}>{new Date(video.created_at).toLocaleDateString()}</strong></p>
            </div>

            <div style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151', color: 'white' }}>
              <h3 style={{ margin: '0 0 1rem 0', color: '#E5E7EB' }}>Processing Metadata</h3>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Transcript Source: <strong style={{ color: '#10B981' }}>{transcript_meta.source || 'Pending'}</strong></p>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Word Count: <strong style={{ color: 'white' }}>{transcript_meta.word_count ? transcript_meta.word_count.toLocaleString() : 0}</strong></p>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Language: <strong style={{ color: 'white' }}>{transcript_meta.language || 'en'}</strong></p>
              <p style={{ margin: '0.5rem 0', color: '#9CA3AF' }}>Processing Time: <strong style={{ color: 'white' }}>{video.processing_time_seconds || 0}s</strong></p>
            </div>
          </div>
        </div>

        {/* Right Column: Transcript */}
        <div style={{ width: '400px', display: 'flex', flexDirection: 'column', background: '#1F2937', borderRadius: '12px', border: '1px solid #374151', overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem', borderBottom: '1px solid #374151', background: '#111827' }}>
            <h3 style={{ margin: 0, color: 'white' }}>Transcript Explorer</h3>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', color: '#D1D5DB', lineHeight: '1.6' }}>
            {!transcript ? (
              <p>Loading transcript...</p>
            ) : (
              <div>
                {(Array.isArray(transcript) ? transcript : transcript.segments)?.map((seg, i) => (
                  <p key={i} style={{ marginBottom: '1.25rem' }}>
                    <span style={{ color: '#60A5FA', marginRight: '0.5rem', fontFamily: 'monospace' }}>
                      [{new Date((seg.start || 0) * 1000).toISOString().substr(14, 5)}]
                    </span>
                    {seg.text}
                  </p>
                ))}
                {!Array.isArray(transcript) && !transcript.segments && <p>{transcript.text}</p>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
