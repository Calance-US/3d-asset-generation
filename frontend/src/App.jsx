import React from "react";
import Generator from "./components/Generator";
import Admin from "./components/Admin";
import LoginPage from "./components/auth/LoginPage";
import ProtectedRoute, { AdminRoute, OptionalAuthRoute } from "./components/auth/ProtectedRoute";
import AuthLoading, { AuthLoadingWithError } from "./components/auth/AuthLoading";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

/**
 * App content component that uses authentication context.
 * This component is rendered inside the AuthProvider to access auth state.
 */
function AppContent() {
  const { isLoading, isAuthInitialized, authError } = useAuth();

  // Show loading screen while authentication is initializing
  if (isLoading || !isAuthInitialized) {
    return (
      <AuthLoadingWithError
        isLoading={isLoading}
        error={authError}
        onRetry={() => window.location.reload()}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Routes>
        {/* Public/Optional Auth Routes */}
        <Route
          path="/"
          element={
            <OptionalAuthRoute>
              <Generator />
            </OptionalAuthRoute>
          }
        />

        {/* Authentication Routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Routes */}
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <Admin />
            </AdminRoute>
          }
        />

        {/* Catch-all route - redirect to home */}
        <Route path="*" element={<Generator />} />
      </Routes>
    </div>
  );
}

/**
 * Main App component with authentication provider.
 */
function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
