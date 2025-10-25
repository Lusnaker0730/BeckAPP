import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import './Admin.css';

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('bulk-data');
  const [bulkDataConfig, setBulkDataConfig] = useState({
    fhirServerUrl: '',
    resourceTypes: ['Patient', 'Condition', 'Encounter', 'Observation'],
    since: '',
  });
  const [etlJobs, setEtlJobs] = useState([]);
  const [valuesets, setValuesets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobDetails, setJobDetails] = useState(null);
  const [showLogModal, setShowLogModal] = useState(false);

  useEffect(() => {
    fetchEtlJobs();
    fetchValuesets();
    
    // Auto-refresh ETL jobs every 5 seconds when on ETL jobs tab
    const interval = setInterval(() => {
      if (activeTab === 'etl-jobs') {
        fetchEtlJobs();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchEtlJobs = async () => {
    try {
      const response = await axios.get('/api/admin/etl-jobs');
      setEtlJobs(response.data);
    } catch (error) {
      console.error('Error fetching ETL jobs:', error);
    }
  };

  const fetchValuesets = async () => {
    try {
      const response = await axios.get('/api/admin/valuesets');
      setValuesets(response.data);
    } catch (error) {
      console.error('Error fetching valuesets:', error);
    }
  };

  const deleteValueset = async (valuesetId) => {
    try {
      await axios.delete(`/api/admin/valuesets/${valuesetId}`);
      alert('Valueset 刪除成功');
      fetchValuesets();  // Reload list
    } catch (error) {
      console.error('Error deleting valueset:', error);
      alert('刪除失敗: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteJob = async (jobId) => {
    try {
      await axios.delete(`/api/admin/etl-jobs/${jobId}`);
      alert('任務刪除成功');
      fetchEtlJobs();  // Reload list
    } catch (error) {
      console.error('Error deleting job:', error);
      alert('刪除失敗: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleBulkDataFetch = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/admin/bulk-data/fetch', bulkDataConfig);
      alert(`BULK DATA 提取任務已啟動\nJob ID: ${response.data.job_id}`);
      fetchEtlJobs();
    } catch (error) {
      console.error('Error starting bulk data fetch:', error);
      const errorMsg = error.response?.data?.detail || '啟動失敗';
      alert(`啟動失敗: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const viewJobLog = async (jobId) => {
    try {
      const response = await axios.get(`/api/admin/etl-jobs/${jobId}/status`);
      setJobDetails(response.data);
      setSelectedJob(jobId);
      setShowLogModal(true);
    } catch (error) {
      console.error('Error fetching job details:', error);
      alert('無法獲取任務詳情');
    }
  };

  const closeLogModal = () => {
    setShowLogModal(false);
    setSelectedJob(null);
    setJobDetails(null);
  };

  const tabs = [
    { id: 'bulk-data', label: 'BULK DATA API', icon: '📥' },
    { id: 'etl-jobs', label: 'ETL 任務', icon: '⚙️' },
    { id: 'valuesets', label: 'Valuesets 管理', icon: '📚' },
    { id: 'api-config', label: 'API 配置', icon: '🔧' },
  ];

  return (
    <div className="container">
      <div className="page-header">
        <h1>後端管理面板</h1>
        <p>工程師專用 - 管理 FHIR 數據處理流程</p>
      </div>

      {/* Tabs */}
      <div className="admin-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="icon">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* BULK DATA Tab */}
        {activeTab === 'bulk-data' && (
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>FHIR BULK DATA API 配置</h3>
            
            <div className="form-group">
              <label className="form-label">FHIR 伺服器 URL</label>
              <input
                type="url"
                value={bulkDataConfig.fhirServerUrl}
                onChange={(e) => setBulkDataConfig({...bulkDataConfig, fhirServerUrl: e.target.value})}
                placeholder="https://hapi.fhir.org/baseR4"
              />
            </div>

            <div className="form-group">
              <label className="form-label">資源類型</label>
              <div className="resource-types">
                {['Patient', 'Condition', 'Encounter', 'Observation', 'Procedure', 'Medication'].map(type => (
                  <label key={type} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={bulkDataConfig.resourceTypes.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setBulkDataConfig({
                            ...bulkDataConfig,
                            resourceTypes: [...bulkDataConfig.resourceTypes, type]
                          });
                        } else {
                          setBulkDataConfig({
                            ...bulkDataConfig,
                            resourceTypes: bulkDataConfig.resourceTypes.filter(t => t !== type)
                          });
                        }
                      }}
                    />
                    <span>{type}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">從此日期開始 (Since)</label>
              <input
                type="datetime-local"
                value={bulkDataConfig.since}
                onChange={(e) => setBulkDataConfig({...bulkDataConfig, since: e.target.value})}
              />
            </div>

            <button 
              onClick={handleBulkDataFetch}
              className="primary"
              disabled={loading}
            >
              {loading ? '啟動中...' : '啟動 BULK DATA 提取'}
            </button>
          </div>
        )}

        {/* ETL Jobs Tab */}
        {activeTab === 'etl-jobs' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>ETL 任務列表</h3>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  onClick={() => {
                    const failedJobs = etlJobs.filter(j => j.status === 'failed' || j.status === 'timeout');
                    if (failedJobs.length === 0) {
                      alert('沒有失敗的任務需要刪除');
                      return;
                    }
                    if (window.confirm(`確定要刪除 ${failedJobs.length} 個失敗的任務嗎？`)) {
                      failedJobs.forEach(job => deleteJob(job.id));
                    }
                  }} 
                  className="outline"
                  style={{ color: '#dc2626' }}
                  disabled={!etlJobs.some(j => j.status === 'failed' || j.status === 'timeout')}
                >
                  🗑️ 刪除失敗任務 ({etlJobs.filter(j => j.status === 'failed' || j.status === 'timeout').length})
                </button>
                <button onClick={fetchEtlJobs} className="outline">
                  🔄 刷新
                </button>
              </div>
            </div>
            
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>任務 ID</th>
                    <th>資源類型</th>
                    <th>狀態</th>
                    <th>開始時間</th>
                    <th>處理記錄數</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {etlJobs.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        暫無 ETL 任務
                      </td>
                    </tr>
                  ) : (
                    etlJobs.map((job) => (
                      <tr key={job.id}>
                        <td>{job.id}</td>
                        <td>{job.resourceType}</td>
                        <td>
                          <span className={`badge ${
                            job.status === 'completed' ? 'success' :
                            job.status === 'running' ? 'warning' : 'danger'
                          }`}>
                            {job.status}
                          </span>
                        </td>
                        <td>{new Date(job.startTime).toLocaleString('zh-TW')}</td>
                        <td>{job.recordsProcessed?.toLocaleString() || 0}</td>
                        <td>
                          <button 
                            className="outline" 
                            style={{ padding: '4px 8px', fontSize: '12px', marginRight: '8px' }}
                            onClick={() => viewJobLog(job.id)}
                          >
                            📋 查看詳情
                          </button>
                          <button 
                            className="outline" 
                            style={{ 
                              padding: '4px 8px', 
                              fontSize: '12px', 
                              color: (job.status === 'failed' || job.status === 'timeout') ? '#dc2626' : '#6b7280'
                            }}
                            onClick={() => {
                              if (window.confirm(`確定要刪除任務 "${job.id}" 嗎？\n\n此操作無法復原。`)) {
                                deleteJob(job.id);
                              }
                            }}
                          >
                            🗑️ 刪除
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Valuesets Tab */}
        {activeTab === 'valuesets' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>Valuesets 管理 (SNOMED-CT & ICD-10)</h3>
              <button className="primary" onClick={() => alert('新增 Valueset 功能開發中')}>
                新增 Valueset
              </button>
            </div>
            
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>名稱</th>
                    <th>代碼系統</th>
                    <th>代碼數量</th>
                    <th>最後更新</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {valuesets.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center' }}>沒有 Valueset</td>
                    </tr>
                  ) : (
                    valuesets.map(vs => (
                      <tr key={vs.id}>
                        <td>{vs.name}</td>
                        <td>{vs.code_system}</td>
                        <td>{vs.code_count}</td>
                        <td>{vs.updated_at ? new Date(vs.updated_at).toLocaleDateString('zh-TW') : 'N/A'}</td>
                        <td>
                          <button 
                            className="outline" 
                            style={{ padding: '4px 8px', fontSize: '12px', marginRight: '8px' }}
                            onClick={() => alert(`Valueset: ${vs.name} (ID: ${vs.id})\n${vs.description}\n\n代碼數量: ${vs.code_count}`)}
                          >
                            查看詳情
                          </button>
                          <button 
                            className="outline" 
                            style={{ padding: '4px 8px', fontSize: '12px' }}
                            onClick={() => {
                              if (window.confirm(`確定要刪除 "${vs.name}" 嗎？`)) {
                                deleteValueset(vs.id);
                              }
                            }}
                          >
                            刪除
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* API Config Tab */}
        {activeTab === 'api-config' && (
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>API 端點配置</h3>
            
            <div className="alert info">
              <strong>當前 API 狀態：</strong> 運行中 ✓
            </div>

            <div className="api-endpoints">
              <div className="endpoint-item">
                <span className="method get">GET</span>
                <span className="path">/api/analytics/stats</span>
                <span className="badge success">啟用</span>
              </div>
              <div className="endpoint-item">
                <span className="method get">GET</span>
                <span className="path">/api/analytics/diagnosis</span>
                <span className="badge success">啟用</span>
              </div>
              <div className="endpoint-item">
                <span className="method post">POST</span>
                <span className="path">/api/export</span>
                <span className="badge success">啟用</span>
              </div>
              <div className="endpoint-item">
                <span className="method post">POST</span>
                <span className="path">/api/admin/bulk-data/fetch</span>
                <span className="badge success">啟用</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Job Log Modal */}
      {showLogModal && jobDetails && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            maxWidth: '800px',
            maxHeight: '80vh',
            overflow: 'auto',
            width: '90%'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>任務詳情</h3>
              <button onClick={closeLogModal} style={{ fontSize: '24px', border: 'none', background: 'none', cursor: 'pointer' }}>×</button>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#2563eb' }}>📋 基本信息</h4>
              <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', marginBottom: '15px' }}>
                <p style={{ margin: '8px 0' }}><strong>任務 ID:</strong> <code style={{ backgroundColor: '#e9ecef', padding: '2px 6px', borderRadius: '3px' }}>{jobDetails.job_id}</code></p>
                <p style={{ margin: '8px 0' }}><strong>資源類型:</strong> {jobDetails.resource_type}</p>
                <p style={{ margin: '8px 0' }}><strong>狀態:</strong> <span style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  backgroundColor: 
                    jobDetails.status === 'completed' ? '#d4edda' :
                    jobDetails.status === 'in-progress' ? '#fff3cd' :
                    jobDetails.status === 'failed' ? '#f8d7da' : '#e2e3e5',
                  color:
                    jobDetails.status === 'completed' ? '#155724' :
                    jobDetails.status === 'in-progress' ? '#856404' :
                    jobDetails.status === 'failed' ? '#721c24' : '#383d41'
                }}>{jobDetails.status}</span></p>
              </div>

              <h4 style={{ marginTop: '20px', marginBottom: '15px', color: '#2563eb' }}>⏱️ 時間信息</h4>
              <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', marginBottom: '15px' }}>
                <p style={{ margin: '8px 0' }}><strong>開始時間:</strong> {jobDetails.start_time ? new Date(jobDetails.start_time).toLocaleString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'N/A'}</p>
                <p style={{ margin: '8px 0' }}><strong>結束時間:</strong> {jobDetails.end_time ? new Date(jobDetails.end_time).toLocaleString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '尚未完成'}</p>
                {jobDetails.start_time && jobDetails.end_time && (
                  <p style={{ margin: '8px 0' }}><strong>執行時長:</strong> {Math.round((new Date(jobDetails.end_time) - new Date(jobDetails.start_time)) / 1000)} 秒</p>
                )}
              </div>

              <h4 style={{ marginTop: '20px', marginBottom: '15px', color: '#2563eb' }}>📊 數據統計</h4>
              <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', marginBottom: '15px' }}>
                <p style={{ margin: '8px 0' }}><strong>處理記錄數:</strong> <span style={{ color: '#28a745', fontWeight: 'bold', fontSize: '18px' }}>{jobDetails.records_processed?.toLocaleString() || 0}</span></p>
                <p style={{ margin: '8px 0' }}><strong>失敗記錄數:</strong> <span style={{ color: '#dc3545', fontWeight: 'bold', fontSize: '18px' }}>{jobDetails.records_failed?.toLocaleString() || 0}</span></p>
              </div>

              {jobDetails.fhir_server_url && (
                <>
                  <h4 style={{ marginTop: '20px', marginBottom: '15px', color: '#2563eb' }}>🌐 數據源信息</h4>
                  <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', marginBottom: '15px' }}>
                    <p style={{ margin: '8px 0' }}><strong>FHIR 服務器:</strong></p>
                    <code style={{ backgroundColor: '#e9ecef', padding: '8px', borderRadius: '3px', display: 'block', fontSize: '11px', wordBreak: 'break-all' }}>{jobDetails.fhir_server_url}</code>
                  </div>
                </>
              )}
            </div>

            {jobDetails.error_log && (
              <div style={{ marginTop: '20px' }}>
                <h4>詳細日誌</h4>
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '15px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '300px',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word'
                }}>
                  {typeof jobDetails.error_log === 'string' 
                    ? (() => {
                        try {
                          const parsed = JSON.parse(jobDetails.error_log);
                          return JSON.stringify(parsed, null, 2);
                        } catch {
                          return jobDetails.error_log;
                        }
                      })()
                    : JSON.stringify(jobDetails.error_log, null, 2)
                  }
                </pre>
              </div>
            )}

            {jobDetails.result && (
              <div style={{ marginTop: '20px' }}>
                <h4>任務結果</h4>
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '15px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '300px',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word'
                }}>
                  {typeof jobDetails.result === 'string'
                    ? jobDetails.result
                    : JSON.stringify(jobDetails.result, null, 2)
                  }
                </pre>
              </div>
            )}

            <div style={{ marginTop: '20px', textAlign: 'right' }}>
              <button onClick={closeLogModal} className="primary">關閉</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;

