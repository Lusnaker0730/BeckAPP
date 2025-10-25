import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import Login from './components/Auth/Login';
import SmartLaunch from './components/Auth/SmartLaunch';
import Dashboard from './components/Dashboard/Dashboard';
import DiagnosisAnalysis from './components/Analysis/DiagnosisAnalysis';
import DataVisualization from './components/Visualization/DataVisualization';
import DataExport from './components/Export/DataExport';
import AdminPanel from './components/Admin/AdminPanel';
import Navbar from './components/Layout/Navbar';
import PrivateRoute from './components/Auth/PrivateRoute';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing authentication
    const token = localStorage.getItem('accessToken');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setIsAuthenticated(true);
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData, token) => {
    localStorage.setItem('accessToken', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    localStorage.removeItem('fhirClient');
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="App">
        {isAuthenticated && <Navbar user={user} onLogout={handleLogout} />}
        <div className="app-content">
          <Routes>
            <Route 
              path="/login" 
              element={
                isAuthenticated ? 
                <Navigate to="/dashboard" /> : 
                <Login onLogin={handleLogin} />
              } 
            />
            <Route 
              path="/smart-launch" 
              element={<SmartLaunch onLogin={handleLogin} />} 
            />
            <Route 
              path="/dashboard" 
              element={
                <PrivateRoute isAuthenticated={isAuthenticated}>
                  <Dashboard />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/diagnosis-analysis" 
              element={
                <PrivateRoute isAuthenticated={isAuthenticated}>
                  <DiagnosisAnalysis />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/visualization" 
              element={
                <PrivateRoute isAuthenticated={isAuthenticated}>
                  <DataVisualization />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/export" 
              element={
                <PrivateRoute isAuthenticated={isAuthenticated}>
                  <DataExport />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/admin" 
              element={
                <PrivateRoute isAuthenticated={isAuthenticated}>
                  <AdminPanel />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/" 
              element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} 
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;

