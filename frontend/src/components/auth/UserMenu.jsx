import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/utils';

/**
 * User menu component for authenticated users.
 *
 * This component provides a dropdown menu with user information,
 * account management options, and logout functionality.
 */
const UserMenu = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);
  const buttonRef = useRef(null);

  const {
    user,
    logout,
    manageAccount,
    isAdmin,
    isEducator,
    displayName,
    userRoles
  } = useAuth();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Close menu on escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleEscape);
      };
    }
  }, [isOpen]);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
  };

  const handleManageAccount = () => {
    setIsOpen(false);
    manageAccount();
  };

  // Get user initials for avatar
  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };

  // Get role color
  const getRoleColor = () => {
    if (isAdmin()) return 'bg-red-500';
    if (isEducator()) return 'bg-blue-500';
    return 'bg-green-500';
  };

  // Get role display name
  const getRoleDisplayName = () => {
    if (isAdmin()) return 'Administrator';
    if (isEducator()) return 'Educator';
    return 'Student';
  };

  return (
    <div className={cn('relative', className)}>
      {/* User Avatar Button */}
      <button
        ref={buttonRef}
        onClick={toggleMenu}
        className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        {/* Avatar */}
        <div className="relative">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
            {getInitials(displayName)}
          </div>
          {/* Role indicator */}
          <div className={cn(
            'absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-800',
            getRoleColor()
          )}></div>
        </div>

        {/* User Name */}
        <div className="hidden md:block text-left">
          <div className="text-sm font-medium text-white">
            {displayName}
          </div>
          <div className="text-xs text-gray-400">
            {getRoleDisplayName()}
          </div>
        </div>

        {/* Dropdown Arrow */}
        <svg
          className={cn(
            'w-4 h-4 text-gray-400 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          ref={menuRef}
          className="absolute right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50"
        >
          {/* User Info Section */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-lg font-medium">
                  {getInitials(displayName)}
                </div>
                <div className={cn(
                  'absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-gray-800',
                  getRoleColor()
                )}></div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">
                  {displayName}
                </div>
                <div className="text-xs text-gray-400 truncate">
                  {user?.email}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {getRoleDisplayName()}
                </div>
              </div>
            </div>

            {/* Roles Badge */}
            {userRoles.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {userRoles.slice(0, 3).map((role) => (
                  <span
                    key={role}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-300"
                  >
                    {role}
                  </span>
                ))}
                {userRoles.length > 3 && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-300">
                    +{userRoles.length - 3}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Menu Items */}
          <div className="py-2">
            {/* Account Management */}
            <button
              onClick={handleManageAccount}
              className="w-full flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              <svg
                className="w-4 h-4 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
              Manage Account
            </button>

            {/* Settings */}
            <button
              onClick={() => {
                setIsOpen(false);
                // Add settings navigation logic
              }}
              className="w-full flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              <svg
                className="w-4 h-4 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              Settings
            </button>

            {/* Help */}
            <button
              onClick={() => {
                setIsOpen(false);
                // Add help navigation logic
              }}
              className="w-full flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              <svg
                className="w-4 h-4 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Help & Support
            </button>

            <div className="border-t border-gray-700 my-2"></div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="w-full flex items-center px-4 py-2 text-sm text-red-400 hover:bg-red-900/20 hover:text-red-300 transition-colors"
            >
              <svg
                className="w-4 h-4 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              Sign Out
            </button>
          </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t border-gray-700 text-xs text-gray-500">
            Connected via {user?.provider || 'SSO'}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Compact user menu for mobile or small spaces.
 */
export const CompactUserMenu = ({ className = '' }) => {
  const { user, logout, displayName, isAdmin, isEducator } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };

  const getRoleColor = () => {
    if (isAdmin()) return 'bg-red-500';
    if (isEducator()) return 'bg-blue-500';
    return 'bg-green-500';
  };

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      <div className="relative">
        <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-medium">
          {getInitials(displayName)}
        </div>
        <div className={cn(
          'absolute -top-1 -right-1 w-2 h-2 rounded-full border border-gray-800',
          getRoleColor()
        )}></div>
      </div>
      <button
        onClick={handleLogout}
        className="p-1 text-gray-400 hover:text-white transition-colors"
        title="Sign Out"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
          />
        </svg>
      </button>
    </div>
  );
};

export default UserMenu;
