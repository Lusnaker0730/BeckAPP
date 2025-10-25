import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import { Bar, Line } from 'react-chartjs-2';
import './Analysis.css';

const DiagnosisAnalysis = () => {
  const [selectedDiagnosis, setSelectedDiagnosis] = useState('influenza');
  const [timeRange, setTimeRange] = useState('yearly');
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [etlJobs, setEtlJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [searchMode, setSearchMode] = useState('predefined'); // 'predefined' or 'code'
  const [searchCode, setSearchCode] = useState('');
  const [availableDiagnoses, setAvailableDiagnoses] = useState([]);
  const [selectedDiagnosisLabel, setSelectedDiagnosisLabel] = useState('流感 (Influenza)');
  const [startYear, setStartYear] = useState(2015);
  const [endYear, setEndYear] = useState(2020);

  const diagnosisOptions = [
    { value: 'influenza', label: '流感 (Influenza)', code: 'J09-J11, SNOMED-CT' },
    { value: 'myocardial_infarction', label: '心肌梗塞 (Myocardial Infarction)', code: 'I21, SNOMED-CT' },
    { value: 'lung_adenocarcinoma', label: '肺腺癌 (Lung Adenocarcinoma)', code: 'C34, SNOMED-CT' },
    { value: 'diabetes', label: '糖尿病 (Diabetes)', code: 'E10-E14, SNOMED-CT' },
    { value: 'hypertension', label: '高血壓 (Hypertension)', code: 'I10, SNOMED-CT' },
    { value: 'copd', label: '慢性阻塞性肺病 (COPD)', code: 'J44, SNOMED-CT' },
  ];

  useEffect(() => {
    fetchEtlJobs();
    fetchAvailableDiagnoses();
  }, []);

  useEffect(() => {
    fetchAnalysisData();
  }, [selectedDiagnosis, timeRange, selectedJobId, searchMode, searchCode, startYear, endYear]);

  const fetchEtlJobs = async () => {
    try {
      const response = await axios.get('/api/analytics/etl-jobs-list');
      setEtlJobs(response.data);
    } catch (error) {
      console.error('Error fetching ETL jobs:', error);
    }
  };

  const fetchAvailableDiagnoses = async () => {
    try {
      const response = await axios.get('/api/analytics/available-diagnoses', {
        params: { limit: 100 }
      });
      setAvailableDiagnoses(response.data);
    } catch (error) {
      console.error('Error fetching available diagnoses:', error);
    }
  };

  const fetchAnalysisData = async () => {
    setLoading(true);
    try {
      let response;
      
      if (searchMode === 'code' && searchCode.trim()) {
        // Search by code
        const params = {
          code: searchCode.trim(),
          timeRange: timeRange,
          startYear: startYear,
          endYear: endYear
        };
        
        response = await axios.get('/api/analytics/diagnosis-by-code', { params });
      } else {
        // Predefined diagnosis
        const params = {
          diagnosis: selectedDiagnosis,
          timeRange: timeRange,
          startYear: startYear,
          endYear: endYear
        };
        
        // Add job_id filter if selected
        if (selectedJobId) {
          params.job_id = selectedJobId;
        }
        
        response = await axios.get('/api/analytics/diagnosis', { params });
      }
      
      setAnalysisData(response.data);
      
      // Update the diagnosis label with the actual diagnosis name from response
      if (response.data.diagnosisName) {
        setSelectedDiagnosisLabel(response.data.diagnosisName);
      }
    } catch (error) {
      console.error('Error fetching analysis data:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = {
    labels: analysisData?.labels || [],
    datasets: [
      {
        label: '發生人次',
        data: analysisData?.counts || [],
        backgroundColor: 'rgba(37, 99, 235, 0.8)',
        borderColor: 'rgb(37, 99, 235)',
        borderWidth: 2,
      },
    ],
  };

  const trendChartData = {
    labels: analysisData?.labels || [],
    datasets: [
      {
        label: '趨勢',
        data: analysisData?.counts || [],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `${selectedDiagnosisLabel} 分析`,
      },
    },
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>診斷分析</h1>
        <p>分析特定診斷的年度發生人次</p>
      </div>

      {/* Filters */}
      <div className="card">
        <div style={{ marginBottom: '15px' }}>
          <label className="form-label">搜尋模式</label>
          <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="radio" 
                value="predefined" 
                checked={searchMode === 'predefined'}
                onChange={(e) => setSearchMode(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              預定義診斷
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="radio" 
                value="code" 
                checked={searchMode === 'code'}
                onChange={(e) => setSearchMode(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              代碼搜尋 (SNOMED-CT / ICD-10)
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="radio" 
                value="database" 
                checked={searchMode === 'database'}
                onChange={(e) => setSearchMode(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              資料庫診斷
            </label>
          </div>
        </div>

        <div className="filters-grid">
          {searchMode === 'predefined' && (
            <div className="form-group">
              <label className="form-label">選擇診斷</label>
              <select 
                value={selectedDiagnosis}
                onChange={(e) => {
                  setSelectedDiagnosis(e.target.value);
                  const option = diagnosisOptions.find(opt => opt.value === e.target.value);
                  setSelectedDiagnosisLabel(option?.label || '');
                }}
              >
                {diagnosisOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label} ({option.code})
                  </option>
                ))}
              </select>
            </div>
          )}

          {searchMode === 'code' && (
            <div className="form-group">
              <label className="form-label">輸入代碼 (SNOMED-CT / ICD-10)</label>
              <input 
                type="text" 
                className="form-control"
                value={searchCode}
                onChange={(e) => {
                  setSearchCode(e.target.value);
                  setSelectedDiagnosisLabel(e.target.value || '代碼搜尋');
                }}
                placeholder="例如: J09, 6142004, diabetes, etc."
              />
            </div>
          )}

          {searchMode === 'database' && (
            <div className="form-group">
              <label className="form-label">選擇診斷（來自資料庫）</label>
              <select 
                value={selectedDiagnosis}
                onChange={(e) => {
                  setSelectedDiagnosis(e.target.value);
                  setSelectedDiagnosisLabel(e.target.value);
                }}
              >
                {availableDiagnoses.length === 0 ? (
                  <option value="">資料庫中無診斷數據</option>
                ) : (
                  availableDiagnoses.map((diag, index) => (
                    <option key={index} value={diag.code_text}>
                      {diag.code_text} ({diag.count} 筆)
                    </option>
                  ))
                )}
              </select>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">時間範圍</label>
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <option value="monthly">月度</option>
              <option value="quarterly">季度</option>
              <option value="yearly">年度</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">起始年份</label>
            <select 
              value={startYear}
              onChange={(e) => setStartYear(Number(e.target.value))}
            >
              {Array.from({ length: 50 }, (_, i) => 2025 - i).map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">結束年份</label>
            <select 
              value={endYear}
              onChange={(e) => setEndYear(Number(e.target.value))}
            >
              {Array.from({ length: 50 }, (_, i) => 2025 - i).map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          {searchMode !== 'code' && (
            <div className="form-group">
              <label className="form-label">ETL 任務篩選</label>
              <select 
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
              >
                <option value="">全部數據</option>
                {etlJobs.map(job => (
                  <option key={job.job_id} value={job.job_id}>
                    {job.resource_type} ({job.records_processed} 筆) - {job.start_time ? new Date(job.start_time).toLocaleDateString() : 'N/A'}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">&nbsp;</label>
            <button onClick={fetchAnalysisData} className="primary">
              更新分析
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
        </div>
      ) : (
        <>
          {/* Display Current Diagnosis Name */}
          {analysisData && analysisData.totalCount > 0 && (
            <div className="card" style={{ 
              backgroundColor: '#f0f9ff', 
              border: '2px solid #3b82f6',
              marginBottom: '20px',
              padding: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.2em', fontWeight: 'bold', color: '#1e40af' }}>
                  正在分析：
                </span>
                <span style={{ fontSize: '1.3em', fontWeight: 'bold', color: '#2563eb' }}>
                  {selectedDiagnosisLabel}
                </span>
                {searchMode === 'code' && (
                  <span style={{ 
                    fontSize: '0.9em', 
                    color: '#64748b',
                    marginLeft: '10px',
                    padding: '4px 12px',
                    backgroundColor: '#e0f2fe',
                    borderRadius: '12px'
                  }}>
                    代碼: {searchCode}
                  </span>
                )}
                {searchMode === 'database' && (
                  <span style={{ 
                    fontSize: '0.9em', 
                    color: '#64748b',
                    marginLeft: '10px',
                    padding: '4px 12px',
                    backgroundColor: '#e0f2fe',
                    borderRadius: '12px'
                  }}>
                    來自資料庫
                  </span>
                )}
                <span style={{ 
                  fontSize: '0.9em', 
                  color: '#059669',
                  marginLeft: 'auto',
                  padding: '4px 12px',
                  backgroundColor: '#d1fae5',
                  borderRadius: '12px',
                  fontWeight: '600'
                }}>
                  ✓ {analysisData.totalCount.toLocaleString()} 筆記錄
                </span>
              </div>
            </div>
          )}
          
          {/* Summary Statistics */}
          <div className="grid grid-cols-4">
            <div className="stat-card">
              <div className="title">總人次</div>
              <div className="value">{analysisData?.totalCount?.toLocaleString() || 0}</div>
            </div>
            <div className="stat-card">
              <div className="title">平均每期</div>
              <div className="value">{analysisData?.averageCount?.toLocaleString() || 0}</div>
            </div>
            <div className="stat-card">
              <div className="title">最高峰</div>
              <div className="value">{analysisData?.peakCount?.toLocaleString() || 0}</div>
            </div>
            <div className="stat-card">
              <div className="title">增長率</div>
              <div className={`value ${analysisData?.growthRate >= 0 ? 'positive' : 'negative'}`}>
                {analysisData?.growthRate?.toFixed(1) || 0}%
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2">
            <div className="chart-container">
              <div className="chart-header">
                <h3 className="chart-title">發生人次柱狀圖</h3>
              </div>
              <div style={{ height: '350px' }}>
                <Bar data={chartData} options={chartOptions} />
              </div>
            </div>

            <div className="chart-container">
              <div className="chart-header">
                <h3 className="chart-title">趨勢折線圖</h3>
              </div>
              <div style={{ height: '350px' }}>
                <Line data={trendChartData} options={chartOptions} />
              </div>
            </div>
          </div>

          {/* Detailed Data Table */}
          <div className="card">
            <h3 style={{ marginBottom: '20px' }}>詳細數據</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>時間期間</th>
                    <th>發生人次</th>
                    <th>較前期變化</th>
                    <th>佔比</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisData?.details?.map((row, index) => (
                    <tr key={index}>
                      <td>{row.period}</td>
                      <td>{row.count.toLocaleString()}</td>
                      <td className={row.change >= 0 ? 'positive' : 'negative'}>
                        {row.change >= 0 ? '+' : ''}{row.change.toFixed(1)}%
                      </td>
                      <td>{row.percentage.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default DiagnosisAnalysis;

