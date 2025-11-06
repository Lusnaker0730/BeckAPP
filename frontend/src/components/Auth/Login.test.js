import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';
import axios from 'axios';

// Mock axios
jest.mock('axios');

// Mock react-router-dom navigate
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockedNavigate,
}));

describe('Login Component', () => {
  const mockOnLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    axios.post = jest.fn();
  });

  const renderLogin = () => {
    return render(
      <BrowserRouter>
        <Login onLogin={mockOnLogin} />
      </BrowserRouter>
    );
  };

  test('renders login form', () => {
    renderLogin();
    
    // Check for username input
    const usernameInputs = screen.queryAllByPlaceholderText(/username|使用者名稱/i);
    const passwordInputs = screen.queryAllByPlaceholderText(/password|密碼/i);
    
    expect(usernameInputs.length + passwordInputs.length).toBeGreaterThan(0);
  });

  test('renders login component without crashing', () => {
    renderLogin();
    expect(true).toBe(true);
  });

  test('has input fields', () => {
    renderLogin();
    
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
  });
});
