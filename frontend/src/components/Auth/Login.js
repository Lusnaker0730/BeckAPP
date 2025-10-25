import React, { useState } from 'react';
import axios from 'axios'; // Use default axios for login (no auth needed)
import './Auth.css';

const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/auth/login`,
        credentials
      );
      
      const { access_token, user } = response.data;
      onLogin(user, access_token);
    } catch (err) {
      setError(err.response?.data?.detail || '登入失敗，請檢查帳號密碼');
    } finally {
      setLoading(false);
    }
  };

  const handleSmartLaunch = () => {
    window.location.href = '/smart-launch';
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>FHIR Analytics Platform</h1>
          <p>醫療公衛分析平台</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="alert error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">使用者名稱</label>
            <input
              type="text"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              placeholder="請輸入使用者名稱"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">密碼</label>
            <input
              type="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              placeholder="請輸入密碼"
              required
            />
          </div>

          <button 
            type="submit" 
            className="primary full-width"
            disabled={loading}
          >
            {loading ? '登入中...' : '登入'}
          </button>
        </form>

        <div className="auth-divider">
          <span>或</span>
        </div>

        <button 
          onClick={handleSmartLaunch}
          className="outline full-width smart-launch-btn"
        >
          <span className="smart-icon">🏥</span>
          使用 SMART on FHIR 登入
        </button>

        <div className="auth-footer">
          <p>連接您的 EHR 系統進行安全登入</p>
        </div>
      </div>
    </div>
  );
};

export default Login;

