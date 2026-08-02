import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Video, Clock, Upload, Database, Languages, Zap, FileText, ChevronLeft, ScanText, PlayCircle } from 'lucide-react';
import './ProjectWorkspace.css';

export default function ProjectWorkspace() {
  const { id } = useParams();
  const { token } = useAuth();
  const [details, setDetails] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [frames, setFrames] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) return;
    
    Promise.all([
      fetch(`http://localhost:5001/videos/${id}/details`, { headers: { 'Authorization': `Bearer ${token}` } }).then(res => res.json()),
      fetch(`http://localhost:5001/videos/${id}/transcript`, { headers: { 'Authorization': `Bearer ${token}` } }).then(res => res.json()),
      fetch(`http://localhost:5001/videos/${id}/frames?selected_only=false`, { headers: { 'Authorization': `Bearer ${token}` } }).then(res => res.json())
    ])
    .then(([detailsData, transcriptData, framesData]) => {
      setDetails(detailsData);
      setTranscript(transcriptData);
      setFrames(framesData);
    })
    .catch(err => { console.error(err); setError('Failed to load workspace data.'); });
  }, [id, token]);

  if (error) return <div className="pw-error-state">{error}</div>;
  if (!details) return (
    <div className="pw-loading-container">
      <div className="pw-loading-wrap">
        <div className="pw-spinner"></div>
        <p className="pw-loading-text">Loading Workspace...</p>
      </div>
      
    </div>
  );

  const { video, transcript_meta } = details;

  // Format title gracefully
  const cleanTitle = (video.title || '').replace(/\.[^/.]+$/, "").replace(/[-_]\d{4}-\d{2}-\d{2}.*/, "").replace(/-/g, " ");
  const displayTitle = cleanTitle.charAt(0).toUpperCase() + cleanTitle.slice(1);

  return (
    <div className="pw-container">
      
      {/* Sleek Custom Scrollbar Style */}
      

      <header className="pw-header">
        <Link to="/dashboard" className="pw-back-link">
          <ChevronLeft size={20} /> Back to Library
        </Link>
        <h1 className="pw-title">{displayTitle}</h1>
      </header>

      <div className="pw-main-content">
        
        {/* Left Column: Video & Metadata */}
        <div className="pw-left-col">
          
          {/* Premium Metadata Cards */}
          <div className="pw-metadata-grid">
            
            <div className="pw-metadata-card">
              <div className="pw-metadata-header">
                <div className="pw-metadata-icon-blue"><Video size={20}/></div>
                <h3 >Video Intelligence</h3>
              </div>
              <div className="pw-metadata-list">
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><PlayCircle size={16}/> Channel</span>
                  <strong className="pw-metadata-value">{video.channel_name || 'N/A'}</strong>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><Clock size={16}/> Duration</span>
                  <strong className="pw-metadata-value">{video.duration_seconds ? Math.round(video.duration_seconds/60) + ' mins' : 'Unknown'}</strong>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><Upload size={16}/> Source</span>
                  <span className="pw-source-badge">{video.source_type}</span>
                </div>
              </div>
            </div>

            <div className="pw-metadata-card">
              <div className="pw-metadata-header">
                <div className="pw-metadata-icon-green"><Database size={20}/></div>
                <h3 >Processing Metadata</h3>
              </div>
              <div className="pw-metadata-list">
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><ScanText size={16}/> Transcript</span>
                  <span style={{ color: '#10B981', fontWeight: '500' }}>{transcript_meta.source === 'manual_upload' ? 'Manual Upload' : transcript_meta.source || 'Pending'}</span>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><FileText size={16}/> Words</span>
                  <strong className="pw-metadata-value">{transcript_meta.word_count ? transcript_meta.word_count.toLocaleString() : 0}</strong>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><Zap size={16}/> Processing</span>
                  <strong style={{ color: '#F59E0B' }}>{video.processing_time_seconds || 0}s</strong>
                </div>
              </div>
            </div>

          </div>

          {/* Intelligent Key Frames Section */}
          <div className="pw-frames-section">
            <div className="pw-frames-header">
              <div className="pw-frames-title-wrap">
                <div className="pw-frames-icon"><ScanText size={20}/></div>
                <h3 >Key Frames Gallery</h3>
              </div>
              <div className="pw-frames-actions">
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
                  className="pw-btn-extract"
                >
                  Extract Frames
                </button>
                <span className="pw-frames-count">
                  {(frames && frames.length) || 0} Found
                </span>
              </div>
            </div>
            
            {(!frames || frames.length === 0) ? (
              <div className="pw-no-frames">
                <ScanText size={32} />
                No key frames analyzed yet. Click "Extract Frames" to start the AI vision pipeline!
              </div>
            ) : (
              <div className="pw-frames-gallery">
                {frames.map((frame) => (
                  <div key={frame.id} className="pw-frame-card"
                  >
                    <div className="pw-frame-img-wrap">
                      <img 
                        src={`http://localhost:5001/${frame.frame_path}`} 
                        alt={`Segment ${frame.scene_number}`} 
                        className="pw-frame-img"
                        onError={(e) => { e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="240" height="140" fill="%23111827"><rect width="100%25" height="100%25"/></svg>' }}
                      />
                      
                      <div className="pw-frame-time">
                        {new Date((frame.timestamp_ms || 0)).toISOString().substr(14, 5)}
                      </div>
                      
                      {frame.score?.is_selected && (
                        <div className="pw-frame-top-pick">
                          ★ Top Pick
                        </div>
                      )}
                    </div>

                    <div className="pw-frame-details">
                      <p className="pw-frame-segment">
                        Segment {frame.scene_number}
                      </p>
                      
                      {frame.ocr && frame.ocr.clean_text ? (
                        <div className="pw-frame-ocr-wrap">
                          <p className="pw-frame-ocr-text" title={frame.ocr.clean_text}>
                            {frame.ocr.clean_text}
                          </p>
                        </div>
                      ) : (
                        <div className="pw-frame-ocr-wrap">
                          <p className="pw-frame-no-ocr">No text detected</p>
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
        <div className="pw-right-col">
          <div className="pw-transcript-header">
            <Languages size={20} color="#60A5FA"/>
            <h3 >Transcript Explorer</h3>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', color: '#D1D5DB', lineHeight: '1.7', fontSize: '0.95rem' }}>
            {!transcript ? (
              <div className="pw-transcript-loading">
                Loading transcript...
              </div>
            ) : (
              <div>
                {(Array.isArray(transcript) ? transcript : transcript.segments)?.map((seg, i) => (
                  <div key={i} className="pw-transcript-segment">
                    <span className="pw-transcript-time">
                      {new Date((seg.start || 0) * 1000).toISOString().substr(14, 5)}
                    </span>
                    <p className="pw-transcript-text">{seg.text}</p>
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
