import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  initKeycloak,
  login,
  logout,
  getUser,
  isAuthenticated,
  hasRole,
  isAdmin,
  isEducator,
  getToken,
  getAuthHeaders,
  manageAccount
} from '../lib/keycloak';

/**
 * Authentication context for managing user authentication state.
 *
 * This context provides:
 * - Authentication status
 * - User information
 * - Login/logout functions
 * - Role checking utilities
 * - Loading states
 */
const AuthContext = createContext(null);

/**
 * Authentication provider component.
 *
 * Wraps the application and provides authentication state and methods
 * to all child components.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 */
export const AuthProvider = ({ children }) => {
  const [isAuthInitialized, setIsAuthInitialized] = useState(false);
  const [isUserAuthenticated, setIsUserAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [authError, setAuthError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if authentication is disabled via environment variable
  const isAuthDisabled = process.env.REACT_APP_DISABLE_AUTH === 'true';

  /**
   * Initialize authentication on component mount.
   */
  useEffect(() => {
    const initAuth = async () => {
      try {
        setIsLoading(true);
        setAuthError(null);

        // If authentication is disabled, skip Keycloak initialization
        if (isAuthDisabled) {
          console.log('Authentication disabled - skipping Keycloak initialization');
          setIsAuthInitialized(true);
          setIsUserAuthenticated(false);
          setUser(null);
          setIsLoading(false);
          return;
        }

        console.log('Initializing authentication...');

        const authenticated = await initKeycloak();

        setIsAuthInitialized(true);
        setIsUserAuthenticated(authenticated);

        if (authenticated) {
          const userInfo = getUser();
          setUser(userInfo);
          console.log('User authenticated:', userInfo);
        } else {
          setUser(null);
          console.log('User not authenticated');
        }

      } catch (error) {
        console.error('Authentication initialization failed:', error);
        setAuthError(error.message || 'Authentication initialization failed');
        setIsAuthInitialized(false);
        setIsUserAuthenticated(false);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [isAuthDisabled]);

  /**
   * Handle user login.
   *
   * @param {Object} options - Login options
   */
  const handleLogin = async (options = {}) => {
    try {
      setAuthError(null);
      await login(options);
    } catch (error) {
      console.error('Login failed:', error);
      setAuthError(error.message || 'Login failed');
    }
  };

  /**
   * Handle user logout.
   *
   * @param {Object} options - Logout options
   */
  const handleLogout = async (options = {}) => {
    try {
      setAuthError(null);
      await logout(options);

      // Clear local state
      setIsUserAuthenticated(false);
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
      setAuthError(error.message || 'Logout failed');
    }
  };

  /**
   * Refresh user information.
   */
  const refreshUser = () => {
    if (isAuthenticated()) {
      const userInfo = getUser();
      setUser(userInfo);
      setIsUserAuthenticated(true);
    } else {
      setUser(null);
      setIsUserAuthenticated(false);
    }
  };

  /**
   * Check if user has a specific role.
   *
   * @param {string} role - Role to check
   * @returns {boolean} Whether user has the role
   */
  const checkRole = (role) => {
    return hasRole(role);
  };

  /**
   * Check if user has admin privileges.
   *
   * @returns {boolean} Whether user is an admin
   */
  const checkIsAdmin = () => {
    return isAdmin();
  };

  /**
   * Check if user has educator privileges.
   *
   * @returns {boolean} Whether user is an educator
   */
  const checkIsEducator = () => {
    return isEducator();
  };

  /**
   * Get authentication token.
   *
   * @returns {string|null} Current authentication token
   */
  const getAuthToken = () => {
    return getToken();
  };

  /**
   * Get authentication headers for API requests.
   *
   * @returns {Object} Headers object with Authorization header
   */
  const getHeaders = () => {
    return getAuthHeaders();
  };

  /**
   * Open account management console.
   */
  const openAccountManagement = () => {
    manageAccount();
  };

  // Context value object
  const contextValue = {
    // State
    isAuthInitialized,
    isAuthenticated: isUserAuthenticated,
    user,
    authError,
    isLoading,
    isAuthDisabled,

    // Actions
    login: handleLogin,
    logout: handleLogout,
    refreshUser,
    manageAccount: openAccountManagement,

    // Utilities
    hasRole: checkRole,
    isAdmin: checkIsAdmin,
    isEducator: checkIsEducator,
    getToken: getAuthToken,
    getAuthHeaders: getHeaders,

    // Helper computed properties
    isStudent: user?.roles?.includes('student') || (!checkIsAdmin() && !checkIsEducator()),
    userRoles: user?.roles || [],
    displayName: user?.firstName && user?.lastName
      ? `${user.firstName} ${user.lastName}`
      : user?.username || user?.email || 'User',
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Hook to access authentication context.
 *
 * @returns {Object} Authentication context value
 * @throws {Error} If used outside of AuthProvider
 */
export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};

/**
 * Hook to check if authentication is ready.
 *
 * @returns {boolean} Whether authentication is initialized and ready
 */
export const useAuthReady = () => {
  const { isAuthInitialized, isLoading } = useAuth();
  return isAuthInitialized && !isLoading;
};

/**
 * Hook to get current user with type safety.
 *
 * @returns {Object|null} Current user object or null
 */
export const useCurrentUser = () => {
  const { user, isAuthenticated } = useAuth();
  return isAuthenticated ? user : null;
};

/**
 * Hook for role-based access control.
 *
 * @param {string|string[]} requiredRoles - Required role(s)
 * @returns {boolean} Whether user has required role(s)
 */
export const useHasRole = (requiredRoles) => {
  const { hasRole } = useAuth();

  if (Array.isArray(requiredRoles)) {
    return requiredRoles.some(role => hasRole(role));
  }

  return hasRole(requiredRoles);
};

/**
 * Hook for admin access control.
 *
 * @returns {boolean} Whether user has admin privileges
 */
export const useIsAdmin = () => {
  const { isAdmin } = useAuth();
  return isAdmin();
};

/**
 * Hook for educator access control.
 *
 * @returns {boolean} Whether user has educator privileges
 */
export const useIsEducator = () => {
  const { isEducator } = useAuth();
  return isEducator();
};

export default AuthContext;
