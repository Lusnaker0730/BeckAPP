import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';
import axios from 'axios';

// Mock axios
jest.mock('axios');

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
  Pie: () => <div data-testid="pie-chart">Pie Chart</div>,
}));

// Mock child components to simplify testing
jest.mock('../../utils/axiosConfig', () => axios);

describe('Dashboard Component', () => {
  const mockStats = {
    totalPatients: 100,
    totalConditions: 250,
    totalEncounters: 500,
    totalObservations: 1000,
    recentDiagnoses: []
  };

  beforeEach(() => {
    jest.clearAllMocks();
    axios.get = jest.fn().mockResolvedValue({ data: mockStats });
  });

  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
  };

  test('renders dashboard without crashing', () => {
    renderDashboard();
    // Just check it renders
    expect(true).toBe(true);
  });

  test('renders dashboard title or header', async () => {
    renderDashboard();
    
    await waitFor(() => {
      // Check for any text that indicates it's a dashboard
      const elements = screen.getAllByText(/dashboard|統計|overview/i);
      expect(elements.length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  test('makes API call on component mount', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalled();
    }, { timeout: 3000 });
  });
});
