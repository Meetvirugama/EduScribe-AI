import os
import re

# We will just write out the complete new contents for Dashboard.jsx, Dashboard.css, ProjectWorkspace.jsx, ProjectWorkspace.css

DASHBOARD_CSS = """
.dashboard-container { padding: 2rem; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.btn-add-content { padding: 0.75rem 1.5rem; background: var(--accent); color: white; border: none; border-radius: 8px; cursor: pointer; }
.btn-add-content:hover { background: var(--accent-hover); }
.analytics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
.analytics-card { background: var(--bg-secondary); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border); }
.analytics-card h3 { margin: 0; color: var(--text-secondary); font-size: 0.875rem; }
.analytics-card p { margin: 0.5rem 0 0; font-size: 2rem; font-weight: bold; color: white; }
.video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
.video-card { padding: 1.5rem; background: var(--bg-secondary); border-radius: 12px; color: white; position: relative; }
.btn-delete { position: absolute; top: 10px; right: 10px; background: #EF4444; color: white; border: none; border-radius: 4px; cursor: pointer; padding: 0.25rem 0.5rem; }
.btn-delete:hover { background: #DC2626; }
.video-card h3 { margin-top: 0; padding-right: 40px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.video-card-type { color: var(--text-secondary); margin: 0.5rem 0; }
.progress-container { margin-top: 1rem; background: #374151; border-radius: 8px; padding: 1rem; }
.progress-text { display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 0.5rem; color: #D1D5DB; }
.progress-bar-bg { width: 100%; height: 8px; background: #4B5563; border-radius: 4px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: var(--accent); transition: width 0.5s ease-in-out; }
.progress-eta { margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-secondary); text-align: right; }
.video-card-status { color: var(--text-secondary); margin: 0.5rem 0; }
.video-error { margin-top: 0.5rem; padding: 0.75rem; background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; border-radius: 6px; }
.video-error p { color: #FCA5A5; margin: 0; font-size: 0.875rem; }
.btn-view-workspace { padding: 0.5rem 1rem; background: #10B981; color: white; border: none; border-radius: 6px; cursor: pointer; }
.btn-view-workspace:hover { background: #059669; }
.no-content { color: var(--text-secondary); }
"""

PW_CSS = """
.pw-container {
  display: flex; flex-direction: column; height: calc(100vh - 64px); box-sizing: border-box; background: radial-gradient(circle at top left, #171E2D, #0B0F19); color: #F3F4F6; margin: -32px; padding: 2rem;
}
.pw-container ::-webkit-scrollbar { width: 6px; height: 6px; }
.pw-container ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 4px; }
.pw-container ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
.pw-container ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

.pw-header { margin-bottom: 2rem; display: flex; align-items: center; gap: 1.5rem; flex-shrink: 0; }
.pw-back-link { display: flex; align-items: center; gap: 0.5rem; color: #9CA3AF; text-decoration: none; transition: color 0.2s; }
.pw-back-link:hover { color: white; }
.pw-title { margin: 0; color: white; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.025em; }

.pw-main-content { display: flex; gap: 2rem; flex: 1; min-height: 0; }
.pw-left-col { flex: 1; display: flex; flex-direction: column; gap: 1.5rem; overflow-y: auto; padding-right: 0.5rem; }
.pw-metadata-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; flex-shrink: 0; }
.pw-metadata-card { display: flex; flex-direction: column; background: linear-gradient(135deg, rgba(31,41,55,0.7) 0%, rgba(17,24,39,0.9) 100%); backdrop-filter: blur(10px); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
.pw-metadata-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; }
.pw-metadata-icon-blue { background: rgba(59,130,246,0.1); padding: 0.5rem; border-radius: 8px; color: #3B82F6; }
.pw-metadata-icon-green { background: rgba(16,185,129,0.1); padding: 0.5rem; border-radius: 8px; color: #10B981; }
.pw-metadata-header h3 { margin: 0; color: white; font-weight: 600; }
.pw-metadata-list { display: grid; gap: 1rem; flex: 1; align-content: start; }
.pw-metadata-item { display: flex; justify-content: space-between; align-items: center; }
.pw-metadata-label { color: #9CA3AF; display: flex; align-items: center; gap: 0.5rem; }
.pw-metadata-value { color: white; font-weight: bold; }
.pw-source-badge { background: rgba(255,255,255,0.1); padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.8rem; color: #E5E7EB; }

.pw-frames-section { background: rgba(31,41,55,0.4); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(10px); }
.pw-frames-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.pw-frames-title-wrap { display: flex; align-items: center; gap: 0.75rem; }
.pw-frames-icon { background: rgba(139,92,246,0.1); padding: 0.5rem; border-radius: 8px; color: #8B5CF6; }
.pw-frames-title-wrap h3 { margin: 0; color: white; font-weight: 600; }
.pw-frames-actions { display: flex; gap: 1rem; align-items: center; }
.pw-btn-extract { background: linear-gradient(to right, #4F46E5, #3B82F6); color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: opacity 0.2s; box-shadow: 0 4px 6px rgba(59,130,246,0.2); }
.pw-btn-extract:hover { opacity: 0.9; }
.pw-frames-count { font-size: 0.85rem; color: #D1D5DB; background: rgba(255,255,255,0.1); padding: 0.4rem 0.8rem; border-radius: 9999px; font-weight: 500; }
.pw-no-frames { padding: 3rem; text-align: center; color: #9CA3AF; background: rgba(0,0,0,0.2); border: 1px dashed rgba(255,255,255,0.1); border-radius: 12px; }
.pw-frames-gallery { display: flex; gap: 1rem; overflow-x: auto; padding-bottom: 1rem; }
.pw-frame-card { min-width: 240px; background: rgba(17,24,39,0.8); border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); position: relative; transition: all 0.3s ease; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
.pw-frame-card:hover { transform: translateY(-6px); border-color: rgba(59,130,246,0.5); box-shadow: 0 10px 15px rgba(0,0,0,0.3); }
.pw-frame-img-wrap { position: relative; overflow: hidden; height: 140px; }
.pw-frame-img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.5s ease; }
.pw-frame-card:hover .pw-frame-img { transform: scale(1.05); }
.pw-frame-time { position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.6); color: #93C5FD; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; font-family: monospace; backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.1); }
.pw-frame-top-pick { position: absolute; top: 8px; left: 8px; background: linear-gradient(45deg, #10B981, #059669); color: white; padding: 4px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; display: flex; align-items: center; gap: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
.pw-frame-details { padding: 1rem; }
.pw-frame-segment { margin: 0; font-size: 0.9rem; color: #F3F4F6; font-weight: 500; }
.pw-frame-ocr-wrap { margin: 0.75rem 0 0 0; position: relative; }
.pw-frame-ocr-text { margin: 0; font-size: 0.75rem; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: rgba(0,0,0,0.2); padding: 0.4rem 0.6rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.02); }
.pw-frame-no-ocr { margin: 0; font-size: 0.75rem; color: #4B5563; font-style: italic; }

.pw-right-col { width: 420px; display: flex; flex-direction: column; background: rgba(31,41,55,0.4); border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden; backdrop-filter: blur(10px); }
.pw-transcript-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(17,24,39,0.8); display: flex; align-items: center; gap: 0.75rem; }
.pw-transcript-header h3 { margin: 0; color: white; font-weight: 600; }
.pw-transcript-body { flex: 1; overflow-y: auto; padding: 1.5rem; color: #D1D5DB; line-height: 1.7; font-size: 0.95rem; }
.pw-transcript-loading { display: flex; justify-content: center; align-items: center; height: 100%; color: #6B7280; }
.pw-transcript-segment { display: flex; gap: 1rem; margin-bottom: 1.25rem; padding: 0.5rem; border-radius: 8px; transition: background 0.2s; }
.pw-transcript-segment:hover { background: rgba(255,255,255,0.03); }
.pw-transcript-time { color: #60A5FA; font-family: monospace; font-size: 0.85rem; padding-top: 0.2rem; flex-shrink: 0; }
.pw-transcript-text { margin: 0; color: #E5E7EB; }

/* Loadings */
.pw-loading-container { display: flex; justify-content: center; align-items: center; height: 100vh; background: radial-gradient(circle at top left, #111827, #000000); color: white; }
.pw-loading-wrap { display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.pw-spinner { width: 40px; height: 40px; border: 3px solid #374151; border-top-color: #3B82F6; border-radius: 50%; animation: spin 1s linear infinite; }
.pw-loading-text { color: #9CA3AF; }
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Error State */
.pw-error-state { display: flex; justify-content: center; align-items: center; height: 100vh; background: radial-gradient(circle at top left, #2f1010, #000000); color: #FCA5A5; font-size: 1.2rem; }
"""

import sys

with open('/Users/meetvirugama/Desktop/EduScribe-AI/frontend/src/pages/Dashboard.css', 'w') as f:
    f.write(DASHBOARD_CSS)
    
with open('/Users/meetvirugama/Desktop/EduScribe-AI/frontend/src/pages/ProjectWorkspace.css', 'w') as f:
    f.write(PW_CSS)

with open('/Users/meetvirugama/Desktop/EduScribe-AI/frontend/src/pages/Dashboard.jsx', 'r') as f:
    dashboard_js = f.read()

# Refactor Dashboard
dashboard_js = dashboard_js.replace("import UploadModal from '../components/UploadModal';", "import UploadModal from '../components/UploadModal';\nimport './Dashboard.css';")
dashboard_js = dashboard_js.replace("style={{ padding: '2rem' }}", "")
dashboard_js = dashboard_js.replace("style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}", "className=\"dashboard-header\"")
dashboard_js = dashboard_js.replace("style={{ padding: '0.75rem 1.5rem', background: '#4F46E5', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}", "className=\"btn-add-content\"")
dashboard_js = dashboard_js.replace("style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}", "className=\"analytics-grid\"")
dashboard_js = dashboard_js.replace("style={{ background: '#1F2937', padding: '1.5rem', borderRadius: '12px', border: '1px solid #374151' }}", "className=\"analytics-card\"")
dashboard_js = dashboard_js.replace("style={{ margin: 0, color: '#9CA3AF', fontSize: '0.875rem' }}", "")
dashboard_js = dashboard_js.replace("style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: 'white' }}", "")
dashboard_js = dashboard_js.replace("style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}", "")
dashboard_js = dashboard_js.replace("style={{ padding: '1.5rem', background: '#1F2937', borderRadius: '12px', color: 'white', position: 'relative' }}", "")
dashboard_js = dashboard_js.replace("style={{ position: 'absolute', top: '10px', right: '10px', background: '#EF4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', padding: '0.25rem 0.5rem' }}", "className=\"btn-delete\"")
dashboard_js = dashboard_js.replace("style={{ marginTop: 0, paddingRight: '40px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}", "")
dashboard_js = dashboard_js.replace("style={{ color: '#9CA3AF', margin: '0.5rem 0' }}", "className=\"video-card-type\"")
dashboard_js = dashboard_js.replace("style={{ marginTop: '1rem', background: '#374151', borderRadius: '8px', padding: '1rem' }}", "className=\"progress-container\"")
dashboard_js = dashboard_js.replace("style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.5rem', color: '#D1D5DB' }}", "className=\"progress-text\"")
dashboard_js = dashboard_js.replace("style={{ width: '100%', height: '8px', background: '#4B5563', borderRadius: '4px', overflow: 'hidden' }}", "className=\"progress-bar-bg\"")
dashboard_js = dashboard_js.replace("style={{ width: `${v.progress_percent || 0}%`, height: '100%', background: '#4F46E5', transition: 'width 0.5s ease-in-out' }}", "className=\"progress-bar-fill\" style={{ width: `${v.progress_percent || 0}%` }}")
dashboard_js = dashboard_js.replace("style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#9CA3AF', textAlign: 'right' }}", "className=\"progress-eta\"")
dashboard_js = dashboard_js.replace("Status: <strong>{v.status}</strong></p>", "Status: <strong>{v.status}</strong></p>").replace("style={{ color: '#9CA3AF', margin: '0.5rem 0' }}>Status:", "className=\"video-card-status\">Status:")
dashboard_js = dashboard_js.replace("style={{ marginTop: '0.5rem', padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #EF4444', borderRadius: '6px' }}", "className=\"video-error\"")
dashboard_js = dashboard_js.replace("style={{ color: '#FCA5A5', margin: 0, fontSize: '0.875rem' }}", "")
dashboard_js = dashboard_js.replace("style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}", "className=\"video-actions\"")
dashboard_js = dashboard_js.replace("style={{ padding: '0.5rem 1rem', background: '#10B981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}", "className=\"btn-view-workspace\"")
dashboard_js = dashboard_js.replace("style={{ color: '#9CA3AF' }}", "className=\"no-content\"")

with open('/Users/meetvirugama/Desktop/EduScribe-AI/frontend/src/pages/Dashboard.jsx', 'w') as f:
    f.write(dashboard_js)


with open('/Users/meetvirugama/Desktop/EduScribe-AI/frontend/src/pages/ProjectWorkspace.jsx', 'r') as f:
    pw_js = f.read()
    
# Refactor ProjectWorkspace
pw_js = pw_js.replace("import { Video, Clock, Upload, Database, Languages, Zap, FileText, ChevronLeft, ScanText, PlayCircle } from 'lucide-react';", "import { Video, Clock, Upload, Database, Languages, Zap, FileText, ChevronLeft, ScanText, PlayCircle } from 'lucide-react';\nimport './ProjectWorkspace.css';")
pw_js = pw_js.replace("const [frames, setFrames] = useState([]);", "const [frames, setFrames] = useState([]);\n  const [error, setError] = useState(null);")
pw_js = pw_js.replace(".catch(err => console.error(err));", ".catch(err => { console.error(err); setError('Failed to load workspace data.'); });")

pw_js = pw_js.replace("if (!details) return (", "if (error) return <div className=\"pw-error-state\">{error}</div>;\n  if (!details) return (")
pw_js = pw_js.replace("style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'radial-gradient(circle at top left, #111827, #000000)', color: 'white' }}", "className=\"pw-loading-container\"")
pw_js = pw_js.replace("style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}", "className=\"pw-loading-wrap\"")
pw_js = pw_js.replace("style={{ width: '40px', height: '40px', border: '3px solid #374151', borderTopColor: '#3B82F6', borderRadius: '50%', animation: 'spin 1s linear infinite' }}", "className=\"pw-spinner\"")
pw_js = pw_js.replace("style={{ color: '#9CA3AF' }}", "className=\"pw-loading-text\"")
pw_js = pw_js.replace("<style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>", "")

pw_js = pw_js.replace("style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', boxSizing: 'border-box', background: 'radial-gradient(circle at top left, #171E2D, #0B0F19)', color: '#F3F4F6', margin: '-32px', padding: '2rem' }}", "className=\"pw-container\"")
pw_js = pw_js.replace("<style>{`\n        ::-webkit-scrollbar { width: 6px; height: 6px; }\n        ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 4px; }\n        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }\n        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }\n      `}</style>", "")

pw_js = pw_js.replace("style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexShrink: 0 }}", "className=\"pw-header\"")
pw_js = pw_js.replace("style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#9CA3AF', textDecoration: 'none', transition: 'color 0.2s' }} onMouseEnter={e => e.target.style.color = 'white'} onMouseLeave={e => e.target.style.color = '#9CA3AF'}", "className=\"pw-back-link\"")
pw_js = pw_js.replace("style={{ margin: 0, color: 'white', fontSize: '1.75rem', fontWeight: '700', letterSpacing: '-0.025em' }}", "className=\"pw-title\"")
pw_js = pw_js.replace("style={{ display: 'flex', gap: '2rem', flex: 1, minHeight: 0 }}", "className=\"pw-main-content\"")
pw_js = pw_js.replace("style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingRight: '0.5rem' }}", "className=\"pw-left-col\"")
pw_js = pw_js.replace("style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', flexShrink: 0 }}", "className=\"pw-metadata-grid\"")
pw_js = pw_js.replace("style={{ display: 'flex', flexDirection: 'column', background: 'linear-gradient(135deg, rgba(31,41,55,0.7) 0%, rgba(17,24,39,0.9) 100%)', backdropFilter: 'blur(10px)', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}", "className=\"pw-metadata-card\"")
pw_js = pw_js.replace("style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}", "className=\"pw-metadata-header\"")
pw_js = pw_js.replace("style={{ background: 'rgba(59,130,246,0.1)', padding: '0.5rem', borderRadius: '8px', color: '#3B82F6' }}", "className=\"pw-metadata-icon-blue\"")
pw_js = pw_js.replace("style={{ margin: 0, color: 'white', fontWeight: '600' }}", "")
pw_js = pw_js.replace("style={{ display: 'grid', gap: '1rem', flex: 1, alignContent: 'start' }}", "className=\"pw-metadata-list\"")
pw_js = pw_js.replace("style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}", "className=\"pw-metadata-item\"")
pw_js = pw_js.replace("style={{ color: '#9CA3AF', display: 'flex', alignItems: 'center', gap: '0.5rem' }}", "className=\"pw-metadata-label\"")
pw_js = pw_js.replace("style={{ color: 'white' }}", "className=\"pw-metadata-value\"")
pw_js = pw_js.replace("style={{ background: 'rgba(255,255,255,0.1)', padding: '0.1rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', color: '#E5E7EB' }}", "className=\"pw-source-badge\"")
pw_js = pw_js.replace("style={{ background: 'rgba(16,185,129,0.1)', padding: '0.5rem', borderRadius: '8px', color: '#10B981' }}", "className=\"pw-metadata-icon-green\"")

pw_js = pw_js.replace("style={{ background: 'rgba(31,41,55,0.4)', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', backdropFilter: 'blur(10px)' }}", "className=\"pw-frames-section\"")
pw_js = pw_js.replace("style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}", "className=\"pw-frames-header\"")
pw_js = pw_js.replace("style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}", "className=\"pw-frames-title-wrap\"")
pw_js = pw_js.replace("style={{ background: 'rgba(139,92,246,0.1)', padding: '0.5rem', borderRadius: '8px', color: '#8B5CF6' }}", "className=\"pw-frames-icon\"")
pw_js = pw_js.replace("style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}", "className=\"pw-frames-actions\"")
pw_js = pw_js.replace("style={{ background: 'linear-gradient(to right, #4F46E5, #3B82F6)', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: '500', cursor: 'pointer', transition: 'opacity 0.2s', boxShadow: '0 4px 6px rgba(59,130,246,0.2)' }}\n                  onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}\n                  onMouseLeave={e => e.currentTarget.style.opacity = '1'}", "className=\"pw-btn-extract\"")
pw_js = pw_js.replace("style={{ fontSize: '0.85rem', color: '#D1D5DB', background: 'rgba(255,255,255,0.1)', padding: '0.4rem 0.8rem', borderRadius: '9999px', fontWeight: '500' }}", "className=\"pw-frames-count\"")
pw_js = pw_js.replace("style={{ padding: '3rem', textAlign: 'center', color: '#9CA3AF', background: 'rgba(0,0,0,0.2)', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '12px' }}", "className=\"pw-no-frames\"")
pw_js = pw_js.replace("style={{ margin: '0 auto 1rem auto', opacity: 0.5 }}", "")
pw_js = pw_js.replace("style={{ display: 'flex', gap: '1rem', overflowX: 'auto', paddingBottom: '1rem' }}", "className=\"pw-frames-gallery\"")
pw_js = pw_js.replace("style={{ \n                      minWidth: '240px', \n                      background: 'rgba(17,24,39,0.8)', \n                      borderRadius: '12px', \n                      overflow: 'hidden', \n                      border: '1px solid rgba(255,255,255,0.05)', \n                      position: 'relative', \n                      transition: 'all 0.3s ease', \n                      cursor: 'pointer',\n                      boxShadow: '0 4px 6px rgba(0,0,0,0.2)'\n                    }}\n                    onMouseEnter={(e) => {\n                      e.currentTarget.style.transform = 'translateY(-6px)';\n                      e.currentTarget.style.borderColor = 'rgba(59,130,246,0.5)';\n                      e.currentTarget.style.boxShadow = '0 10px 15px rgba(0,0,0,0.3)';\n                    }}\n                    onMouseLeave={(e) => {\n                      e.currentTarget.style.transform = 'translateY(0)';\n                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)';\n                      e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.2)';\n                    }}", "className=\"pw-frame-card\"")
pw_js = pw_js.replace("style={{ position: 'relative', overflow: 'hidden', height: '140px' }}", "className=\"pw-frame-img-wrap\"")
pw_js = pw_js.replace("style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', transition: 'transform 0.5s ease' }} \n                        onMouseEnter={e => e.target.style.transform = 'scale(1.05)'}\n                        onMouseLeave={e => e.target.style.transform = 'scale(1)'}", "className=\"pw-frame-img\"")
pw_js = pw_js.replace("style={{ position: 'absolute', top: '8px', right: '8px', background: 'rgba(0,0,0,0.6)', color: '#93C5FD', padding: '4px 8px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: '600', fontFamily: 'monospace', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.1)' }}", "className=\"pw-frame-time\"")
pw_js = pw_js.replace("style={{ position: 'absolute', top: '8px', left: '8px', background: 'linear-gradient(45deg, #10B981, #059669)', color: 'white', padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}", "className=\"pw-frame-top-pick\"")
pw_js = pw_js.replace("style={{ padding: '1rem' }}", "className=\"pw-frame-details\"")
pw_js = pw_js.replace("style={{ margin: 0, fontSize: '0.9rem', color: '#F3F4F6', fontWeight: '500' }}", "className=\"pw-frame-segment\"")
pw_js = pw_js.replace("style={{ margin: '0.75rem 0 0 0', position: 'relative' }}", "className=\"pw-frame-ocr-wrap\"")
pw_js = pw_js.replace("style={{ margin: 0, fontSize: '0.75rem', color: '#9CA3AF', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', background: 'rgba(0,0,0,0.2)', padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.02)' }}", "className=\"pw-frame-ocr-text\"")
pw_js = pw_js.replace("style={{ margin: '0.75rem 0 0 0' }}", "className=\"pw-frame-ocr-wrap\"")
pw_js = pw_js.replace("style={{ margin: 0, fontSize: '0.75rem', color: '#4B5563', fontStyle: 'italic' }}", "className=\"pw-frame-no-ocr\"")

pw_js = pw_js.replace("style={{ width: '420px', display: 'flex', flexDirection: 'column', background: 'rgba(31,41,55,0.4)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', overflow: 'hidden', backdropFilter: 'blur(10px)' }}", "className=\"pw-right-col\"")
pw_js = pw_js.replace("style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(17,24,39,0.8)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}", "className=\"pw-transcript-header\"")
pw_js = pw_js.replace("style={{ flex: 1, overflow-y: 'auto', padding: '1.5rem', color: '#D1D5DB', lineHeight: '1.7', fontSize: '0.95rem' }}", "className=\"pw-transcript-body\"")
pw_js = pw_js.replace("style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#6B7280' }}", "className=\"pw-transcript-loading\"")
pw_js = pw_js.replace("style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem', padding: '0.5rem', borderRadius: '8px', transition: 'background 0.2s' }} onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}", "className=\"pw-transcript-segment\"")
pw_js = pw_js.replace("style={{ color: '#60A5FA', fontFamily: 'monospace', fontSize: '0.85rem', paddingTop: '0.2rem', flexShrink: 0 }}", "className=\"pw-transcript-time\"")
pw_js = pw_js.replace("style={{ margin: 0, color: '#E5E7EB' }}", "className=\"pw-transcript-text\"")

with open('/Users/meetvirugama/Desktop/EduScribe-AI/frontend/src/pages/ProjectWorkspace.jsx', 'w') as f:
    f.write(pw_js)

