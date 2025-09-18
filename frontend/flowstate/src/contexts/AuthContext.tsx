'use client';
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';

// Update User interface to match backend response
interface User {
  id: string; // Changed from number to string to match backend UUID
  name: string;
  email: string;
  notion_connected?: boolean;
  google_calendar_connected?: boolean;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
          setLoading(false);
          return;
        }

        // BACKDOOR FOR TESTING - Check for mock token
        if (token === 'mock-test-token-123') {
          const mockUser: User = {
            id: 'test-user-123',
            name: 'Test User',
            email: 'test@flowstate.dev',
            notion_connected: false,
            google_calendar_connected: false,
          };
          setUser(mockUser);
          setLoading(false);
          return;
        }

        const response = await fetch('/api/auth/user', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          localStorage.removeItem('accessToken');
        }
      } catch (error) {
        console.error('Authentication error:', error);
        localStorage.removeItem('accessToken');
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      // BACKDOOR FOR TESTING - Remove this when database is available
      if (email === 'test@flowstate.dev' && password === 'testpass123') {
        // Mock user data for testing
        const mockUser: User = {
          id: 'test-user-123',
          name: 'Test User',
          email: 'test@flowstate.dev',
          notion_connected: false,
          google_calendar_connected: false,
        };

        // Set mock token
        localStorage.setItem('accessToken', 'mock-test-token-123');
        setUser(mockUser);
        setLoading(false);
        return;
      }

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Login failed');
      }

      const data = await response.json();
      localStorage.setItem('accessToken', data.token);
      setUser(data.user);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    setLoading(true);
    try {
      // BACKDOOR FOR TESTING - Allow test signup without database
      if (email === 'test@flowstate.dev' || email.includes('test')) {
        const mockUser: User = {
          id: 'test-user-123',
          name: name || 'Test User',
          email: email,
          notion_connected: false,
          google_calendar_connected: false,
        };

        localStorage.setItem('accessToken', 'mock-test-token-123');
        setUser(mockUser);
        setLoading(false);
        return;
      }

      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Signup failed');
      }

      const data = await response.json();
      localStorage.setItem('accessToken', data.token);
      setUser(data.user);
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      localStorage.removeItem('accessToken');
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    logout,
    signup,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthProvider;
