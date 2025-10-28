import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';
import axios from 'axios';

// Mock axios
jest.mock('axios');

// Mock child components
jest.mock('../../utils/axiosConfig', () => ({
  __esModule: true,
  default: axios,
}));

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    axios.get.mockResolvedValue({
      data: {
        totalPatients: 100,
        totalConditions: 250,
        totalEncounters: 500,
        totalObservations: 1000
      }
    });
  });

  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
  };

  test('renders dashboard title', () => {
    renderDashboard();
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  test('loads and displays statistics', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument(); // Total Patients
      expect(screen.getByText('250')).toBeInTheDocument(); // Total Conditions
    });
  });

  test('shows loading state initially', () => {
    axios.get.mockImplementationOnce(() => new Promise(() => {})); // Never resolves
    
    renderDashboard();
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test('shows error state on API failure', async () => {
    axios.get.mockRejectedValueOnce(new Error('API Error'));
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  test('makes API call on component mount', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/analytics/stats')
      );
    });
  });
});

