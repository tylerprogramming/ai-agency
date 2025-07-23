import { useState, useEffect } from 'react';

export const useGoogleAuth = () => {
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/auth/status');
      const data = await response.json();
      setIsSignedIn(data.authenticated);
      setError(null);
    } catch (err) {
      setError('Failed to check authentication status');
      setIsSignedIn(false);
    } finally {
      setLoading(false);
    }
  };

  const signIn = () => {
    window.location.href = '/auth/start';
  };

  const signOut = async () => {
    try {
      await fetch('/auth/logout', { method: 'POST' });
      setIsSignedIn(false);
    } catch (err) {
      setError('Failed to sign out');
    }
  };

  const retry = () => {
    setError(null);
    checkAuthStatus();
  };

  useEffect(() => {
    // Check auth status on component mount
    checkAuthStatus();

    // Check for auth success callback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth') === 'success') {
      // Remove the auth parameter from URL
      window.history.replaceState({}, document.title, window.location.pathname);
      // Recheck auth status
      setTimeout(() => checkAuthStatus(), 1000);
    }
  }, []);

  return {
    isSignedIn,
    user: null,
    loading,
    error,
    signIn,
    signOut,
    retry,
    checkAuthStatus,
  };
};