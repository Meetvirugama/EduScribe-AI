import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Video, Clock, Upload, Database, Languages, Zap, FileText, ChevronLeft, ScanText, PlayCircle } from 'lucide-react';

export default function ProjectWorkspace() {
  const { id } = useParams();
  const { token } = useAuth();
  const [details, setDetails] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [frames, setFrames] = useState([]);

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

    fetch(`http://localhost:5001/videos/${id}/frames?selected_only=false`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setFrames(data))
    .catch(err => console.error(err));
  }, [id, token]);

  if (!details) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'radial-gradient(circle at top left, #111827, #000000)', color: 'white' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
        <div style={{ width: '40px', height: '40px', border: '3px solid #374151', borderTopColor: '#3B82F6', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
        <p style={{ color: '#9CA3AF' }}>Loading Workspace...</p>
      </div>
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </div>
  );

  const { video, transcript_meta } = details;

  // Format title gracefully
  const cleanTitle = (video.title || '').replace(/\.[^/.]+$/, "").replace(/[-_]\d{4}-\d{2}-\d{2}.*/, "").replace(/-/g, " ");
  const displayTitle = cleanTitle.charAt(0).toUpperCase() + cleanTitle.slice(1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', boxSizing: 'border-box', background: 'radial-gradient(circle at top left, #171E2D, #0B0F19)', color: '#F3F4F6', margin: '-32px', padding: '2rem' }}>
      
      {/* Sleek Custom Scrollbar Style */}
      <style>{`
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
      `}</style>

      <header style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexShrink: 0 }}>
        <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#9CA3AF', textDecoration: 'none', transition: 'color 0.2s' }} onMouseEnter={e => e.target.style.color = 'white'} onMouseLeave={e => e.target.style.color = '#9CA3AF'}>
          <ChevronLeft size={20} /> Back to Library
        </Link>
        <h1 style={{ margin: 0, color: 'white', fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.025em' }}>{displayTitle}</h1>
      </header>

      <div style={{ display: 'flex', gap: '2rem', flex: 1, minHeight: 0 }}>
        
        {/* Left Column: Video & Metadata */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingRight: '0.5rem' }}>
          
          {/* Premium Metadata Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', flexShrink: 0 }}>
            
            <div style={{ display: 'flex', flexDirection: 'column', background: 'linear-gradient(135deg, rgba(31,41,55,0.7) 0%, rgba(17,24,39,0.9) 100%)', backdropFilter: 'blur(10px)', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <div style={{ background: 'rgba(59,130,246,0.1)', padding: '0.5rem', borderRadius: '8px', color: '#3B82F6' }}><Video size={20}/></div>
                <h3 style={{ margin: 0, color: 'white', fontWeight: '600' }}>Video Intelligence</h3>
              </div>
              <div style={{ display: 'grid', gap: '1rem', flex: 1, alignContent: 'start' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><PlayCircle size={16}/> Channel</span>
                  <strong style={{ color: 'white' }}>{video.channel_name || 'N/A'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Clock size={16}/> Duration</span>
                  <strong style={{ color: 'white' }}>{video.duration_seconds ? Math.round(video.duration_seconds/60) + ' mins' : 'Unknown'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Upload size={16}/> Source</span>
                  <span style={{ background: 'rgba(255,255,255,0.1)', padding: '0.1rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', color: '#E5E7EB' }}>{video.source_type}</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', background: 'linear-gradient(135deg, rgba(31,41,55,0.7) 0%, rgba(17,24,39,0.9) 100%)', backdropFilter: 'blur(10px)', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <div style={{ background: 'rgba(16,185,129,0.1)', padding: '0.5rem', borderRadius: '8px', color: '#10B981' }}><Database size={20}/></div>
                <h3 style={{ margin: 0, color: 'white', fontWeight: '600' }}>Processing Metadata</h3>
              </div>
              <div style={{ display: 'grid', gap: '1rem', flex: 1, alignContent: 'start' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><ScanText size={16}/> Transcript</span>
                  <span style={{ color: '#10B981', fontWeight: '500' }}>{transcript_meta.source === 'manual_upload' ? 'Manual Upload' : transcript_meta.source || 'Pending'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><FileText size={16}/> Words</span>
                  <strong style={{ color: 'white' }}>{transcript_meta.word_count ? transcript_meta.word_count.toLocaleString() : 0}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Zap size={16}/> Processing</span>
                  <strong style={{ color: '#F59E0B' }}>{video.processing_time_seconds || 0}s</strong>
                </div>
              </div>
            </div>

          </div>

          {/* Intelligent Key Frames Section */}
          <div style={{ background: 'rgba(31,41,55,0.4)', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', backdropFilter: 'blur(10px)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ background: 'rgba(139,92,246,0.1)', padding: '0.5rem', borderRadius: '8px', color: '#8B5CF6' }}><ScanText size={20}/></div>
                <h3 style={{ margin: 0, color: 'white', fontWeight: '600' }}>Key Frames Gallery</h3>
              </div>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <button 
                  onClick={async () => {
                    if (confirm('Extract frames for this video? This may take a minute.')) {
                      try {
                        const res = await fetch(`http://localhost:5001/videos/${id}/extract-frames`, {
                          method: 'POST',
                          headers: { 'Authorization': `Bearer ${token}` }
                        });
                        if (res.ok) {
                          alert('Frame extraction started! Check back in a few minutes.');
                        } else {
                          const err = await res.json();
                          alert('Error: ' + (err.detail || 'Failed to start extraction'));
                        }
                      } catch {
                        alert('Network error.');
                      }
                    }
                  }}
                  style={{ background: 'linear-gradient(to right, #4F46E5, #3B82F6)', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: '500', cursor: 'pointer', transition: 'opacity 0.2s', boxShadow: '0 4px 6px rgba(59,130,246,0.2)' }}
                  onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
                  onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                >
                  Extract Frames
                </button>
                <span style={{ fontSize: '0.85rem', color: '#D1D5DB', background: 'rgba(255,255,255,0.1)', padding: '0.4rem 0.8rem', borderRadius: '9999px', fontWeight: '500' }}>
                  {(frames && frames.length) || 0} Found
                </span>
              </div>
            </div>
            
            {(!frames || frames.length === 0) ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: '#9CA3AF', background: 'rgba(0,0,0,0.2)', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '12px' }}>
                <ScanText size={32} style={{ margin: '0 auto 1rem auto', opacity: 0.5 }}/>
                No key frames analyzed yet. Click "Extract Frames" to start the AI vision pipeline!
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '1rem', overflowX: 'auto', paddingBottom: '1rem' }}>
                {frames.map((frame) => (
                  <div key={frame.id} style={{ 
                      minWidth: '240px', 
                      background: 'rgba(17,24,39,0.8)', 
                      borderRadius: '12px', 
                      overflow: 'hidden', 
                      border: '1px solid rgba(255,255,255,0.05)', 
                      position: 'relative', 
                      transition: 'all 0.3s ease', 
                      cursor: 'pointer',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.2)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-6px)';
                      e.currentTarget.style.borderColor = 'rgba(59,130,246,0.5)';
                      e.currentTarget.style.boxShadow = '0 10px 15px rgba(0,0,0,0.3)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)';
                      e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.2)';
                    }}
                  >
                    <div style={{ position: 'relative', overflow: 'hidden', height: '140px' }}>
                      <img 
                        src={`http://localhost:5001/${frame.frame_path}`} 
                        alt={`Segment ${frame.scene_number}`} 
                        style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', transition: 'transform 0.5s ease' }} 
                        onMouseEnter={e => e.target.style.transform = 'scale(1.05)'}
                        onMouseLeave={e => e.target.style.transform = 'scale(1)'}
                        onError={(e) => { e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="240" height="140" fill="%23111827"><rect width="100%25" height="100%25"/></svg>' }}
                      />
                      
                      <div style={{ position: 'absolute', top: '8px', right: '8px', background: 'rgba(0,0,0,0.6)', color: '#93C5FD', padding: '4px 8px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '600', fontFamily: 'monospace', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.1)' }}>
                        {new Date((frame.timestamp_ms || 0)).toISOString().substr(14, 5)}
                      </div>
                      
                      {frame.score?.is_selected && (
                        <div style={{ position: 'absolute', top: '8px', left: '8px', background: 'linear-gradient(45deg, #10B981, #059669)', color: 'white', padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}>
                          ★ Top Pick
                        </div>
                      )}
                    </div>

                    <div style={{ padding: '1rem' }}>
                      <p style={{ margin: 0, fontSize: '0.9rem', color: '#F3F4F6', fontWeight: '500' }}>
                        Segment {frame.scene_number}
                      </p>
                      
                      {frame.ocr && frame.ocr.clean_text ? (
                        <div style={{ margin: '0.75rem 0 0 0', position: 'relative' }}>
                          <p style={{ margin: 0, fontSize: '0.75rem', color: '#9CA3AF', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', background: 'rgba(0,0,0,0.2)', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.02)' }} title={frame.ocr.clean_text}>
                            {frame.ocr.clean_text}
                          </p>
                        </div>
                      ) : (
                        <div style={{ margin: '0.75rem 0 0 0' }}>
                          <p style={{ margin: 0, fontSize: '0.75rem', color: '#4B5563', fontStyle: 'italic' }}>No text detected</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Transcript Explorer */}
        <div style={{ width: '420px', display: 'flex', flexDirection: 'column', background: 'rgba(31,41,55,0.4)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', overflow: 'hidden', backdropFilter: 'blur(10px)' }}>
          <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(17,24,39,0.8)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Languages size={20} color="#60A5FA"/>
            <h3 style={{ margin: 0, color: 'white', fontWeight: '600' }}>Transcript Explorer</h3>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', color: '#D1D5DB', lineHeight: '1.7', fontSize: '0.95rem' }}>
            {!transcript ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#6B7280' }}>
                Loading transcript...
              </div>
            ) : (
              <div>
                {(Array.isArray(transcript) ? transcript : transcript.segments)?.map((seg, i) => (
                  <div key={i} style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem', padding: '0.5rem', borderRadius: '8px', transition: 'background 0.2s' }} onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <span style={{ color: '#60A5FA', fontFamily: 'monospace', fontSize: '0.85rem', paddingTop: '0.2rem', flexShrink: 0 }}>
                      {new Date((seg.start || 0) * 1000).toISOString().substr(14, 5)}
                    </span>
                    <p style={{ margin: 0, color: '#E5E7EB' }}>{seg.text}</p>
                  </div>
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
