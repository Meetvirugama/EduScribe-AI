import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../lib/api';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
  { name: 'Settings', path: '/settings', icon: <Settings size={20} /> },
];

const Sidebar = () => {
  const location = useLocation();
  const { logout, token } = useAuth();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    if (!token) return;
    apiFetch('/auth/me', {}, token)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setProfile(data); })
      .catch(() => {});
  }, [token]);

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="sidebar-logo-icon">🎓</span>
          <h2>EduScribe</h2>
        </div>
      </div>

      <nav className="sidebar-nav">
        <ul>
          {navItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={`nav-link ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
              >
                {item.icon}
                <span>{item.name}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        {/* User Avatar */}
        {profile && (
          <div className="sidebar-user">
            {profile.picture
              ? <img src={profile.picture} alt="Avatar" className="sidebar-user-avatar" />
              : <div className="sidebar-user-avatar sidebar-user-avatar--placeholder">
                  {(profile.name || '?')[0].toUpperCase()}
                </div>
            }
            <div className="sidebar-user-info">
              <p className="sidebar-user-name">{profile.name}</p>
              <p className="sidebar-user-email">{profile.email}</p>
            </div>
          </div>
        )}

        <button
          id="sidebar-logout-btn"
          onClick={logout}
          className="nav-link sidebar-logout-btn"
        >
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
