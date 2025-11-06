import { render, screen } from '@testing-library/react';
import App from './App';

// Mock all child components to avoid deep dependencies
jest.mock('./components/Auth/Login', () => {
  return function MockLogin() {
    return <div data-testid="mock-login">Login Component</div>;
  };
});

jest.mock('./components/Dashboard/Dashboard', () => {
  return function MockDashboard() {
    return <div data-testid="mock-dashboard">Dashboard Component</div>;
  };
});

jest.mock('./components/Analysis/DiagnosisAnalysis', () => {
  return function MockDiagnosisAnalysis() {
    return <div>Diagnosis Analysis</div>;
  };
});

jest.mock('./components/Visualization/DataVisualization', () => {
  return function MockDataVisualization() {
    return <div>Data Visualization</div>;
  };
});

jest.mock('./components/Export/DataExport', () => {
  return function MockDataExport() {
    return <div>Data Export</div>;
  };
});

jest.mock('./components/Admin/AdminPanel', () => {
  return function MockAdminPanel() {
    return <div>Admin Panel</div>;
  };
});

jest.mock('./components/Survival/SurvivalAnalysis', () => {
  return function MockSurvivalAnalysis() {
    return <div>Survival Analysis</div>;
  };
});

jest.mock('./components/AuditLogs/AuditLogs', () => {
  return function MockAuditLogs() {
    return <div>Audit Logs</div>;
  };
});

jest.mock('./components/Cohort/CohortAnalysis', () => {
  return function MockCohortAnalysis() {
    return <div>Cohort Analysis</div>;
  };
});

jest.mock('./components/Quality/DataQuality', () => {
  return function MockDataQuality() {
    return <div>Data Quality</div>;
  };
});

describe('App Component', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  test('renders without crashing', () => {
    render(<App />);
    expect(true).toBe(true);
  });

  test('renders application', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
  });
});
