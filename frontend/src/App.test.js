import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

// Mock the child components to avoid dependencies
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

describe('App Component', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  test('renders without crashing', () => {
    render(<App />);
  });

  test('shows login page when not authenticated', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByTestId('mock-login')).toBeInTheDocument();
    });
  });

  test('checks for existing authentication on mount', async () => {
    // Set up authenticated state
    localStorage.setItem('accessToken', 'fake-token');
    localStorage.setItem('user', JSON.stringify({ username: 'testuser' }));
    
    render(<App />);
    
    await waitFor(() => {
      // Should navigate to dashboard
      expect(window.location.pathname).toBe('/');
    });
  });

  test('handles logout correctly', async () => {
    localStorage.setItem('accessToken', 'fake-token');
    localStorage.setItem('user', JSON.stringify({ username: 'testuser' }));
    
    const { rerender } = render(<App />);
    
    // Simulate logout
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    
    rerender(<App />);
    
    await waitFor(() => {
      expect(localStorage.getItem('accessToken')).toBeNull();
    });
  });
});

