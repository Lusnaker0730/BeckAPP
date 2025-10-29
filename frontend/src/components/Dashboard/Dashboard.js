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
  Legend
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

  useEffect(() => {
    fetchEtlJobs();
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedJobId, trendStartYear, trendEndYear]);

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
    },
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
            <Line data={lineChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-container">
          <div className="chart-header">
            <h3 className="chart-title">前五大診斷</h3>
            <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '5px' }}>
              {trendStartYear} - {trendEndYear}
            </p>
          </div>
          <div style={{ height: '300px' }}>
            <Bar data={barChartData} options={chartOptions} />
          </div>
        </div>
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

