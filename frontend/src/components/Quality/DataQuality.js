import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale
} from 'chart.js';
import { Bar, Line, Doughnut, Radar } from 'react-chartjs-2';
import './DataQuality.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
);

const DataQuality = () => {
  const [overview, setOverview] = useState(null);
  const [completeness, setCompleteness] = useState([]);
  const [consistency, setConsistency] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [timeliness, setTimeliness] = useState(null);
  const [issues, setIssues] = useState([]);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTab, setSelectedTab] = useState('overview');

  useEffect(() => {
    fetchQualityData();
  }, []);

  const fetchQualityData = async () => {
    setLoading(true);
    try {
      // Fetch all quality metrics
      const [
        overviewRes,
        completenessRes,
        consistencyRes,
        accuracyRes,
        timelinessRes,
        issuesRes,
        trendsRes
      ] = await Promise.all([
        axios.get('/api/data-quality/overview'),
        axios.get('/api/data-quality/completeness'),
        axios.get('/api/data-quality/consistency'),
        axios.get('/api/data-quality/accuracy'),
        axios.get('/api/data-quality/timeliness'),
        axios.get('/api/data-quality/issues?limit=20'),
        axios.get('/api/data-quality/trends?days=30')
      ]);

      setOverview(overviewRes.data);
      setCompleteness(completenessRes.data);
      setConsistency(consistencyRes.data);
      setAccuracy(accuracyRes.data);
      setTimeliness(timelinessRes.data);
      setIssues(issuesRes.data.issues || []);
      setTrends(trendsRes.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching quality data:', err);
      setError('Failed to fetch data quality metrics');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.9) return '#4caf50';
    if (score >= 0.7) return '#ff9800';
    return '#f44336';
  };

  const getScoreLabel = (score) => {
    if (score >= 0.9) return 'Excellent';
    if (score >= 0.7) return 'Good';
    if (score >= 0.5) return 'Fair';
    return 'Poor';
  };

  // Quality Score Radar Chart
  const radarChartData = overview ? {
    labels: ['Completeness', 'Consistency', 'Accuracy', 'Timeliness'],
    datasets: [{
      label: 'Quality Score',
      data: [
        overview.metrics.completeness,
        overview.metrics.consistency,
        overview.metrics.accuracy,
        overview.metrics.timeliness
      ],
      backgroundColor: 'rgba(102, 126, 234, 0.2)',
      borderColor: 'rgba(102, 126, 234, 1)',
      borderWidth: 2,
      pointBackgroundColor: 'rgba(102, 126, 234, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
    }]
  } : null;

  const radarOptions = {
    scales: {
      r: {
        beginAtZero: true,
        max: 1,
        ticks: {
          stepSize: 0.2
        }
      }
    },
    plugins: {
      legend: {
        display: false
      }
    }
  };

  // Completeness Chart
  const completenessChartData = completeness.length > 0 ? {
    labels: completeness.map(c => c.table_name),
    datasets: [{
      label: 'Completeness Score',
      data: completeness.map(c => c.completeness_score * 100),
      backgroundColor: completeness.map(c => 
        c.completeness_score >= 0.9 ? 'rgba(76, 175, 80, 0.6)' :
        c.completeness_score >= 0.7 ? 'rgba(255, 152, 0, 0.6)' :
        'rgba(244, 67, 54, 0.6)'
      ),
      borderColor: completeness.map(c => 
        c.completeness_score >= 0.9 ? 'rgba(76, 175, 80, 1)' :
        c.completeness_score >= 0.7 ? 'rgba(255, 152, 0, 1)' :
        'rgba(244, 67, 54, 1)'
      ),
      borderWidth: 1
    }]
  } : null;

  // Trend Chart
  const trendChartData = trends ? {
    labels: trends.trends.map(t => new Date(t.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: 'Overall Score',
        data: trends.trends.map(t => t.overall_score * 100),
        borderColor: 'rgb(102, 126, 234)',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        tension: 0.4
      },
      {
        label: 'Completeness',
        data: trends.trends.map(t => t.completeness * 100),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        tension: 0.4
      },
      {
        label: 'Consistency',
        data: trends.trends.map(t => t.consistency * 100),
        borderColor: 'rgb(255, 159, 64)',
        backgroundColor: 'rgba(255, 159, 64, 0.1)',
        tension: 0.4
      }
    ]
  } : null;

  const trendOptions = {
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value) => value + '%'
        }
      }
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`
        }
      }
    }
  };

  if (loading && !overview) {
    return (
      <div className="quality-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading data quality metrics...</p>
        </div>
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="quality-container">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchQualityData} className="btn btn-primary">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="quality-container">
      <div className="quality-header">
        <div>
          <h1>📊 Data Quality Dashboard</h1>
          <p className="subtitle">Monitor and improve data quality across the platform</p>
        </div>
        <button onClick={fetchQualityData} className="btn btn-primary" disabled={loading}>
          {loading ? '🔄 Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Overall Quality Score */}
      {overview && (
        <div className="quality-score-section">
          <div className="score-card main-score">
            <div className="score-circle" style={{ borderColor: getScoreColor(overview.overall_score) }}>
              <div className="score-value">{(overview.overall_score * 100).toFixed(0)}</div>
              <div className="score-label">Overall Score</div>
              <div className="score-status">{getScoreLabel(overview.overall_score)}</div>
            </div>
          </div>

          <div className="stats-cards">
            <div className="stat-card">
              <div className="stat-icon">📝</div>
              <div className="stat-content">
                <div className="stat-value">{overview.total_records.toLocaleString()}</div>
                <div className="stat-label">Total Records</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">⚠️</div>
              <div className="stat-content">
                <div className="stat-value">{overview.quality_issues}</div>
                <div className="stat-label">Quality Issues</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">🕒</div>
              <div className="stat-content">
                <div className="stat-value">
                  {new Date(overview.last_updated).toLocaleString()}
                </div>
                <div className="stat-label">Last Updated</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="quality-tabs">
        <button
          className={`tab ${selectedTab === 'overview' ? 'active' : ''}`}
          onClick={() => setSelectedTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${selectedTab === 'metrics' ? 'active' : ''}`}
          onClick={() => setSelectedTab('metrics')}
        >
          Detailed Metrics
        </button>
        <button
          className={`tab ${selectedTab === 'issues' ? 'active' : ''}`}
          onClick={() => setSelectedTab('issues')}
        >
          Issues ({issues.length})
        </button>
        <button
          className={`tab ${selectedTab === 'trends' ? 'active' : ''}`}
          onClick={() => setSelectedTab('trends')}
        >
          Trends
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {selectedTab === 'overview' && overview && (
          <div className="overview-grid">
            <div className="chart-card">
              <h3>Quality Dimensions</h3>
              {radarChartData && <Radar data={radarChartData} options={radarOptions} />}
            </div>

            <div className="metrics-summary">
              <h3>Dimension Scores</h3>
              <div className="metric-item">
                <div className="metric-header">
                  <span>Completeness</span>
                  <span className="metric-score" style={{ color: getScoreColor(overview.metrics.completeness) }}>
                    {(overview.metrics.completeness * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${overview.metrics.completeness * 100}%`,
                      backgroundColor: getScoreColor(overview.metrics.completeness)
                    }}
                  ></div>
                </div>
              </div>

              <div className="metric-item">
                <div className="metric-header">
                  <span>Consistency</span>
                  <span className="metric-score" style={{ color: getScoreColor(overview.metrics.consistency) }}>
                    {(overview.metrics.consistency * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${overview.metrics.consistency * 100}%`,
                      backgroundColor: getScoreColor(overview.metrics.consistency)
                    }}
                  ></div>
                </div>
              </div>

              <div className="metric-item">
                <div className="metric-header">
                  <span>Accuracy</span>
                  <span className="metric-score" style={{ color: getScoreColor(overview.metrics.accuracy) }}>
                    {(overview.metrics.accuracy * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${overview.metrics.accuracy * 100}%`,
                      backgroundColor: getScoreColor(overview.metrics.accuracy)
                    }}
                  ></div>
                </div>
              </div>

              <div className="metric-item">
                <div className="metric-header">
                  <span>Timeliness</span>
                  <span className="metric-score" style={{ color: getScoreColor(overview.metrics.timeliness) }}>
                    {(overview.metrics.timeliness * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${overview.metrics.timeliness * 100}%`,
                      backgroundColor: getScoreColor(overview.metrics.timeliness)
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'metrics' && (
          <div className="metrics-grid">
            {/* Completeness */}
            <div className="metric-card">
              <h3>📝 Data Completeness</h3>
              {completenessChartData && (
                <Bar data={completenessChartData} options={{ 
                  scales: { y: { beginAtZero: true, max: 100 } },
                  plugins: { legend: { display: false } }
                }} />
              )}
              <div className="metric-details">
                {completeness.map(c => (
                  <div key={c.table_name} className="detail-item">
                    <strong>{c.table_name}</strong>
                    <span>{c.total_records.toLocaleString()} records</span>
                    <div className="missing-fields">
                      {Object.entries(c.missing_fields).map(([field, count]) => (
                        count > 0 && <span key={field} className="missing-badge">
                          {field}: {count} missing
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Consistency */}
            {consistency && (
              <div className="metric-card">
                <h3>🔗 Data Consistency</h3>
                <div className="stat-grid">
                  <div className="stat-box">
                    <div className="stat-number">{consistency.duplicate_patients}</div>
                    <div className="stat-text">Duplicate Patients</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number">{consistency.orphaned_records}</div>
                    <div className="stat-text">Orphaned Records</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number">{consistency.total_issues}</div>
                    <div className="stat-text">Total Issues</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number" style={{ color: getScoreColor(consistency.consistency_score) }}>
                      {(consistency.consistency_score * 100).toFixed(0)}%
                    </div>
                    <div className="stat-text">Consistency Score</div>
                  </div>
                </div>
              </div>
            )}

            {/* Accuracy */}
            {accuracy && (
              <div className="metric-card">
                <h3>✓ Data Accuracy</h3>
                <div className="stat-grid">
                  <div className="stat-box">
                    <div className="stat-number">{accuracy.invalid_dates}</div>
                    <div className="stat-text">Invalid Dates</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number">{accuracy.invalid_codes}</div>
                    <div className="stat-text">Invalid Codes</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number">{accuracy.outliers}</div>
                    <div className="stat-text">Outliers</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number" style={{ color: getScoreColor(accuracy.accuracy_score) }}>
                      {(accuracy.accuracy_score * 100).toFixed(0)}%
                    </div>
                    <div className="stat-text">Accuracy Score</div>
                  </div>
                </div>
              </div>
            )}

            {/* Timeliness */}
            {timeliness && (
              <div className="metric-card">
                <h3>⏰ Data Timeliness</h3>
                <div className="stat-grid">
                  <div className="stat-box">
                    <div className="stat-number">{timeliness.avg_ingestion_delay_hours.toFixed(1)}h</div>
                    <div className="stat-text">Avg Ingestion Delay</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number">{timeliness.stale_records_count}</div>
                    <div className="stat-text">Stale Records</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number">
                      {timeliness.last_update ? new Date(timeliness.last_update).toLocaleDateString() : 'N/A'}
                    </div>
                    <div className="stat-text">Last Update</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-number" style={{ color: getScoreColor(timeliness.timeliness_score) }}>
                      {(timeliness.timeliness_score * 100).toFixed(0)}%
                    </div>
                    <div className="stat-text">Timeliness Score</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {selectedTab === 'issues' && (
          <div className="issues-container">
            <h3>Quality Issues</h3>
            {issues.length === 0 ? (
              <div className="no-issues">
                <p>✨ No data quality issues detected!</p>
              </div>
            ) : (
              <div className="issues-list">
                {issues.map(issue => (
                  <div key={issue.id} className={`issue-card severity-${issue.severity}`}>
                    <div className="issue-header">
                      <span className={`severity-badge ${issue.severity}`}>
                        {issue.severity.toUpperCase()}
                      </span>
                      <span className="issue-type">{issue.issue_type}</span>
                    </div>
                    <div className="issue-body">
                      <p className="issue-description">{issue.description}</p>
                      <div className="issue-meta">
                        <span>Table: {issue.table_name}</span>
                        {issue.record_id && <span>Record: {issue.record_id}</span>}
                        <span>Detected: {new Date(issue.detected_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {selectedTab === 'trends' && trends && (
          <div className="trends-container">
            <h3>Quality Trends (Last 30 Days)</h3>
            <div className="chart-wrapper">
              {trendChartData && <Line data={trendChartData} options={trendOptions} />}
            </div>
            <div className="trend-insights">
              <h4>Insights</h4>
              <ul>
                <li>Overall data quality has been {overview.overall_score >= 0.8 ? 'stable' : 'improving'}</li>
                <li>Completeness is the {overview.metrics.completeness >= 0.9 ? 'strongest' : 'needs attention'}</li>
                <li>{issues.length > 0 ? `${issues.length} issues need resolution` : 'No critical issues detected'}</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataQuality;

