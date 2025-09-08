/**
 * Theme context for managing dark/light mode across the app.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { updateUserProfile, getUserProfile } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeContextProvider');
  }
  return context;
};

export const ThemeContextProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  // Load theme preference on mount
  useEffect(() => {
    const loadThemePreference = async () => {
      try {
        if (user?.uid) {
          // Try to get user profile with theme preference
          const profile = await getUserProfile(user.uid);
          const savedTheme = profile?.theme_preference || 'light';
          setIsDarkMode(savedTheme === 'dark');
        } else {
          // Fall back to localStorage for non-authenticated users
          const savedTheme = localStorage.getItem('saathi_theme');
          setIsDarkMode(savedTheme === 'dark');
        }
      } catch (error) {
        // Fall back to localStorage if API fails
        const savedTheme = localStorage.getItem('saathi_theme');
        setIsDarkMode(savedTheme === 'dark');
      } finally {
        setLoading(false);
      }
    };

    loadThemePreference();
  }, [user]);

  // Save theme preference when it changes
  useEffect(() => {
    const saveThemePreference = async () => {
      const theme = isDarkMode ? 'dark' : 'light';
      
      // Always save to localStorage as backup
      localStorage.setItem('saathi_theme', theme);
      
      // Also save to user profile if authenticated
      if (user?.uid) {
        try {
          await updateUserProfile({
            uid: user.uid,
            theme_preference: theme
          });
        } catch (error) {
          console.warn('Failed to save theme preference to profile:', error);
        }
      }
    };

    if (!loading) {
      saveThemePreference();
    }
  }, [isDarkMode, user, loading]);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  const setTheme = (theme) => {
    setIsDarkMode(theme === 'dark');
  };

  const value = {
    isDarkMode,
    themePreference: isDarkMode ? 'dark' : 'light',
    toggleTheme,
    setTheme,
    loading
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};