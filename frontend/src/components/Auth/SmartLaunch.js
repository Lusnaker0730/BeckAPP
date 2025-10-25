import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FHIR from 'fhirclient';
import './Auth.css';

const SmartLaunch = ({ onLogin }) => {
  const [status, setStatus] = useState('initializing');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const initializeSmart = async () => {
      try {
        setStatus('authorizing');
        
        // Check if we're returning from authorization
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('code') || urlParams.has('state')) {
          setStatus('completing');
          
          // Complete the authorization process
          const client = await FHIR.oauth2.ready();
          
          // Get patient and user info
          const patient = await client.patient.read();
          const user = await client.user.read();
          
          // Store FHIR client context
          localStorage.setItem('fhirClient', JSON.stringify({
            patient: patient,
            user: user,
            tokenResponse: client.state.tokenResponse
          }));

          // Create user object
          const userData = {
            id: user.id,
            name: user.name?.[0]?.text || 'FHIR User',
            role: 'clinician',
            fhirEnabled: true
          };

          // Login with FHIR token
          onLogin(userData, client.state.tokenResponse.access_token);
          navigate('/dashboard');
        } else {
          // Start the authorization process
          await FHIR.oauth2.authorize({
            clientId: process.env.REACT_APP_FHIR_CLIENT_ID,
            scope: process.env.REACT_APP_FHIR_SCOPE || 
                   'patient/*.read launch/patient openid fhirUser',
            redirectUri: process.env.REACT_APP_FHIR_REDIRECT_URI || 
                        window.location.origin + '/smart-launch',
            iss: urlParams.get('iss') // FHIR server URL from EHR launch
          });
        }
      } catch (err) {
        console.error('SMART on FHIR Error:', err);
        setError(err.message || 'SMART on FHIR 認證失敗');
        setStatus('error');
      }
    };

    initializeSmart();
  }, [onLogin, navigate]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>SMART on FHIR Launch</h1>
        </div>

        <div className="smart-status">
          {status === 'initializing' && (
            <>
              <div className="spinner"></div>
              <p>初始化 SMART on FHIR...</p>
            </>
          )}
          
          {status === 'authorizing' && (
            <>
              <div className="spinner"></div>
              <p>正在連接 EHR 系統...</p>
              <p className="text-secondary">請在彈出視窗中完成授權</p>
            </>
          )}
          
          {status === 'completing' && (
            <>
              <div className="spinner"></div>
              <p>完成授權中...</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="alert error">
                <strong>錯誤：</strong> {error}
              </div>
              <button 
                onClick={() => navigate('/login')}
                className="primary"
              >
                返回登入頁面
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SmartLaunch;

