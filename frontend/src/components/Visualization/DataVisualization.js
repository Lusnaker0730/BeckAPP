import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import analyticsAxios from '../../utils/analyticsAxios';
import { Line, Bar, Scatter, Pie } from 'react-chartjs-2';
import './Visualization.css';

const DataVisualization = () => {
  const [chartType, setChartType] = useState('bar');
  const [xAxis, setXAxis] = useState('age_group');
  const [yAxis, setYAxis] = useState('count');
  const [filterCondition, setFilterCondition] = useState('all');
  const [visualizationData, setVisualizationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState('global'); // 'global', 'diagnosis', 'demographic'
  const [selectedDiagnosis, setSelectedDiagnosis] = useState('');
  const [availableDiagnoses, setAvailableDiagnoses] = useState([]);
  const [demographicFilter, setDemographicFilter] = useState('all'); // 'all', 'male', 'female', 'age_0_18', etc.

  const axisOptions = [
    { value: 'age_group', label: '年齡組' },
    { value: 'gender', label: '性別' },
    { value: 'condition_code', label: '診斷代碼' },
    { value: 'encounter_type', label: '就診類型' },
    { value: 'date', label: '日期' },
    { value: 'count', label: '人次' },
    { value: 'average', label: '平均值' },
    { value: 'total', label: '總計' },
  ];

  const chartTypes = [
    { value: 'bar', label: '柱狀圖', icon: '📊' },
    { value: 'line', label: '折線圖', icon: '📈' },
    { value: 'scatter', label: '散點圖', icon: '⚫' },
    { value: 'pie', label: '圓餅圖', icon: '🥧' },
  ];

  useEffect(() => {
    fetchAvailableDiagnoses();
  }, []);

  useEffect(() => {
    // Auto-adjust axes based on analysis mode for better defaults
    // Note: Allow condition_code in diagnosis mode for comorbidity analysis
    if (analysisMode === 'demographic') {
      if (xAxis !== 'condition_code' && xAxis !== 'date') {
        setXAxis('condition_code'); // Show diagnoses when analyzing demographics
      }
    }
  }, [analysisMode]);

  useEffect(() => {
    fetchVisualizationData();
  }, [xAxis, yAxis, filterCondition, analysisMode, selectedDiagnosis, demographicFilter]);

  const fetchAvailableDiagnoses = async () => {
    try {
      const response = await axios.get('/api/analytics/available-diagnoses', {
        params: { limit: 100 }
      });
      setAvailableDiagnoses(response.data);
      if (response.data.length > 0) {
        setSelectedDiagnosis(response.data[0].code_text);
      }
    } catch (error) {
      console.error('Error fetching available diagnoses:', error);
    }
  };

  const fetchVisualizationData = async () => {
    setLoading(true);
    try {
      let endpoint = '/api/visualization';
      let params = {
        xAxis,
        yAxis,
        filter: filterCondition
      };

      // Different endpoints based on analysis mode
      if (analysisMode === 'diagnosis' && selectedDiagnosis) {
        endpoint = '/api/visualization/by-diagnosis';
        params.diagnosis = selectedDiagnosis;
      } else if (analysisMode === 'demographic') {
        endpoint = '/api/visualization/by-demographic';
        params.demographic = demographicFilter;
      }

      // Use analyticsAxios for visualization endpoints (analytics-service on port 8002)
      const response = await analyticsAxios.get(endpoint, { params });
      setVisualizationData(response.data);
    } catch (error) {
      console.error('Error fetching visualization data:', error);
      console.error('Full error:', error.response?.data || error.message);
      // Show error instead of fake data (medical software should never show fake data)
      setVisualizationData({
        labels: [],
        datasets: [{
          label: yAxis === 'count' ? '人次' : yAxis,
          data: [],
          backgroundColor: [],
        }],
        error: '数据加载失败: ' + (error.response?.data?.error || error.message || '未知错误')
      });
    } finally {
      setLoading(false);
    }
  };

  const generateSampleData = () => {
    // DO NOT generate fake data for medical software
    // Instead, show empty chart with error message
    setVisualizationData({
      labels: [],
      datasets: [
        {
          label: yAxis === 'count' ? '人次' : yAxis,
          data: [],
          backgroundColor: [],
          borderColor: [],
          borderWidth: 2,
        },
      ],
      error: '无法加载数据，请检查网络连接或稍后重试'
    });
  };

  const renderChart = () => {
    if (!visualizationData) return null;

    // Build dynamic title based on analysis mode
    let chartTitle = '';
    if (analysisMode === 'diagnosis' && selectedDiagnosis) {
      if (xAxis === 'condition_code') {
        chartTitle = `${selectedDiagnosis} - 共病症分析`;
      } else {
        chartTitle = `${selectedDiagnosis} - ${axisOptions.find(a => a.value === xAxis)?.label}分佈`;
      }
    } else if (analysisMode === 'demographic') {
      const demographicLabels = {
        'all': '全部人群',
        'male': '男性',
        'female': '女性',
        'age_0_18': '0-18歲',
        'age_19_35': '19-35歲',
        'age_36_50': '36-50歲',
        'age_51_65': '51-65歲',
        'age_65_plus': '65歲以上'
      };
      chartTitle = `${demographicLabels[demographicFilter] || demographicFilter} - ${axisOptions.find(a => a.value === xAxis)?.label}`;
    } else {
      chartTitle = `${axisOptions.find(a => a.value === xAxis)?.label} vs ${axisOptions.find(a => a.value === yAxis)?.label}`;
    }

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: chartTitle,
        },
      },
    };

    switch (chartType) {
      case 'line':
        return <Line data={visualizationData} options={options} />;
      case 'scatter':
        return <Scatter data={visualizationData} options={options} />;
      case 'pie':
        return <Pie data={visualizationData} options={options} />;
      default:
        return <Bar data={visualizationData} options={options} />;
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>數據視覺化</h1>
        <p>
          {analysisMode === 'global' && '全局分析：查看所有數據的整體分佈'}
          {analysisMode === 'diagnosis' && '診斷分析：查看特定診斷的患者人口統計分佈或共病症分析'}
          {analysisMode === 'demographic' && '人群分析：查看特定人群的診斷分佈'}
        </p>
      </div>

      {/* Configuration Panel */}
      <div className="card">
        <h3 style={{ marginBottom: '20px' }}>圖表配置</h3>
        
        {/* Analysis Mode Selection */}
        <div style={{ marginBottom: '20px' }}>
          <label className="form-label">分析模式</label>
          <div style={{ display: 'flex', gap: '15px', marginTop: '10px' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="radio" 
                value="global" 
                checked={analysisMode === 'global'}
                onChange={(e) => setAnalysisMode(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              全局分析（所有數據）
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="radio" 
                value="diagnosis" 
                checked={analysisMode === 'diagnosis'}
                onChange={(e) => setAnalysisMode(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              診斷分析（按特定診斷）
            </label>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input 
                type="radio" 
                value="demographic" 
                checked={analysisMode === 'demographic'}
                onChange={(e) => setAnalysisMode(e.target.value)}
                style={{ marginRight: '5px' }}
              />
              人群分析（按人群特徵）
            </label>
          </div>
        </div>

        {/* Diagnosis Selection (when in diagnosis mode) */}
        {analysisMode === 'diagnosis' && (
          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label className="form-label">選擇診斷</label>
            <select 
              value={selectedDiagnosis}
              onChange={(e) => setSelectedDiagnosis(e.target.value)}
            >
              {availableDiagnoses.map((diag, index) => (
                <option key={index} value={diag.code_text}>
                  {diag.code_text} ({diag.count} 筆)
                </option>
              ))}
            </select>
            <p style={{ fontSize: '0.9em', color: '#666', marginTop: '5px' }}>
              {xAxis === 'condition_code' 
                ? '顯示該診斷患者群體中最常見的共病症（前10種）' 
                : '查看特定診斷的患者人口統計分佈（例如：高血壓患者的男女比例）'}
            </p>
          </div>
        )}

        {/* Demographic Filter (when in demographic mode) */}
        {analysisMode === 'demographic' && (
          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label className="form-label">選擇人群特徵</label>
            <select 
              value={demographicFilter}
              onChange={(e) => setDemographicFilter(e.target.value)}
            >
              <option value="all">全部人群</option>
              <optgroup label="性別">
                <option value="male">男性</option>
                <option value="female">女性</option>
              </optgroup>
              <optgroup label="年齡組">
                <option value="age_0_18">0-18歲</option>
                <option value="age_19_35">19-35歲</option>
                <option value="age_36_50">36-50歲</option>
                <option value="age_51_65">51-65歲</option>
                <option value="age_65_plus">65歲以上</option>
              </optgroup>
            </select>
            <p style={{ fontSize: '0.9em', color: '#666', marginTop: '5px' }}>
              查看特定人群的診斷分佈（例如：男性最多的診斷是什麼）
            </p>
          </div>
        )}
        
        {/* Chart Type Selection */}
        <div className="form-group">
          <label className="form-label">圖表類型</label>
          <div className="chart-type-selector">
            {chartTypes.map(type => (
              <button
                key={type.value}
                className={`chart-type-btn ${chartType === type.value ? 'active' : ''}`}
                onClick={() => setChartType(type.value)}
              >
                <span className="icon">{type.icon}</span>
                <span>{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Axis Configuration */}
        <div className="filters-grid">
          <div className="form-group">
            <label className="form-label">X 軸變數</label>
            <select value={xAxis} onChange={(e) => setXAxis(e.target.value)}>
              {axisOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Y 軸變數</label>
            <select value={yAxis} onChange={(e) => setYAxis(e.target.value)}>
              {axisOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">篩選條件</label>
            <select 
              value={filterCondition}
              onChange={(e) => setFilterCondition(e.target.value)}
            >
              <option value="all">全部</option>
              <option value="condition">依診斷</option>
              <option value="timerange">依時間範圍</option>
              <option value="location">依地區</option>
            </select>
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <button onClick={fetchVisualizationData} className="primary">
            生成圖表
          </button>
          <button 
            onClick={() => {
              // Export chart as image
              const canvas = document.querySelector('canvas');
              const url = canvas.toDataURL('image/png');
              const link = document.createElement('a');
              link.download = 'chart.png';
              link.href = url;
              link.click();
            }}
            className="outline"
            style={{ marginLeft: '12px' }}
          >
            下載圖表
          </button>
        </div>
      </div>

      {/* Chart Display */}
      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
        </div>
      ) : (
        <div className="chart-container" style={{ height: '500px' }}>
          {visualizationData && visualizationData.error ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#dc2626',
              textAlign: 'center',
              padding: '40px'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>⚠️</div>
              <h3 style={{ marginBottom: '10px' }}>数据加载失败</h3>
              <p style={{ color: '#6b7280', maxWidth: '500px' }}>
                {visualizationData.error}
              </p>
              <p style={{ color: '#9ca3af', fontSize: '14px', marginTop: '20px' }}>
                医疗软件不会显示假数据。请检查：
              </p>
              <ul style={{ color: '#9ca3af', fontSize: '14px', textAlign: 'left', marginTop: '10px' }}>
                <li>Analytics Service (端口 8002) 是否正在运行</li>
                <li>数据库中是否有相关数据</li>
                <li>网络连接是否正常</li>
              </ul>
            </div>
          ) : visualizationData && visualizationData.labels && visualizationData.labels.length > 0 ? (
            renderChart()
          ) : (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#9ca3af',
              textAlign: 'center',
              padding: '40px'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
              <h3 style={{ marginBottom: '10px', color: '#6b7280' }}>无数据</h3>
              <p>当前筛选条件下没有数据</p>
            </div>
          )}
        </div>
      )}

      {/* Data Table */}
      {visualizationData && (
        <div className="card">
          <h3 style={{ marginBottom: '20px' }}>數據表格</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>{axisOptions.find(a => a.value === xAxis)?.label}</th>
                  <th>{axisOptions.find(a => a.value === yAxis)?.label}</th>
                  <th>佔比</th>
                </tr>
              </thead>
              <tbody>
                {visualizationData.labels?.map((label, index) => {
                  const value = visualizationData.datasets[0].data[index];
                  const total = visualizationData.datasets[0].data.reduce((a, b) => a + b, 0);
                  const percentage = ((value / total) * 100).toFixed(1);
                  
                  return (
                    <tr key={index}>
                      <td>{label}</td>
                      <td>{value.toLocaleString()}</td>
                      <td>{percentage}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataVisualization;

