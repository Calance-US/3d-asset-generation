import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Navigate, useLocation } from 'react-router-dom';
import { cn } from '../../lib/utils';

/**
 * Login page component for user authentication.
 *
 * This component provides a login interface and handles authentication
 * redirects. It integrates with Keycloak for SSO authentication.
 */
const LoginPage = () => {
  const { isAuthenticated, login, isLoading, authError } = useAuth();
  const location = useLocation();

  // Get the intended destination after login
  const from = location.state?.from?.pathname || '/';

  // Redirect to intended destination if already authenticated
  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  /**
   * Handle login button click.
   * Initiates Keycloak authentication flow.
   */
  const handleLogin = () => {
    login({
      redirectUri: window.location.origin + from,
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full mx-auto px-4">
        <div className="bg-gray-800 rounded-lg shadow-xl border border-gray-700 p-8">
          {/* Logo and Title */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
                  />
                </svg>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">
              3D Educational Visualizer
            </h1>
            <p className="text-gray-400 text-sm">
              Sign in to create and explore interactive 3D visualizations
            </p>
          </div>

          {/* Error Message */}
          {authError && (
            <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
              <div className="flex items-center space-x-2">
                <svg
                  className="w-5 h-5 text-red-400 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div>
                  <h3 className="text-red-400 font-medium text-sm">
                    Authentication Error
                  </h3>
                  <p className="text-red-300 text-xs mt-1">{authError}</p>
                </div>
              </div>
            </div>
          )}

          {/* Login Button */}
          <div className="space-y-4">
            <button
              onClick={handleLogin}
              disabled={isLoading}
              className={cn(
                'w-full flex items-center justify-center px-4 py-3 border border-transparent text-sm font-medium rounded-lg text-white transition-colors',
                'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-gray-800',
                isLoading && 'opacity-50 cursor-not-allowed'
              )}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Signing in...
                </>
              ) : (
                <>
                  <svg
                    className="w-4 h-4 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                    />
                  </svg>
                  Sign In with SSO
                </>
              )}
            </button>

            <div className="text-center">
              <p className="text-xs text-gray-500">
                Secure authentication powered by Keycloak
              </p>
            </div>
          </div>

          {/* Features Preview */}
          <div className="mt-8 pt-6 border-t border-gray-700">
            <h3 className="text-sm font-medium text-gray-400 mb-3">
              What you can do:
            </h3>
            <div className="space-y-2 text-xs text-gray-500">
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                <span>Create interactive 3D educational content</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                <span>Save and organize your visualizations</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
                <span>Share content with students and colleagues</span>
              </div>
            </div>
          </div>

          {/* Help Text */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-600">
              Need help? Contact your administrator or{' '}
              <a
                href="mailto:support@example.com"
                className="text-blue-400 hover:text-blue-300 underline"
              >
                technical support
              </a>
            </p>
          </div>
        </div>

        {/* Development Info */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-4 p-3 bg-yellow-900/30 border border-yellow-700 rounded-lg">
            <div className="flex items-center space-x-2 text-yellow-400">
              <svg
                className="w-4 h-4 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <h4 className="text-xs font-medium">Development Mode</h4>
                <p className="text-xs text-yellow-300 mt-1">
                  Using local Keycloak instance. Make sure your Keycloak server is running on localhost:28080.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;
