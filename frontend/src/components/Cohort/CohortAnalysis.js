import React, { useState, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import './Cohort.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const CohortAnalysis = () => {
  const [cohorts, setCohorts] = useState([]);
  const [selectedCohort, setSelectedCohort] = useState(null);
  const [cohortStats, setCohortStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Create cohort form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [cohortForm, setCohortForm] = useState({
    name: '',
    description: '',
    criteria: {
      age_min: '',
      age_max: '',
      gender: '',
      conditions: [],
      date_range_start: '',
      date_range_end: ''
    }
  });
  
  // Comparison mode
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedCohorts, setSelectedCohorts] = useState([]);
  const [comparisonResults, setComparisonResults] = useState(null);

  useEffect(() => {
    fetchCohorts();
  }, []);

  useEffect(() => {
    if (selectedCohort) {
      fetchCohortStats(selectedCohort.id);
    }
  }, [selectedCohort]);

  const fetchCohorts = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/cohort/cohorts');
      setCohorts(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching cohorts:', err);
      setError('Failed to fetch cohorts');
    } finally {
      setLoading(false);
    }
  };

  const fetchCohortStats = async (cohortId) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/cohort/cohorts/${cohortId}/stats`);
      setCohortStats(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching cohort stats:', err);
      setError('Failed to fetch cohort statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCohort = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Clean up criteria - remove empty fields
      const cleanedCriteria = {};
      Object.keys(cohortForm.criteria).forEach(key => {
        const value = cohortForm.criteria[key];
        if (value !== '' && value !== null && !(Array.isArray(value) && value.length === 0)) {
          cleanedCriteria[key] = value;
        }
      });
      
      const payload = {
        name: cohortForm.name,
        description: cohortForm.description || null,
        criteria: cleanedCriteria
      };
      
      await axios.post('/api/cohort/cohorts', payload);
      
      // Reset form and refresh list
      setCohortForm({
        name: '',
        description: '',
        criteria: {
          age_min: '',
          age_max: '',
          gender: '',
          conditions: [],
          date_range_start: '',
          date_range_end: ''
        }
      });
      setShowCreateForm(false);
      fetchCohorts();
      setError(null);
    } catch (err) {
      console.error('Error creating cohort:', err);
      setError(err.response?.data?.detail || 'Failed to create cohort');
    } finally {
      setLoading(false);
    }
  };

  const handleCompareCohorts = async () => {
    if (selectedCohorts.length < 2) {
      setError('Please select at least 2 cohorts to compare');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post('/api/cohort/cohorts/compare', {
        name: `Comparison ${new Date().toISOString().split('T')[0]}`,
        cohort_ids: selectedCohorts,
        analysis_type: 'demographics'
      });
      
      setComparisonResults(response.data.results);
      setError(null);
    } catch (err) {
      console.error('Error comparing cohorts:', err);
      setError('Failed to compare cohorts');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCohort = async (cohortId) => {
    if (!window.confirm('Are you sure you want to delete this cohort?')) {
      return;
    }
    
    try {
      await axios.delete(`/api/cohort/cohorts/${cohortId}`);
      
      fetchCohorts();
      if (selectedCohort?.id === cohortId) {
        setSelectedCohort(null);
        setCohortStats(null);
      }
    } catch (err) {
      console.error('Error deleting cohort:', err);
      setError('Failed to delete cohort');
    }
  };

  const toggleCohortSelection = (cohortId) => {
    setSelectedCohorts(prev => {
      if (prev.includes(cohortId)) {
        return prev.filter(id => id !== cohortId);
      } else if (prev.length < 5) {
        return [...prev, cohortId];
      } else {
        setError('Maximum 5 cohorts can be compared');
        return prev;
      }
    });
  };

  // Chart data for gender distribution
  const genderChartData = cohortStats ? {
    labels: Object.keys(cohortStats.gender_distribution),
    datasets: [{
      label: 'Gender Distribution',
      data: Object.values(cohortStats.gender_distribution),
      backgroundColor: [
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 99, 132, 0.6)',
        'rgba(255, 206, 86, 0.6)'
      ],
      borderColor: [
        'rgba(54, 162, 235, 1)',
        'rgba(255, 99, 132, 1)',
        'rgba(255, 206, 86, 1)'
      ],
      borderWidth: 1
    }]
  } : null;

  // Chart data for age distribution
  const ageChartData = cohortStats ? {
    labels: Object.keys(cohortStats.age_distribution),
    datasets: [{
      label: 'Patients',
      data: Object.values(cohortStats.age_distribution),
      backgroundColor: 'rgba(75, 192, 192, 0.6)',
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 1
    }]
  } : null;

  // Chart data for top conditions
  const conditionsChartData = cohortStats ? {
    labels: cohortStats.top_conditions.map(c => c.condition),
    datasets: [{
      label: 'Condition Count',
      data: cohortStats.top_conditions.map(c => c.count),
      backgroundColor: 'rgba(153, 102, 255, 0.6)',
      borderColor: 'rgba(153, 102, 255, 1)',
      borderWidth: 1
    }]
  } : null;

  return (
    <div className="cohort-analysis-container">
      <div className="cohort-header">
        <h1>👥 Patient Cohort Analysis</h1>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? '❌ Cancel' : '➕ Create New Cohort'}
          </button>
          <button 
            className={`btn ${comparisonMode ? 'btn-warning' : 'btn-secondary'}`}
            onClick={() => {
              setComparisonMode(!comparisonMode);
              setSelectedCohorts([]);
              setComparisonResults(null);
            }}
          >
            {comparisonMode ? '📊 View Mode' : '🔍 Compare Mode'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {showCreateForm && (
        <div className="cohort-form-card">
          <h2>Create New Cohort</h2>
          <form onSubmit={handleCreateCohort}>
            <div className="form-group">
              <label>Cohort Name *</label>
              <input
                type="text"
                value={cohortForm.name}
                onChange={(e) => setCohortForm({...cohortForm, name: e.target.value})}
                placeholder="e.g., Diabetic Patients 2023"
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={cohortForm.description}
                onChange={(e) => setCohortForm({...cohortForm, description: e.target.value})}
                placeholder="Brief description of this cohort..."
                rows="3"
              />
            </div>

            <h3>Inclusion Criteria</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>Minimum Age</label>
                <input
                  type="number"
                  value={cohortForm.criteria.age_min}
                  onChange={(e) => setCohortForm({
                    ...cohortForm,
                    criteria: {...cohortForm.criteria, age_min: e.target.value ? parseInt(e.target.value) : ''}
                  })}
                  min="0"
                  max="120"
                  placeholder="e.g., 18"
                />
              </div>

              <div className="form-group">
                <label>Maximum Age</label>
                <input
                  type="number"
                  value={cohortForm.criteria.age_max}
                  onChange={(e) => setCohortForm({
                    ...cohortForm,
                    criteria: {...cohortForm.criteria, age_max: e.target.value ? parseInt(e.target.value) : ''}
                  })}
                  min="0"
                  max="120"
                  placeholder="e.g., 65"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Gender</label>
              <select
                value={cohortForm.criteria.gender}
                onChange={(e) => setCohortForm({
                  ...cohortForm,
                  criteria: {...cohortForm.criteria, gender: e.target.value}
                })}
              >
                <option value="">All</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Conditions (comma-separated)</label>
              <input
                type="text"
                placeholder="e.g., Diabetes, Hypertension"
                onChange={(e) => {
                  const conditions = e.target.value ? e.target.value.split(',').map(c => c.trim()) : [];
                  setCohortForm({
                    ...cohortForm,
                    criteria: {...cohortForm.criteria, conditions}
                  });
                }}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Start Date</label>
                <input
                  type="date"
                  value={cohortForm.criteria.date_range_start}
                  onChange={(e) => setCohortForm({
                    ...cohortForm,
                    criteria: {...cohortForm.criteria, date_range_start: e.target.value}
                  })}
                />
              </div>

              <div className="form-group">
                <label>End Date</label>
                <input
                  type="date"
                  value={cohortForm.criteria.date_range_end}
                  onChange={(e) => setCohortForm({
                    ...cohortForm,
                    criteria: {...cohortForm.criteria, date_range_end: e.target.value}
                  })}
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Creating...' : '✓ Create Cohort'}
              </button>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => setShowCreateForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="cohort-content">
        <div className="cohort-list">
          <h2>Saved Cohorts ({cohorts.length})</h2>
          {loading && cohorts.length === 0 ? (
            <div className="loading">Loading cohorts...</div>
          ) : cohorts.length === 0 ? (
            <div className="empty-state">
              <p>No cohorts created yet.</p>
              <p>Click "Create New Cohort" to get started!</p>
            </div>
          ) : (
            <div className="cohorts-grid">
              {cohorts.map(cohort => (
                <div 
                  key={cohort.id}
                  className={`cohort-card ${selectedCohort?.id === cohort.id ? 'active' : ''} ${
                    comparisonMode && selectedCohorts.includes(cohort.id) ? 'selected-for-comparison' : ''
                  }`}
                  onClick={() => {
                    if (comparisonMode) {
                      toggleCohortSelection(cohort.id);
                    } else {
                      setSelectedCohort(cohort);
                    }
                  }}
                >
                  {comparisonMode && (
                    <div className="comparison-checkbox">
                      <input 
                        type="checkbox" 
                        checked={selectedCohorts.includes(cohort.id)}
                        readOnly
                      />
                    </div>
                  )}
                  <h3>{cohort.name}</h3>
                  <p className="cohort-description">{cohort.description || 'No description'}</p>
                  <div className="cohort-meta">
                    <span className="patient-count">👤 {cohort.patient_count} patients</span>
                    <span className="created-date">
                      📅 {new Date(cohort.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {!comparisonMode && (
                    <div className="cohort-actions">
                      <button 
                        className="btn-icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteCohort(cohort.id);
                        }}
                        title="Delete cohort"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {comparisonMode && selectedCohorts.length >= 2 && (
            <button 
              className="btn btn-primary btn-compare"
              onClick={handleCompareCohorts}
              disabled={loading}
            >
              {loading ? 'Comparing...' : `Compare ${selectedCohorts.length} Cohorts`}
            </button>
          )}
        </div>

        {comparisonMode && comparisonResults ? (
          <div className="cohort-details">
            <h2>Comparison Results</h2>
            <div className="comparison-grid">
              {Object.entries(comparisonResults).map(([cohortName, data]) => (
                <div key={cohortName} className="comparison-card">
                  <h3>{cohortName}</h3>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="stat-label">Total Patients</span>
                      <span className="stat-value">{data.total_patients}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Average Age</span>
                      <span className="stat-value">{data.average_age} years</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Age Range</span>
                      <span className="stat-value">
                        {data.age_range.min} - {data.age_range.max}
                      </span>
                    </div>
                  </div>
                  <div className="gender-breakdown">
                    <strong>Gender Distribution:</strong>
                    {Object.entries(data.gender_distribution).map(([gender, count]) => (
                      <div key={gender}>
                        {gender}: {count} ({((count/data.total_patients)*100).toFixed(1)}%)
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : selectedCohort && cohortStats ? (
          <div className="cohort-details">
            <h2>{selectedCohort.name}</h2>
            <p className="details-description">{selectedCohort.description}</p>

            <div className="stats-summary">
              <div className="stat-card">
                <div className="stat-icon">👥</div>
                <div className="stat-content">
                  <div className="stat-value">{cohortStats.total_patients}</div>
                  <div className="stat-label">Total Patients</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">🏥</div>
                <div className="stat-content">
                  <div className="stat-value">{cohortStats.encounters_count}</div>
                  <div className="stat-label">Total Encounters</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-content">
                  <div className="stat-value">{cohortStats.avg_encounters_per_patient}</div>
                  <div className="stat-label">Avg Encounters/Patient</div>
                </div>
              </div>
            </div>

            <div className="charts-grid">
              <div className="chart-card">
                <h3>Gender Distribution</h3>
                {genderChartData && <Pie data={genderChartData} />}
              </div>

              <div className="chart-card">
                <h3>Age Distribution</h3>
                {ageChartData && <Bar data={ageChartData} />}
              </div>

              <div className="chart-card chart-card-wide">
                <h3>Top 5 Conditions</h3>
                {conditionsChartData && conditionsChartData.labels.length > 0 ? (
                  <Bar data={conditionsChartData} />
                ) : (
                  <p className="no-data">No condition data available</p>
                )}
              </div>
            </div>

            <div className="criteria-section">
              <h3>Inclusion Criteria</h3>
              <div className="criteria-grid">
                {Object.entries(selectedCohort.criteria).map(([key, value]) => {
                  if (!value || (Array.isArray(value) && value.length === 0)) return null;
                  return (
                    <div key={key} className="criteria-item">
                      <strong>{key.replace(/_/g, ' ').toUpperCase()}:</strong>
                      <span>{Array.isArray(value) ? value.join(', ') : value}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="cohort-details empty">
            <div className="empty-state-large">
              <h2>📊 Select a Cohort</h2>
              <p>Click on a cohort from the list to view detailed statistics and visualizations</p>
              {comparisonMode && (
                <p className="comparison-hint">
                  💡 <strong>Comparison Mode:</strong> Select 2-5 cohorts to compare their demographics
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CohortAnalysis;

