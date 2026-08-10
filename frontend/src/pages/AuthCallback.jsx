import { useEffect } from 'react';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE } from '../lib/api';

/**
 * AuthCallback — handles the OAuth redirect from the backend.
 *
 * CRITICAL-004 fix: The backend (ISSUE-03 / auth.py) was updated to redirect to
 * /auth/callback?code=<one-time-code> instead of /auth/callback#token=<jwt>.
 * The old implementation read window.location.hash which was always empty,
 * causing every login attempt to bounce back to /login.
 *
 * New flow:
 *   1. Read ?code= from the query string.
 *   2. POST it to /auth/exchange.
 *   3. Receive the JWT in the JSON response body.
 *   4. Call login(access_token) and navigate to /dashboard.
 */
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();

  useEffect(() => {
    const code = searchParams.get('code');

    if (!code) {
      // No code in the query string — redirect to login with an error indicator.
      navigate('/login?error=auth_failed', { replace: true });
      return;
    }

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/exchange`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code }),
        });

        if (!res.ok) {
          throw new Error(`Exchange failed: ${res.status}`);
        }

        const data = await res.json();
        const token = data.access_token;

        if (token) {
          login(token);
          navigate('/dashboard', { replace: true });
        } else {
          throw new Error('No access_token in exchange response');
        }
      } catch (err) {
        console.error('AuthCallback: token exchange failed', err);
        navigate('/login?error=auth_failed', { replace: true });
      }
    })();
  }, [location, login, navigate, searchParams]);

  return (
    <div className="auth-callback">
      <p>Authenticating...</p>
    </div>
  );
};

export default AuthCallback;
