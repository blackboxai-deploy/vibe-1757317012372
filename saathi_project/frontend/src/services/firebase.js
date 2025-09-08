/**
 * Firebase configuration and initialization for Saathi.
 * Handles authentication, Firestore, and Storage integration.
 */

import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';
import { getStorage, connectStorageEmulator } from 'firebase/storage';

let app = null;
let auth = null;
let db = null;
let storage = null;

/**
 * Initialize Firebase with configuration from environment variables.
 */
export const initializeFirebase = async () => {
  try {
    // Parse Firebase config from environment variable
    const firebaseConfigString = import.meta.env.REACT_APP_FIREBASE_CONFIG;
    
    if (!firebaseConfigString) {
      console.warn('Firebase config not found in environment variables. Using fallback configuration.');
      // Fallback configuration for development
      const fallbackConfig = {
        apiKey: "demo-api-key",
        authDomain: "saathi-demo.firebaseapp.com",
        projectId: "saathi-demo",
        storageBucket: "saathi-demo.appspot.com",
        messagingSenderId: "123456789012",
        appId: "1:123456789012:web:abcdef123456"
      };
      
      app = initializeApp(fallbackConfig);
    } else {
      const firebaseConfig = JSON.parse(firebaseConfigString);
      app = initializeApp(firebaseConfig);
    }
    
    // Initialize Firebase services
    auth = getAuth(app);
    db = getFirestore(app);
    storage = getStorage(app);
    
    // Connect to emulators in development
    if (import.meta.env.DEV) {
      try {
        // These will only connect if emulators are running
        connectAuthEmulator(auth, 'http://localhost:9099');
        connectFirestoreEmulator(db, 'localhost', 8080);
        connectStorageEmulator(storage, 'localhost', 9199);
        console.log('Connected to Firebase emulators');
      } catch (error) {
        console.log('Firebase emulators not available, using live Firebase');
      }
    }
    
    console.log('Firebase initialized successfully');
    
    return { app, auth, db, storage };
    
  } catch (error) {
    console.error('Firebase initialization error:', error);
    throw error;
  }
};

/**
 * Get Firebase Auth instance.
 */
export const getFirebaseAuth = () => {
  if (!auth) {
    throw new Error('Firebase not initialized. Call initializeFirebase() first.');
  }
  return auth;
};

/**
 * Get Firestore instance.
 */
export const getFirestore = () => {
  if (!db) {
    throw new Error('Firebase not initialized. Call initializeFirebase() first.');
  }
  return db;
};

/**
 * Get Firebase Storage instance.
 */
export const getFirebaseStorage = () => {
  if (!storage) {
    throw new Error('Firebase not initialized. Call initializeFirebase() first.');
  }
  return storage;
};

/**
 * Get Firebase App instance.
 */
export const getFirebaseApp = () => {
  if (!app) {
    throw new Error('Firebase not initialized. Call initializeFirebase() first.');
  }
  return app;
};

// Export instances for backward compatibility
export { auth, db, storage, app };