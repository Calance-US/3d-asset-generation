import React from 'react';
import { cn } from '../../lib/utils';

/**
 * Loading component displayed during authentication initialization.
 *
 * This component provides visual feedback while Keycloak authentication
 * is being initialized and configured.
 */
const AuthLoading = ({
  className = '',
  message = 'Initializing authentication...',
  showSpinner = true,
  showLogo = true
}) => {
  return (
    <div className={cn(
      'min-h-screen bg-gray-900 flex items-center justify-center',
      className
    )}>
      <div className="text-center space-y-6 max-w-md mx-auto px-4">
        {/* Logo Section */}
        {showLogo && (
          <div className="flex justify-center mb-8">
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
        )}

        {/* Spinner */}
        {showSpinner && (
          <div className="flex justify-center">
            <div className="relative">
              <div className="w-12 h-12 border-4 border-gray-300 border-solid rounded-full animate-spin border-t-transparent"></div>
              <div className="absolute top-0 left-0 w-12 h-12 border-4 border-blue-500 border-solid rounded-full animate-spin border-t-transparent border-l-transparent border-r-transparent"></div>
            </div>
          </div>
        )}

        {/* Loading Message */}
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-white">
            3D Educational Visualizer
          </h2>
          <p className="text-gray-400 text-sm">
            {message}
          </p>
        </div>

        {/* Loading Steps */}
        <div className="space-y-2 text-xs text-gray-500">
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span>Connecting to authentication service</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
            <span>Verifying credentials</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
            <span>Loading application</span>
          </div>
        </div>

        {/* Additional Info */}
        <div className="text-xs text-gray-600 border-t border-gray-800 pt-4">
          <p>If this takes longer than expected, please refresh the page.</p>
        </div>
      </div>
    </div>
  );
};

/**
 * Minimal loading spinner component for inline use.
 */
export const AuthLoadingSpinner = ({
  size = 'md',
  className = '',
  color = 'blue'
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  };

  const colorClasses = {
    blue: 'border-blue-500',
    gray: 'border-gray-500',
    white: 'border-white',
    green: 'border-green-500',
    red: 'border-red-500'
  };

  return (
    <div className={cn(
      'inline-block animate-spin rounded-full border-2 border-solid border-current border-r-transparent',
      sizeClasses[size],
      colorClasses[color],
      className
    )}>
      <span className="sr-only">Loading...</span>
    </div>
  );
};

/**
 * Loading component with error state support.
 */
export const AuthLoadingWithError = ({
  isLoading = true,
  error = null,
  onRetry = null,
  className = ''
}) => {
  if (error) {
    return (
      <div className={cn(
        'min-h-screen bg-gray-900 flex items-center justify-center',
        className
      )}>
        <div className="text-center space-y-6 max-w-md mx-auto px-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-red-600 rounded-lg flex items-center justify-center">
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
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-white">
              Authentication Error
            </h2>
            <p className="text-gray-400 text-sm">
              {error}
            </p>
          </div>

          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <AuthLoading className={className} />;
  }

  return null;
};

export default AuthLoading;
