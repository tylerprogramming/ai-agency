import React from 'react';
import { LogIn, LogOut, RefreshCw, AlertCircle } from 'lucide-react';

interface AuthButtonProps {
  isSignedIn: boolean;
  loading: boolean;
  error?: string | null;
  onSignIn: () => void;
  onSignOut: () => void;
  onRetry?: () => void;
}

export const AuthButton: React.FC<AuthButtonProps> = ({
  isSignedIn,
  loading,
  error,
  onSignIn,
  onSignOut,
  onRetry,
}) => {
  if (loading) {
    return (
      <div className="flex items-center space-x-2 bg-gray-100 px-4 py-2 rounded-lg">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
        <span className="text-gray-600">Loading...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col space-y-2">
        <div className="flex items-center space-x-2 bg-red-50 text-red-700 px-4 py-2 rounded-lg border border-red-200 max-w-md">
          <AlertCircle size={16} />
          <span className="text-sm">{error}</span>
        </div>
        <div className="flex items-center space-x-2">
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors duration-200"
            >
              <RefreshCw size={16} />
              <span>Retry</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  if (isSignedIn) {
    return (
      <button
        onClick={onSignOut}
        className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors duration-200"
      >
        <LogOut size={16} />
        <span>Sign Out</span>
      </button>
    );
  }

  return (
    <button
      onClick={onSignIn}
      className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors duration-200 shadow-md hover:shadow-lg"
    >
      <LogIn size={16} />
      <span>Sign in with Google</span>
    </button>
  );
};