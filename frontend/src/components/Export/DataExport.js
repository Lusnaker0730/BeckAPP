import React, { useState } from 'react';
import axios from '../../utils/axiosConfig';
import Papa from 'papaparse';
import './Export.css';

const DataExport = () => {
  const [exportConfig, setExportConfig] = useState({
    dataType: 'conditions',
    format: 'csv',
    dateFrom: '',
    dateTo: '',
    includeFields: {
      patient: true,
      condition: true,
      encounter: true,
      observation: false
    }
  });
  const [loading, setLoading] = useState(false);
  const [exportHistory, setExportHistory] = useState([]);

  const dataTypes = [
    { value: 'conditions', label: '診斷資料 (Conditions)' },
    { value: 'patients', label: '病患資料 (Patients)' },
    { value: 'encounters', label: '就診資料 (Encounters)' },
    { value: 'observations', label: '觀察資料 (Observations)' },
    { value: 'combined', label: '綜合報表' },
  ];

  const formats = [
    { value: 'csv', label: 'CSV', icon: '📄' },
    { value: 'json', label: 'JSON', icon: '📋' },
    { value: 'excel', label: 'Excel', icon: '📊' },
    { value: 'parquet', label: 'Parquet', icon: '🗂️' },
  ];

  const handleExport = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/export', exportConfig, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const extension = exportConfig.format === 'excel' ? 'xlsx' : exportConfig.format;
      link.setAttribute('download', `fhir_export_${exportConfig.dataType}_${Date.now()}.${extension}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      // Add to history
      setExportHistory([
        {
          timestamp: new Date().toLocaleString('zh-TW'),
          dataType: exportConfig.dataType,
          format: exportConfig.format,
          status: 'success'
        },
        ...exportHistory
      ]);

    } catch (error) {
      console.error('Export error:', error);
      alert('匯出失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldToggle = (field) => {
    setExportConfig({
      ...exportConfig,
      includeFields: {
        ...exportConfig.includeFields,
        [field]: !exportConfig.includeFields[field]
      }
    });
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>資料匯出</h1>
        <p>匯出 FHIR 數據為各種格式</p>
      </div>

      <div className="grid grid-cols-2">
        {/* Export Configuration */}
        <div className="card">
          <h3 style={{ marginBottom: '20px' }}>匯出設定</h3>

          <div className="form-group">
            <label className="form-label">資料類型</label>
            <select 
              value={exportConfig.dataType}
              onChange={(e) => setExportConfig({...exportConfig, dataType: e.target.value})}
            >
              {dataTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">匯出格式</label>
            <div className="format-selector">
              {formats.map(format => (
                <button
                  key={format.value}
                  className={`format-btn ${exportConfig.format === format.value ? 'active' : ''}`}
                  onClick={() => setExportConfig({...exportConfig, format: format.value})}
                >
                  <span className="icon">{format.icon}</span>
                  <span>{format.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">日期範圍</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <input
                type="date"
                value={exportConfig.dateFrom}
                onChange={(e) => setExportConfig({...exportConfig, dateFrom: e.target.value})}
                placeholder="開始日期"
              />
              <input
                type="date"
                value={exportConfig.dateTo}
                onChange={(e) => setExportConfig({...exportConfig, dateTo: e.target.value})}
                placeholder="結束日期"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">包含欄位</label>
            <div className="checkbox-group">
              {Object.keys(exportConfig.includeFields).map(field => (
                <label key={field} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={exportConfig.includeFields[field]}
                    onChange={() => handleFieldToggle(field)}
                  />
                  <span>{field.charAt(0).toUpperCase() + field.slice(1)}</span>
                </label>
              ))}
            </div>
          </div>

          <button 
            onClick={handleExport}
            className="primary full-width"
            disabled={loading}
          >
            {loading ? '匯出中...' : '開始匯出'}
          </button>
        </div>

        {/* Export Preview */}
        <div className="card">
          <h3 style={{ marginBottom: '20px' }}>匯出預覽</h3>
          
          <div className="export-summary">
            <div className="summary-item">
              <span className="label">資料類型</span>
              <span className="value">
                {dataTypes.find(t => t.value === exportConfig.dataType)?.label}
              </span>
            </div>
            <div className="summary-item">
              <span className="label">格式</span>
              <span className="value">{exportConfig.format.toUpperCase()}</span>
            </div>
            <div className="summary-item">
              <span className="label">日期範圍</span>
              <span className="value">
                {exportConfig.dateFrom && exportConfig.dateTo 
                  ? `${exportConfig.dateFrom} ~ ${exportConfig.dateTo}`
                  : '全部'}
              </span>
            </div>
            <div className="summary-item">
              <span className="label">包含欄位</span>
              <span className="value">
                {Object.entries(exportConfig.includeFields)
                  .filter(([_, v]) => v)
                  .map(([k, _]) => k)
                  .join(', ')}
              </span>
            </div>
          </div>

          <div className="alert info" style={{ marginTop: '20px' }}>
            <strong>提示：</strong> 大量數據匯出可能需要較長時間，請耐心等待。
          </div>
        </div>
      </div>

      {/* Export History */}
      <div className="card">
        <h3 style={{ marginBottom: '20px' }}>匯出歷史</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>時間</th>
                <th>資料類型</th>
                <th>格式</th>
                <th>狀態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {exportHistory.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                    尚無匯出記錄
                  </td>
                </tr>
              ) : (
                exportHistory.map((record, index) => (
                  <tr key={index}>
                    <td>{record.timestamp}</td>
                    <td>{dataTypes.find(t => t.value === record.dataType)?.label}</td>
                    <td>{record.format.toUpperCase()}</td>
                    <td>
                      <span className={`badge ${record.status === 'success' ? 'success' : 'danger'}`}>
                        {record.status === 'success' ? '成功' : '失敗'}
                      </span>
                    </td>
                    <td>
                      <button className="outline" style={{ padding: '6px 12px', fontSize: '12px' }}>
                        重新下載
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DataExport;

