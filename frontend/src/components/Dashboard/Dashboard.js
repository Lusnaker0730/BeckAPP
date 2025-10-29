import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import './Dashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartDataLabels
);

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalPatients: 0,
    totalConditions: 0,
    totalEncounters: 0,
    totalObservations: 0
  });
  const [trendData, setTrendData] = useState(null);
  const [topConditions, setTopConditions] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [etlJobs, setEtlJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [trendStartYear, setTrendStartYear] = useState(2020);
  const [trendEndYear, setTrendEndYear] = useState(new Date().getFullYear());
  const [comparisonMode, setComparisonMode] = useState(false);
  const [compareStartYear, setCompareStartYear] = useState(2015);
  const [compareEndYear, setCompareEndYear] = useState(2019);
  const [compareTopConditions, setCompareTopConditions] = useState(null);

  // Export functions
  const exportToCSV = () => {
    if (!topConditions || !topConditions.labels || topConditions.labels.length === 0) {
      alert('沒有可導出的數據');
      return;
    }

    const headers = ['排名', '診斷', '人次', '百分比', '趨勢', '變化率'];
    const rows = topConditions.labels.map((label, index) => {
      const trend = topConditions.trends && topConditions.trends[index];
      let trendText = '無';
      let changeText = '0%';
      
      if (trend && trend.direction !== 'none') {
        if (trend.direction === 'up') trendText = '上升';
        else if (trend.direction === 'down') trendText = '下降';
        else if (trend.direction === 'stable') trendText = '穩定';
        else if (trend.direction === 'new') trendText = '新增';
        changeText = `${trend.change}%`;
      }
      
      return [
        index + 1,
        `"${label}"`,  // Quote to handle commas in diagnosis names
        topConditions.values[index],
        `${topConditions.percentages[index]}%`,
        trendText,
        changeText
      ].join(',');
    });

    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });  // Add BOM for Excel
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `前五大診斷_${trendStartYear}-${trendEndYear}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToJSON = () => {
    if (!topConditions || !topConditions.labels || topConditions.labels.length === 0) {
      alert('沒有可導出的數據');
      return;
    }

    const exportData = {
      metadata: {
        exportDate: new Date().toISOString(),
        yearRange: `${trendStartYear}-${trendEndYear}`,
        etlJobId: selectedJobId || 'all',
        total: topConditions.total
      },
      diagnoses: topConditions.labels.map((label, index) => ({
        rank: index + 1,
        diagnosis: label,
        count: topConditions.values[index],
        percentage: topConditions.percentages[index],
        trend: topConditions.trends && topConditions.trends[index] ? topConditions.trends[index] : { direction: 'none', change: 0 }
      }))
    };

    const json = JSON.stringify(exportData, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `前五大診斷_${trendStartYear}-${trendEndYear}_${new Date().toISOString().split('T')[0]}.json`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  useEffect(() => {
    fetchEtlJobs();
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedJobId, trendStartYear, trendEndYear, comparisonMode, compareStartYear, compareEndYear]);

  const fetchEtlJobs = async () => {
    try {
      const response = await axios.get('/api/analytics/etl-jobs-list');
      setEtlJobs(response.data);
    } catch (error) {
      console.error('Error fetching ETL jobs:', error);
      // Error handling is done by axios interceptor
    }
  };

  const fetchDashboardData = async () => {
    try {
      // Add job_id parameter if selected
      const params = selectedJobId ? { job_id: selectedJobId } : {};

      // Fetch statistics
      const statsResponse = await axios.get('/api/analytics/stats', { params });
      setStats(statsResponse.data);

      // Fetch trend data with year range
      const trendParams = { 
        ...params, 
        start_year: trendStartYear, 
        end_year: trendEndYear 
      };
      const trendResponse = await axios.get('/api/analytics/trends', { params: trendParams });
      setTrendData(trendResponse.data);

      // Fetch top conditions with same year range
      const conditionsParams = {
        ...params,
        start_year: trendStartYear,
        end_year: trendEndYear
      };
      const conditionsResponse = await axios.get('/api/analytics/top-conditions', { params: conditionsParams });
      setTopConditions(conditionsResponse.data);

      // Fetch comparison data if comparison mode is enabled
      if (comparisonMode) {
        const compareParams = {
          ...params,
          start_year: compareStartYear,
          end_year: compareEndYear
        };
        const compareResponse = await axios.get('/api/analytics/top-conditions', { params: compareParams });
        setCompareTopConditions(compareResponse.data);
      } else {
        setCompareTopConditions(null);
      }

      // Fetch recent activities
      const activitiesResponse = await axios.get('/api/analytics/recent-activities', { params: { limit: 10 } });
      setRecentActivities(activitiesResponse.data);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Error handling is done by axios interceptor
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  const lineChartData = {
    labels: trendData?.labels || [],
    datasets: [
      {
        label: '診斷人次',
        data: trendData?.values || [],
        borderColor: 'rgb(37, 99, 235)',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const barChartData = {
    labels: topConditions?.labels || [],
    datasets: [
      {
        label: '人次',
        data: topConditions?.values || [],
        backgroundColor: [
          'rgba(37, 99, 235, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        // Store percentages for display
        percentages: topConditions?.percentages || [],
      },
    ],
  };

  const compareBarChartData = {
    labels: compareTopConditions?.labels || [],
    datasets: [
      {
        label: '人次',
        data: compareTopConditions?.values || [],
        backgroundColor: [
          'rgba(234, 88, 12, 0.8)',  // Orange theme for comparison
          'rgba(168, 85, 247, 0.8)',
          'rgba(236, 72, 153, 0.8)',
          'rgba(14, 165, 233, 0.8)',
          'rgba(34, 197, 94, 0.8)',
        ],
        percentages: compareTopConditions?.percentages || [],
      },
    ],
  };

  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      datalabels: {
        display: false  // Disable datalabels for line chart
      }
    },
  };

  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            const percentage = context.dataset.percentages[context.dataIndex];
            return `${label}: ${value.toLocaleString()} (${percentage}%)`;
          }
        }
      },
      datalabels: {
        display: true,
        color: '#fff',
        font: {
          weight: 'bold',
          size: 12
        },
        formatter: function(value, context) {
          const percentage = context.dataset.percentages[context.dataIndex];
          return `${percentage}%`;
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return value.toLocaleString();
          }
        }
      }
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>儀錶板</h1>
        <p>總覽您的 FHIR 數據分析</p>
      </div>

      {/* Job Filter */}
      <div className="card" style={{ marginBottom: '20px', padding: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <label style={{ fontWeight: '500', minWidth: '100px' }}>ETL 任務篩選:</label>
          <select 
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
          >
            <option value="">全部數據</option>
            {etlJobs.map(job => (
              <option key={job.job_id} value={job.job_id}>
                {job.resource_type} ({job.records_processed} 筆) - {job.start_time ? new Date(job.start_time).toLocaleDateString() : 'N/A'}
              </option>
            ))}
          </select>
          <button onClick={fetchDashboardData} className="primary" style={{ padding: '8px 20px' }}>
            重新載入
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4">
        <div className="stat-card">
          <div className="title">總病患數</div>
          <div className="value">{stats.totalPatients.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="title">總診斷數</div>
          <div className="value">{stats.totalConditions.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="title">總就診次數</div>
          <div className="value">{stats.totalEncounters.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="title">總觀察記錄</div>
          <div className="value">{stats.totalObservations.toLocaleString()}</div>
        </div>
      </div>

      {/* Comparison Mode Toggle */}
      <div className="card" style={{ marginBottom: '20px', padding: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontWeight: '500' }}>
            <input 
              type="checkbox"
              checked={comparisonMode}
              onChange={(e) => setComparisonMode(e.target.checked)}
              style={{ marginRight: '8px', cursor: 'pointer', width: '18px', height: '18px' }}
            />
            啟用對比模式
          </label>
          
          {comparisonMode && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: 'auto' }}>
              <label style={{ fontSize: '14px', color: '#6b7280' }}>對比期間:</label>
              <select 
                value={compareStartYear}
                onChange={(e) => setCompareStartYear(Number(e.target.value))}
                style={{ 
                  padding: '4px 8px', 
                  borderRadius: '4px', 
                  border: '1px solid #d1d5db',
                  fontSize: '14px'
                }}
              >
                {Array.from({ length: 26 }, (_, i) => 2000 + i).map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
              <span style={{ color: '#6b7280' }}>至</span>
              <select 
                value={compareEndYear}
                onChange={(e) => setCompareEndYear(Number(e.target.value))}
                style={{ 
                  padding: '4px 8px', 
                  borderRadius: '4px', 
                  border: '1px solid #d1d5db',
                  fontSize: '14px'
                }}
              >
                {Array.from({ length: 26 }, (_, i) => 2000 + i).map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2">
        <div className="chart-container">
          <div className="chart-header">
            <h3 className="chart-title">診斷趨勢分析</h3>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '10px' }}>
              <label style={{ fontSize: '14px', color: '#6b7280' }}>年份區間:</label>
              <select 
                value={trendStartYear}
                onChange={(e) => setTrendStartYear(Number(e.target.value))}
                style={{ 
                  padding: '4px 8px', 
                  borderRadius: '4px', 
                  border: '1px solid #d1d5db',
                  fontSize: '14px'
                }}
              >
                {Array.from({ length: 26 }, (_, i) => 2000 + i).map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
              <span style={{ color: '#6b7280' }}>至</span>
              <select 
                value={trendEndYear}
                onChange={(e) => setTrendEndYear(Number(e.target.value))}
                style={{ 
                  padding: '4px 8px', 
                  borderRadius: '4px', 
                  border: '1px solid #d1d5db',
                  fontSize: '14px'
                }}
              >
                {Array.from({ length: 26 }, (_, i) => 2000 + i).map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ height: '300px' }}>
            <Line data={lineChartData} options={lineChartOptions} />
          </div>
        </div>

        {!comparisonMode ? (
          // Single view mode
          <div className="chart-container">
            <div className="chart-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 className="chart-title">前五大診斷</h3>
                <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '5px' }}>
                  {trendStartYear} - {trendEndYear}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  onClick={exportToCSV}
                  style={{
                    padding: '6px 12px',
                    fontSize: '13px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => e.target.style.backgroundColor = '#059669'}
                  onMouseOut={(e) => e.target.style.backgroundColor = '#10b981'}
                  title="導出為 CSV 格式"
                >
                  📊 CSV
                </button>
                <button 
                  onClick={exportToJSON}
                  style={{
                    padding: '6px 12px',
                    fontSize: '13px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => e.target.style.backgroundColor = '#2563eb'}
                  onMouseOut={(e) => e.target.style.backgroundColor = '#3b82f6'}
                  title="導出為 JSON 格式"
                >
                  📄 JSON
                </button>
              </div>
            </div>
            <div style={{ height: '300px' }}>
              <Bar data={barChartData} options={barChartOptions} />
            </div>
            
            {/* Trend indicators */}
            {topConditions && topConditions.trends && topConditions.trends.length > 0 && (
              <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f9fafb', borderRadius: '6px' }}>
                <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px', color: '#374151' }}>
                  趨勢分析 (相比上一期間)
                </div>
                {topConditions.labels.map((label, index) => {
                  const trend = topConditions.trends[index];
                  if (!trend || trend.direction === 'none') return null;
                  
                  let arrow = '';
                  let color = '';
                  let text = '';
                  
                  if (trend.direction === 'up') {
                    arrow = '↗️';
                    color = '#dc2626';
                    text = `上升 ${Math.abs(trend.change)}%`;
                  } else if (trend.direction === 'down') {
                    arrow = '↘️';
                    color = '#16a34a';
                    text = `下降 ${Math.abs(trend.change)}%`;
                  } else if (trend.direction === 'stable') {
                    arrow = '→';
                    color = '#6b7280';
                    text = '穩定';
                  } else if (trend.direction === 'new') {
                    arrow = '✨';
                    color = '#2563eb';
                    text = '新增';
                  }
                  
                  return (
                    <div key={index} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      padding: '4px 0',
                      fontSize: '12px'
                    }}>
                      <span style={{ 
                        minWidth: '25px',
                        fontSize: '16px'
                      }}>{arrow}</span>
                      <span style={{ 
                        flex: 1,
                        color: '#4b5563',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>{label}</span>
                      <span style={{ 
                        color: color,
                        fontWeight: '500',
                        marginLeft: '10px'
                      }}>{text}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          // Comparison mode - two charts side by side
          <>
            <div className="chart-container">
              <div className="chart-header">
                <h3 className="chart-title">前五大診斷 - 期間 A</h3>
                <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '5px' }}>
                  {trendStartYear} - {trendEndYear}
                </p>
              </div>
              <div style={{ height: '250px' }}>
                <Bar data={barChartData} options={barChartOptions} />
              </div>
              <div style={{ marginTop: '10px', padding: '8px', backgroundColor: '#eff6ff', borderRadius: '6px', fontSize: '12px' }}>
                <strong>總計：</strong>{topConditions?.total?.toLocaleString() || 0} 人次
              </div>
            </div>

            <div className="chart-container">
              <div className="chart-header">
                <h3 className="chart-title">前五大診斷 - 期間 B</h3>
                <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '5px' }}>
                  {compareStartYear} - {compareEndYear}
                </p>
              </div>
              <div style={{ height: '250px' }}>
                <Bar data={compareBarChartData} options={barChartOptions} />
              </div>
              <div style={{ marginTop: '10px', padding: '8px', backgroundColor: '#fff7ed', borderRadius: '6px', fontSize: '12px' }}>
                <strong>總計：</strong>{compareTopConditions?.total?.toLocaleString() || 0} 人次
              </div>
            </div>
          </>
        )}
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 style={{ marginBottom: '20px' }}>最近活動</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>時間</th>
                <th>類型</th>
                <th>描述</th>
                <th>狀態</th>
              </tr>
            </thead>
            <tbody>
              {recentActivities.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', color: '#999' }}>
                    尚無活動記錄
                  </td>
                </tr>
              ) : (
                recentActivities.map((activity, index) => (
                  <tr key={index}>
                    <td>{activity.time}</td>
                    <td><span className={`badge ${activity.type === 'ETL' ? 'primary' : 'info'}`}>{activity.type}</span></td>
                    <td>{activity.description}</td>
                    <td><span className={`badge ${activity.statusBadge}`}>{activity.status}</span></td>
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

export default Dashboard;

