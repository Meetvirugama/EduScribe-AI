import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiFetch, API_BASE } from '../lib/api';
import {
  Video, Clock, Upload, Database, Languages, Zap, FileText,
  ChevronLeft, ScanText, PlayCircle, BookOpen, Search,
  Download, Trash2, X, BookMarked, Lightbulb, Map, FileSpreadsheet, MessagesSquare, CheckSquare, Presentation
} from 'lucide-react';
import { useVirtualizer } from '@tanstack/react-virtual';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ConfirmModal from '../components/ConfirmModal';
import './ProjectWorkspace.css';

const ARTIFACT_TYPES = {
  detailed_notes: { label: 'Detailed Notes', icon: BookOpen },
  quiz: { label: 'Quiz', icon: CheckSquare },
  flashcards: { label: 'Flashcards', icon: Presentation },
  mindmap: { label: 'Mindmap', icon: Map },
  formula_sheet: { label: 'Formula Sheet', icon: FileSpreadsheet },
  interview: { label: 'Interview Prep', icon: MessagesSquare },
  revision: { label: 'Revision Sheet', icon: Lightbulb },
};

/**
 * VirtualTranscript — renders only visible transcript segments (perf).
 */
function VirtualTranscript({ transcript }) {
  const parentRef = useRef(null);
  const segments = Array.isArray(transcript) ? transcript : transcript?.segments ?? [];

  const rowVirtualizer = useVirtualizer({
    count: segments.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72,
    overscan: 10,
  });

  if (!transcript) return <div className="pw-transcript-loading">Loading transcript…</div>;
  if (segments.length === 0) return (
    <p style={{ padding: '1.5rem', color: '#9CA3AF' }}>No transcript segments found.</p>
  );

  return (
    <div ref={parentRef} style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', color: '#D1D5DB', lineHeight: '1.7', fontSize: '0.95rem' }}>
      <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const seg = segments[virtualRow.index];
          return (
            <div
              key={virtualRow.index}
              style={{ position: 'absolute', top: 0, left: 0, width: '100%', transform: `translateY(${virtualRow.start}px)` }}
            >
              <div className="pw-transcript-segment">
                <span className="pw-transcript-time">
                  {new Date((seg.start || 0) * 1000).toISOString().substr(14, 5)}
                </span>
                <p className="pw-transcript-text">{seg.text}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


export default function ProjectWorkspace() {
  const { id } = useParams();
  const { token } = useAuth();
  const [details, setDetails] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [frames, setFrames] = useState([]);
  
  // Artifacts state
  const [artifacts, setArtifacts] = useState([]);
  const [activeTab, setActiveTab] = useState('detailed_notes'); // default artifact or transcript
  
  const [error, setError] = useState(null);
  const [generatingArtifact, setGeneratingArtifact] = useState(false);

  const fetchArtifacts = useCallback(async () => {
    try {
      const res = await apiFetch(`/generate/${id}/artifacts`, {}, token);
      if (res.ok) {
        const data = await res.json();
        setArtifacts(data.artifacts || []);
      }
    } catch (err) {
      console.error('Failed to fetch artifacts', err);
    }
  }, [id, token]);

  useEffect(() => {
    if (!token) return;

    Promise.all([
      apiFetch(`/videos/${id}/details`, {}, token).then(r => r.json()),
      apiFetch(`/videos/${id}/transcript`, {}, token).then(r => r.ok ? r.json() : null),
      apiFetch(`/videos/${id}/frames?selected_only=false`, {}, token).then(r => r.ok ? r.json() : []),
    ])
      .then(([detailsData, transcriptData, framesData]) => {
        setDetails(detailsData);
        setTranscript(transcriptData);
        setFrames(Array.isArray(framesData) ? framesData : []);
      })
      .catch(err => { console.error(err); setError('Failed to load workspace data.'); });
      
    fetchArtifacts();
  }, [id, token, fetchArtifacts]);

  // Polling for artifact generation progress
  useEffect(() => {
    const isGenerating = artifacts.some(a => a.status === 'PENDING' || a.status === 'GENERATING');
    if (!isGenerating) return;

    const timer = setInterval(() => {
      fetchArtifacts();
    }, 5000);

    return () => clearInterval(timer);
  }, [artifacts, fetchArtifacts]);

  const handleGenerate = async (artifactType) => {
    setGeneratingArtifact(true);
    try {
      const res = await apiFetch(`/generate/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ artifacts: [artifactType] })
      }, token);
      
      if (res.ok) {
        await fetchArtifacts();
        setActiveTab(artifactType);
      } else {
        const err = await res.json();
        alert(`Failed to generate: ${err.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error(err);
      alert('Network error while generating artifact.');
    } finally {
      setGeneratingArtifact(false);
    }
  };

  if (error) return <div className="pw-error-state">{error}</div>;
  if (!details) return (
    <div className="pw-loading-container">
      <div className="pw-loading-wrap">
        <div className="pw-spinner" />
        <p className="pw-loading-text">Loading Workspace…</p>
      </div>
    </div>
  );

  const { video, transcript_meta } = details;
  const rawTitle = (video.title || '').replace(/\.[^/.]+$/, '').replace(/[-_]\d{4}-\d{2}-\d{2}.*/, '').replace(/-/g, ' ');
  const displayTitle = rawTitle.charAt(0).toUpperCase() + rawTitle.slice(1);

  // Helper to get active artifact data
  const getActiveArtifact = () => {
    return artifacts.find(a => a.artifact_type === activeTab);
  };
  const activeArtifact = getActiveArtifact();

  return (
    <div className="pw-container">
      <header className="pw-header">
        <Link to="/dashboard" className="pw-back-link">
          <ChevronLeft size={20} /> Back to Library
        </Link>
        <h1 className="pw-title">{displayTitle}</h1>
      </header>

      <div className="pw-main-content">
        {/* ── Left Column ── */}
        <div className="pw-left-col">

          {/* Metadata Cards */}
          <div className="pw-metadata-grid">
            <div className="pw-metadata-card">
              <div className="pw-metadata-header">
                <div className="pw-metadata-icon-blue"><Video size={20} /></div>
                <h3>Video Intelligence</h3>
              </div>
              <div className="pw-metadata-list">
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><PlayCircle size={16} /> Channel</span>
                  <strong className="pw-metadata-value">{video.channel_name || 'N/A'}</strong>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><Clock size={16} /> Duration</span>
                  <strong className="pw-metadata-value">
                    {video.duration_seconds ? Math.round(video.duration_seconds / 60) + ' mins' : 'Unknown'}
                  </strong>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><Upload size={16} /> Source</span>
                  <span className="pw-source-badge">{video.source_type}</span>
                </div>
              </div>
            </div>

            <div className="pw-metadata-card">
              <div className="pw-metadata-header">
                <div className="pw-metadata-icon-green"><Database size={20} /></div>
                <h3>Processing Metadata</h3>
              </div>
              <div className="pw-metadata-list">
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><ScanText size={16} /> Transcript</span>
                  <span style={{ color: '#10B981', fontWeight: 500 }}>
                    {transcript_meta.source === 'manual_upload' ? 'Manual Upload' : transcript_meta.source || 'Pending'}
                  </span>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><FileText size={16} /> Words</span>
                  <strong className="pw-metadata-value">
                    {transcript_meta.word_count ? transcript_meta.word_count.toLocaleString() : 0}
                  </strong>
                </div>
                <div className="pw-metadata-item">
                  <span className="pw-metadata-label"><Zap size={16} /> Processing</span>
                  <strong style={{ color: '#F59E0B' }}>{video.processing_time_seconds || 0}s</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Key Frames Gallery */}
          <div className="pw-frames-section">
            <div className="pw-frames-header">
              <div className="pw-frames-title-wrap">
                <div className="pw-frames-icon"><ScanText size={20} /></div>
                <h3>Key Frames Gallery</h3>
              </div>
            </div>

            {frames.length === 0 ? (
              <div className="pw-no-frames">
                <ScanText size={32} />
                <p>No key frames analyzed for this video.</p>
              </div>
            ) : (
              <div className="pw-frames-gallery">
                {frames.map((frame) => (
                  <div key={frame.id} className="pw-frame-card">
                    <div className="pw-frame-img-wrap">
                      <img
                        src={`${API_BASE}/videos/${id}/frames/${frame.id}/image?token=${token}`}
                        alt={`Segment ${frame.scene_number}`}
                        className="pw-frame-img"
                        onError={(e) => {
                          e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="240" height="140" fill="%23111827"><rect width="100%" height="100%"/></svg>';
                        }}
                      />
                      <div className="pw-frame-time">
                        {new Date(frame.timestamp_ms || 0).toISOString().substr(14, 5)}
                      </div>
                      {frame.score?.is_selected && (
                        <div className="pw-frame-top-pick">★ Top Pick</div>
                      )}
                    </div>
                    <div className="pw-frame-details">
                      <p className="pw-frame-segment">Segment {frame.scene_number}</p>
                      <div className="pw-frame-ocr-wrap">
                        {frame.ocr?.clean_text ? (
                          <p className="pw-frame-ocr-text" title={frame.ocr.clean_text}>{frame.ocr.clean_text}</p>
                        ) : (
                          <p className="pw-frame-no-ocr">No text detected</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Right Column ── */}
        <div className="pw-right-col">
          {/* Tabs */}
          <div className="pw-transcript-header">
            <div className="pw-tabs" style={{ flexWrap: 'wrap', gap: '0.5rem' }}>
              <button
                className={`pw-tab-btn ${activeTab === 'transcript' ? 'active' : ''}`}
                onClick={() => setActiveTab('transcript')}
              >
                <Languages size={16} /> Transcript
              </button>
              
              {/* Artifact Tabs */}
              {Object.entries(ARTIFACT_TYPES).map(([type, config]) => {
                const Icon = config.icon;
                const artifact = artifacts.find(a => a.artifact_type === type);
                
                return (
                  <button
                    key={type}
                    className={`pw-tab-btn ${activeTab === type ? 'active' : ''}`}
                    onClick={() => setActiveTab(type)}
                  >
                    <Icon size={16} /> {config.label}
                    {artifact && (
                      <span className={`status-indicator status-${artifact.status.toLowerCase()}`} title={artifact.status} />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pw-right-content">
            {activeTab === 'transcript' ? (
              transcript
                ? <VirtualTranscript transcript={transcript} />
                : <div className="pw-transcript-loading">
                    <BookMarked size={32} style={{ opacity: 0.3 }} />
                    <p>Transcript not available yet.</p>
                  </div>
            ) : (
              // Artifact Viewer
              <div className="pw-markdown-container">
                {!activeArtifact ? (
                  <div className="pw-empty-artifact">
                    <div style={{ textAlign: 'center', margin: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                      <p>This artifact hasn't been generated yet.</p>
                      <button 
                        className="pw-btn-extract" 
                        onClick={() => handleGenerate(activeTab)}
                        disabled={generatingArtifact}
                      >
                        {generatingArtifact ? 'Starting...' : `Generate ${ARTIFACT_TYPES[activeTab].label}`}
                      </button>
                    </div>
                  </div>
                ) : activeArtifact.status === 'PENDING' || activeArtifact.status === 'GENERATING' ? (
                  <div className="pw-transcript-loading" style={{ flexDirection: 'column', gap: '0.75rem' }}>
                    <div className="pw-spinner" />
                    <p>Generating {ARTIFACT_TYPES[activeTab].label}...</p>
                  </div>
                ) : activeArtifact.status === 'FAILED' ? (
                  <div className="pw-transcript-loading" style={{ flexDirection: 'column', gap: '0.75rem' }}>
                    <Trash2 size={32} style={{ opacity: 0.3 }} />
                    <p>Failed to generate {ARTIFACT_TYPES[activeTab].label}.</p>
                    <p style={{ fontSize: '0.8rem', color: '#ef4444' }}>{activeArtifact.error_message}</p>
                    <button 
                      className="pw-btn-extract" 
                      onClick={() => handleGenerate(activeTab)}
                    >
                      Retry
                    </button>
                  </div>
                ) : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      img: ({ node, ...props }) => {
                        let src = props.src;
                        if (src?.startsWith('/storage/')) src = `${API_BASE}${src}`;
                        return <img {...props} src={src} style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '1rem', border: '1px solid rgba(255,255,255,0.1)' }} />;
                      },
                    }}
                  >
                    {typeof activeArtifact.content === 'string' ? activeArtifact.content : JSON.stringify(activeArtifact.content, null, 2)}
                  </ReactMarkdown>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
