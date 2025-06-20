import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import AuthLoading from './AuthLoading';

/**
 * Protected route component that requires authentication.
 *
 * This component wraps routes that require user authentication.
 * It redirects unauthenticated users to login and shows loading
 * state during authentication initialization.
 */
const ProtectedRoute = ({
  children,
  redirectTo = '/login',
  requiredRole = null,
  requireAdmin = false,
  requireEducator = false,
  fallback = null
}) => {
  const {
    isAuthenticated,
    isAuthInitialized,
    isLoading,
    hasRole,
    isAdmin,
    isEducator,
    authError
  } = useAuth();
  const location = useLocation();

  // Show loading spinner while authentication is initializing
  if (isLoading || !isAuthInitialized) {
    return <AuthLoading message="Checking authentication..." />;
  }

  // Show error state if authentication failed
  if (authError) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md mx-auto px-4">
          <div className="w-16 h-16 bg-red-600 rounded-lg flex items-center justify-center mx-auto">
            <svg
              className="w-8 h-8 text-white"
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
          </div>
          <h2 className="text-xl font-semibold text-white">Authentication Error</h2>
          <p className="text-gray-400 text-sm">{authError}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Check role-based access control
  if (requireAdmin && !isAdmin()) {
    if (fallback) {
      return fallback;
    }
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md mx-auto px-4">
          <div className="w-16 h-16 bg-yellow-600 rounded-lg flex items-center justify-center mx-auto">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m0 0v2m0-2h2m-2 0H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white">Access Denied</h2>
          <p className="text-gray-400 text-sm">
            Admin privileges required to access this page.
          </p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (requireEducator && !isEducator()) {
    if (fallback) {
      return fallback;
    }
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md mx-auto px-4">
          <div className="w-16 h-16 bg-yellow-600 rounded-lg flex items-center justify-center mx-auto">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m0 0v2m0-2h2m-2 0H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white">Access Denied</h2>
          <p className="text-gray-400 text-sm">
            Educator privileges required to access this page.
          </p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (requiredRole && !hasRole(requiredRole)) {
    if (fallback) {
      return fallback;
    }
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md mx-auto px-4">
          <div className="w-16 h-16 bg-yellow-600 rounded-lg flex items-center justify-center mx-auto">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m0 0v2m0-2h2m-2 0H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white">Access Denied</h2>
          <p className="text-gray-400 text-sm">
            Role '{requiredRole}' required to access this page.
          </p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // User is authenticated and authorized, render the protected content
  return children;
};

/**
 * Admin-only protected route component.
 */
export const AdminRoute = ({ children, fallback = null }) => {
  return (
    <ProtectedRoute requireAdmin={true} fallback={fallback}>
      {children}
    </ProtectedRoute>
  );
};

/**
 * Educator-or-higher protected route component.
 */
export const EducatorRoute = ({ children, fallback = null }) => {
  return (
    <ProtectedRoute requireEducator={true} fallback={fallback}>
      {children}
    </ProtectedRoute>
  );
};

/**
 * Role-based protected route component.
 */
export const RoleBasedRoute = ({ children, requiredRole, fallback = null }) => {
  return (
    <ProtectedRoute requiredRole={requiredRole} fallback={fallback}>
      {children}
    </ProtectedRoute>
  );
};

/**
 * Optional authentication route - works with or without authentication.
 * Shows different content based on authentication status.
 */
export const OptionalAuthRoute = ({
  children,
  unauthenticatedFallback = null,
  loadingFallback = null
}) => {
  const { isAuthenticated, isAuthInitialized, isLoading } = useAuth();

  // Show loading spinner while authentication is initializing
  if (isLoading || !isAuthInitialized) {
    return loadingFallback || <AuthLoading message="Loading..." />;
  }

  // Show content regardless of authentication status
  if (!isAuthenticated && unauthenticatedFallback) {
    return unauthenticatedFallback;
  }

  return children;
};

export default ProtectedRoute;
