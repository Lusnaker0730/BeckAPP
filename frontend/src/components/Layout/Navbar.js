import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

const Navbar = ({ user, onLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  const navItems = [
    { path: '/dashboard', label: '儀錶板', icon: '📊' },
    { path: '/diagnosis-analysis', label: '診斷分析', icon: '🏥' },
    { path: '/cohort', label: '群組分析', icon: '👥' },
    { path: '/survival-analysis', label: '存活分析', icon: '🔬' },
    { path: '/data-quality', label: '數據質量', icon: '✅' },
    { path: '/visualization', label: '數據視覺化', icon: '📈' },
    { path: '/export', label: '資料匯出', icon: '💾' },
  ];

  if (user?.role === 'admin' || user?.role === 'engineer') {
    navItems.push({ path: '/admin', label: '後端管理', icon: '⚙️' });
  }
  
  // 審計日誌僅對管理員可見
  if (user?.role === 'admin') {
    navItems.push({ path: '/audit-logs', label: '審計日誌', icon: '🔐' });
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/dashboard">
            <span className="brand-icon">🏥</span>
            <span className="brand-text">FHIR Analytics</span>
          </Link>
        </div>

        <button 
          className="mobile-menu-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <div className={`navbar-menu ${mobileMenuOpen ? 'open' : ''}`}>
          <ul className="navbar-nav">
            {navItems.map((item) => (
              <li key={item.path} className={isActive(item.path)}>
                <Link to={item.path} onClick={() => setMobileMenuOpen(false)}>
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>

          <div className="navbar-user">
            <div className="user-info">
              <span className="user-name">{user?.name || 'User'}</span>
              <span className="user-role">{user?.role || 'User'}</span>
            </div>
            <button onClick={onLogout} className="logout-btn">
              登出
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

