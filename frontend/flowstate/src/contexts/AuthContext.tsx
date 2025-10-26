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

  // Helper function to get token from localStorage or cookie
  const getAuthToken = (): string | null => {
    // Try localStorage first
    let token = localStorage.getItem('accessToken');

    // If not in localStorage, try cookie (useful after OAuth redirect)
    if (!token) {
      const cookies = document.cookie.split(';');
      for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'accessToken') {
          token = value;
          // Restore to localStorage for future use
          if (token) {
            localStorage.setItem('accessToken', token);
          }
          break;
        }
      }
    }

    return token;
  };

  useEffect(() => {
    // Check if user is already logged in
    const checkAuthStatus = async () => {
      try {
        const token = getAuthToken();
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
          // Also clear cookie
          document.cookie = 'accessToken=; path=/; max-age=0';
        }
      } catch (error) {
        console.error('Authentication error:', error);
        localStorage.removeItem('accessToken');
        // Also clear cookie
        document.cookie = 'accessToken=; path=/; max-age=0';
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Helper function to store token in both localStorage and cookie
  const storeAuthToken = (token: string) => {
    localStorage.setItem('accessToken', token);
    // Also store in cookie for OAuth redirect persistence
    // Cookie expires in 7 days, httpOnly is false (client-side access needed)
    document.cookie = `accessToken=${token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        const error = new Error(data.detail) as Error & {
          code?: string;
        };

        if (data.code) {
          error.code = data.code;
        }
        console.log('Error was: ' + data.code);
        throw error;
      }

      const data = await response.json();
      storeAuthToken(data.token);
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

      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        const error = new Error(data.detail) as Error & {
          code?: string;
        };

        if (data.code) {
          error.code = data.code;
        }
        console.log('Error was: ' + data.message);
        throw error;
      }


      const data = await response.json();
      storeAuthToken(data.token);
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
      // Also clear the cookie
      document.cookie = 'accessToken=; path=/; max-age=0';
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
