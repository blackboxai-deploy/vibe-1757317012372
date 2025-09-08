import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, CircularProgress } from '@mui/material';

// Firebase and Auth
import { initializeFirebase } from './services/firebase';
import { useAuth } from './hooks/useAuth';

// Theme
import { ThemeContextProvider, useTheme } from './contexts/ThemeContext';

// Pages
import Login from './pages/Login';
import Chat from './pages/Chat';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import Booking from './pages/Booking';

// Components
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/AppLayout';
import ErrorBoundary from './components/ErrorBoundary';

function AppContent() {
  const { isDarkMode, themePreference } = useTheme();
  const { user, loading } = useAuth();
  
  const theme = createTheme({
    palette: {
      mode: isDarkMode ? 'dark' : 'light',
      primary: {
        main: '#667eea',
        light: '#8aa5f5',
        dark: '#4a5db5',
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#764ba2',
        light: '#9f78c7',
        dark: '#553572',
        contrastText: '#ffffff',
      },
      background: {
        default: isDarkMode ? '#121212' : '#fafafa',
        paper: isDarkMode ? '#1e1e1e' : '#ffffff',
      },
      text: {
        primary: isDarkMode ? '#ffffff' : '#333333',
        secondary: isDarkMode ? '#b3b3b3' : '#666666',
      },
      error: {
        main: '#f44336',
      },
      warning: {
        main: '#ff9800',
      },
      info: {
        main: '#2196f3',
      },
      success: {
        main: '#4caf50',
      },
    },
    typography: {
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      h1: {
        fontWeight: 600,
      },
      h2: {
        fontWeight: 600,
      },
      h3: {
        fontWeight: 500,
      },
      h4: {
        fontWeight: 500,
      },
      h5: {
        fontWeight: 500,
      },
      h6: {
        fontWeight: 500,
      },
      body1: {
        lineHeight: 1.6,
      },
      body2: {
        lineHeight: 1.5,
      },
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            borderRadius: 8,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
            border: isDarkMode ? '1px solid #333' : '1px solid #e0e0e0',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
    },
  });

  if (loading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}
      >
        <Box textAlign="center">
          <Box fontSize="3rem" mb={2}>🧠</Box>
          <CircularProgress color="inherit" size={40} />
          <Box mt={2} fontSize="1.2rem">Initializing Saathi...</Box>
        </Box>
      </Box>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <Routes>
          {/* Public Routes */}
          <Route 
            path="/login" 
            element={user ? <Navigate to="/" replace /> : <Login />} 
          />
          
          {/* Protected Routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Chat />
                </AppLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Dashboard />
                </AppLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/history" 
            element={
              <ProtectedRoute>
                <AppLayout>
                  <History />
                </AppLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/booking" 
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Booking />
                </AppLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Redirect unknown routes */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

function App() {
  const [firebaseInitialized, setFirebaseInitialized] = useState(false);
  
  useEffect(() => {
    const initFirebase = async () => {
      try {
        await initializeFirebase();
        setFirebaseInitialized(true);
      } catch (error) {
        console.error('Firebase initialization failed:', error);
        setFirebaseInitialized(true); // Continue anyway for development
      }
    };
    
    initFirebase();
  }, []);
  
  if (!firebaseInitialized) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}
      >
        <Box textAlign="center">
          <Box fontSize="3rem" mb={2}>🔥</Box>
          <CircularProgress color="inherit" size={40} />
          <Box mt={2} fontSize="1.2rem">Connecting to Firebase...</Box>
        </Box>
      </Box>
    );
  }
  
  return (
    <ThemeContextProvider>
      <AppContent />
    </ThemeContextProvider>
  );
}

export default App;