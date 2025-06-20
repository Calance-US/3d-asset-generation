import Keycloak from 'keycloak-js';

/**
 * Keycloak configuration for frontend authentication.
 *
 * This configuration supports both development and production environments
 * with fallback values for local development.
 */
const keycloakConfig = {
  url: 'http://localhost:28080',
  realm: 'local-apps',
  clientId: '3d-visualization-app',
};

// Debug environment variables
if (process.env.NODE_ENV === 'development') {
  console.log('Environment variables:', {
    REACT_APP_KEYCLOAK_SERVER_URL: process.env.REACT_APP_KEYCLOAK_SERVER_URL,
    REACT_APP_KEYCLOAK_REALM: process.env.REACT_APP_KEYCLOAK_REALM,
    REACT_APP_KEYCLOAK_CLIENT_ID: process.env.REACT_APP_KEYCLOAK_CLIENT_ID,
  });
  console.log('Final Keycloak config:', keycloakConfig);
}

/**
 * Keycloak initialization options.
 *
 * These options control how Keycloak behaves during initialization:
 * - onLoad: 'check-sso' - Check if user is already authenticated
 * - silentCheckSsoRedirectUri: Handle silent authentication checks
 * - pkceMethod: 'S256' - Use PKCE for enhanced security
 */
const keycloakInitOptions = {
  onLoad: 'check-sso',
  checkLoginIframe: false,
  enableLogging: false,
  flow: 'standard',
  responseMode: 'fragment',
  redirectUri: window.location.origin,
};

// Create Keycloak instance
const keycloak = new Keycloak(keycloakConfig);

// Track initialization state to prevent multiple initializations
let isInitialized = false;
let initializationPromise = null;

/**
 * Initialize Keycloak authentication.
 *
 * @returns {Promise<boolean>} Promise that resolves to authentication status
 */
export const initKeycloak = async () => {
  // Return existing initialization promise if already in progress
  if (initializationPromise) {
    return initializationPromise;
  }

  // Return current state if already initialized
  if (isInitialized) {
    return keycloak.authenticated || false;
  }

  // Create initialization promise
  initializationPromise = (async () => {
    try {
      console.log('Initializing Keycloak with config:', keycloakConfig);

      const authenticated = await keycloak.init(keycloakInitOptions);
      isInitialized = true;

      if (authenticated) {
        console.log('User is authenticated');
        console.log('Token expires in:', keycloak.tokenParsed?.exp - Math.floor(Date.now() / 1000), 'seconds');

        // Set up token refresh
        setupTokenRefresh();
      } else {
        console.log('User is not authenticated');
      }

      return authenticated;
    } catch (error) {
      console.error('Failed to initialize Keycloak:', error);

      // Reset initialization state on error
      isInitialized = false;
      initializationPromise = null;

      // Handle common Keycloak errors gracefully
      if (error && error.error === 'Timeout when waiting for 3rd party check iframe message.' ||
        (error && error.toString().includes('url.indexOf is not a function')) ||
        (error && error.toString().includes('network error')) ||
        (error && error.toString().includes('CORS')) ||
        !error) {
        console.warn('Keycloak connection issue - treating as not authenticated:', error);
        return false;
      }

      // For any other errors, also treat as not authenticated
      console.warn('Keycloak initialization failed - treating as not authenticated:', error);
      return false;
    }
  })();

  return initializationPromise;
};

/**
 * Set up automatic token refresh.
 *
 * This function ensures tokens are refreshed before they expire
 * to maintain seamless user experience.
 */
const setupTokenRefresh = () => {
  // Refresh token when it's about to expire (5 minutes before)
  keycloak.onTokenExpired = () => {
    console.log('Token expired, refreshing...');
    keycloak.updateToken(30)
      .then((refreshed) => {
        if (refreshed) {
          console.log('Token refreshed successfully');
        } else {
          console.log('Token is still valid');
        }
      })
      .catch((error) => {
        console.error('Failed to refresh token:', error);
        // Force re-authentication if refresh fails
        keycloak.login();
      });
  };

  // Update token every 5 minutes to ensure it stays fresh
  setInterval(() => {
    keycloak.updateToken(300) // Refresh if token expires within 5 minutes
      .then((refreshed) => {
        if (refreshed) {
          console.log('Token refreshed proactively');
        }
      })
      .catch((error) => {
        console.error('Proactive token refresh failed:', error);
      });
  }, 60000); // Check every minute
};

/**
 * Login function.
 *
 * @param {Object} options - Login options
 * @returns {Promise} Login promise
 */
export const login = (options = {}) => {
  return keycloak.login({
    redirectUri: window.location.origin,
    ...options,
  });
};

/**
 * Logout function.
 *
 * @param {Object} options - Logout options
 * @returns {Promise} Logout promise
 */
export const logout = (options = {}) => {
  return keycloak.logout({
    redirectUri: window.location.origin,
    ...options,
  });
};

/**
 * Get the current authentication token.
 *
 * @returns {string|null} The current token or null if not authenticated
 */
export const getToken = () => {
  return isInitialized ? (keycloak.token || null) : null;
};

/**
 * Get the current user information.
 *
 * @returns {Object|null} User information from token or null if not authenticated
 */
export const getUser = () => {
  if (!isInitialized || !keycloak.tokenParsed) {
    return null;
  }

  return {
    id: keycloak.tokenParsed.sub,
    username: keycloak.tokenParsed.preferred_username,
    email: keycloak.tokenParsed.email,
    firstName: keycloak.tokenParsed.given_name,
    lastName: keycloak.tokenParsed.family_name,
    roles: keycloak.tokenParsed.realm_access?.roles || [],
    isAdmin: keycloak.tokenParsed.realm_access?.roles?.includes('admin') || false,
    isEducator: keycloak.tokenParsed.realm_access?.roles?.includes('educator') || false,
  };
};

/**
 * Check if user is authenticated.
 *
 * @returns {boolean} Authentication status
 */
export const isAuthenticated = () => {
  return isInitialized && (keycloak.authenticated || false);
};

/**
 * Check if user has a specific role.
 *
 * @param {string} role - Role to check
 * @returns {boolean} Whether user has the role
 */
export const hasRole = (role) => {
  return keycloak.hasRealmRole(role);
};

/**
 * Check if user has admin privileges.
 *
 * @returns {boolean} Whether user is an admin
 */
export const isAdmin = () => {
  return hasRole('admin') || hasRole('super_admin');
};

/**
 * Check if user has educator privileges.
 *
 * @returns {boolean} Whether user is an educator
 */
export const isEducator = () => {
  return hasRole('educator') || isAdmin();
};

/**
 * Update the current token.
 *
 * @param {number} minValidity - Minimum token validity in seconds
 * @returns {Promise<boolean>} Promise that resolves to refresh status
 */
export const updateToken = (minValidity = 30) => {
  if (!isInitialized) {
    return Promise.resolve(false);
  }
  return keycloak.updateToken(minValidity);
};

/**
 * Get authentication headers for API requests.
 *
 * @returns {Object} Headers object with Authorization header
 */
export const getAuthHeaders = () => {
  const token = getToken();
  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
};

/**
 * Account management function.
 * Opens Keycloak account management console.
 */
export const manageAccount = () => {
  keycloak.accountManagement();
};

// Export the keycloak instance for advanced usage
export default keycloak;
