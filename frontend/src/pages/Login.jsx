import { API_BASE } from '../lib/api';

const Login = () => {
  const handleGoogleLogin = () => {
    // Navigate to backend auth endpoint
    window.location.href = `${API_BASE}/auth/google/login`;
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>EduScribe AI</h1>
        <p>Sign in to access your dashboard</p>
        <button onClick={handleGoogleLogin} className="btn-primary">
          Sign in with Google
        </button>
      </div>
    </div>
  );
};

export default Login;
