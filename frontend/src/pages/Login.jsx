import { useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { API_BASE } from '../lib/api';
import './Login.css';

const FEATURES = [
  { icon: '🎙️', title: 'Auto-Transcription', desc: 'Whisper-powered speech-to-text in any language' },
  { icon: '🖼️', title: 'Key Frame Extraction', desc: 'AI vision pipeline picks the best slides & visuals' },
  { icon: '📝', title: 'Smart Notes', desc: 'LLM-authored study notes, quizzes & flashcards' },
  { icon: '🔍', title: 'Semantic Search', desc: 'RAG-powered search across all your notes instantly' },
];

export default function Login() {
  const [searchParams] = useSearchParams();
  const authError = searchParams.get('error');
  const canvasRef = useRef(null);

  const handleGoogleLogin = () => {
    window.location.href = `${API_BASE}/auth/google/login`;
  };

  // Animated particle background
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const particles = Array.from({ length: 60 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5 + 0.5,
      dx: (Math.random() - 0.5) * 0.4,
      dy: (Math.random() - 0.5) * 0.4,
      alpha: Math.random() * 0.5 + 0.1,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(99,102,241,${p.alpha})`;
        ctx.fill();
        p.x += p.dx;
        p.y += p.dy;
        if (p.x < 0 || p.x > canvas.width) p.dx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
      });

      // Draw connecting lines between nearby particles
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(99,102,241,${0.08 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <div className="login-root">
      <canvas ref={canvasRef} className="login-canvas" />

      <div className="login-layout">
        {/* Left — Branding & Features */}
        <div className="login-left">
          <div className="login-brand">
            <div className="login-logo">
              <span>🎓</span>
            </div>
            <div>
              <h1 className="login-brand-name">EduScribe <span className="login-brand-ai">AI</span></h1>
              <p className="login-brand-tagline">Transform lectures into mastery</p>
            </div>
          </div>

          <p className="login-hero-text">
            Drop a video or paste a YouTube link — get structured study notes, key frames, flashcards, and semantic search in minutes.
          </p>

          <div className="login-features">
            {FEATURES.map(f => (
              <div key={f.title} className="login-feature-card">
                <span className="login-feature-icon">{f.icon}</span>
                <div>
                  <h3 className="login-feature-title">{f.title}</h3>
                  <p className="login-feature-desc">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Sign-in Card */}
        <div className="login-right">
          <div className="login-card-glass">
            <div className="login-card-top">
              <h2 className="login-card-title">Welcome back</h2>
              <p className="login-card-subtitle">Sign in to access your learning library</p>
            </div>

            {authError && (
              <div className="login-error-banner">
                <span>⚠️</span>
                <span>Authentication failed. Please try again.</span>
              </div>
            )}

            <button
              id="google-signin-btn"
              onClick={handleGoogleLogin}
              className="login-google-btn"
            >
              <svg width="20" height="20" viewBox="0 0 48 48" fill="none">
                <path d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z" fill="#FFC107"/>
                <path d="M6.3 14.7l7 5.1C15.1 16 19.2 13 24 13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 16.3 2 9.7 7.4 6.3 14.7z" fill="#FF3D00"/>
                <path d="M24 46c5.5 0 10.5-1.8 14.4-5L31.7 35c-2.2 1.5-5 2.4-7.7 2.4-6 0-11.1-4-12.9-9.5L4 33.5C7.4 40.5 15.1 46 24 46z" fill="#4CAF50"/>
                <path d="M44.5 20H24v8.5h11.8c-.8 2.5-2.4 4.6-4.5 6l6.7 6c3.9-3.6 6-9 6-16.5 0-1.3-.2-2.7-.5-4z" fill="#1976D2"/>
              </svg>
              <span>Continue with Google</span>
            </button>

            <div className="login-divider">
              <span />
              <p>Secure OAuth2 — we never store your password</p>
              <span />
            </div>

            <div className="login-trust-row">
              <div className="login-trust-item"><span>🔒</span> JWT secured</div>
              <div className="login-trust-item"><span>🗑️</span> Auto-expiring data</div>
              <div className="login-trust-item"><span>⚡</span> Real-time pipeline</div>
            </div>
          </div>

          <p className="login-footer-note">
            By signing in, you agree to our data retention policy. All content is automatically deleted after your chosen retention period.
          </p>
        </div>
      </div>
    </div>
  );
}
