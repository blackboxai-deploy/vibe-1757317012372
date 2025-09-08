/**
 * Authentication service for Saathi.
 * Handles Google sign-in and email magic links.
 */

import { 
  signInWithPopup, 
  GoogleAuthProvider, 
  sendSignInLinkToEmail,
  isSignInWithEmailLink,
  signInWithEmailLink,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';
import { getFirebaseAuth } from './firebase';

const provider = new GoogleAuthProvider();

/**
 * Sign in with Google popup.
 */
export const signInWithGoogle = async () => {
  try {
    const auth = getFirebaseAuth();
    const result = await signInWithPopup(auth, provider);
    
    // Get user information
    const user = result.user;
    const credential = GoogleAuthProvider.credentialFromResult(result);
    
    return {
      user: {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        emailVerified: user.emailVerified
      },
      credential,
      isNewUser: result._tokenResponse?.isNewUser || false
    };
  } catch (error) {
    console.error('Google sign-in error:', error);
    throw {
      code: error.code,
      message: error.message,
      details: error
    };
  }
};

/**
 * Send sign-in link to email.
 */
export const sendSignInLinkToEmailAddress = async (email) => {
  try {
    const auth = getFirebaseAuth();
    
    const actionCodeSettings = {
      // URL you want to redirect back to after the link is clicked
      url: `${window.location.origin}/login`,
      // This must be true
      handleCodeInApp: true,
      iOS: {
        bundleId: 'com.saathi.app'
      },
      android: {
        packageName: 'com.saathi.app',
        installApp: true,
        minimumVersion: '12'
      },
      dynamicLinkDomain: 'saathi.page.link'
    };
    
    await sendSignInLinkToEmail(auth, email, actionCodeSettings);
    
    // Save the email locally so you don't need to ask the user for it again
    window.localStorage.setItem('emailForSignIn', email);
    
    return { success: true };
  } catch (error) {
    console.error('Send email link error:', error);
    throw {
      code: error.code,
      message: error.message,
      details: error
    };
  }
};

/**
 * Complete sign-in with email link.
 */
export const completeSignInWithEmailLink = async (emailLink) => {
  try {
    const auth = getFirebaseAuth();
    
    // Confirm the link is a sign-in with email link
    if (!isSignInWithEmailLink(auth, emailLink)) {
      throw new Error('Invalid sign-in link');
    }
    
    // Get the email if available from localStorage
    let email = window.localStorage.getItem('emailForSignIn');
    
    if (!email) {
      // If missing, ask the user to provide their email
      email = window.prompt('Please provide your email for confirmation');
    }
    
    if (!email) {
      throw new Error('Email is required to complete sign-in');
    }
    
    const result = await signInWithEmailLink(auth, email, emailLink);
    
    // Clear the email from storage
    window.localStorage.removeItem('emailForSignIn');
    
    return {
      user: {
        uid: result.user.uid,
        email: result.user.email,
        displayName: result.user.displayName,
        photoURL: result.user.photoURL,
        emailVerified: result.user.emailVerified
      },
      isNewUser: result._tokenResponse?.isNewUser || false
    };
  } catch (error) {
    console.error('Email link sign-in error:', error);
    throw {
      code: error.code,
      message: error.message,
      details: error
    };
  }
};

/**
 * Sign out current user.
 */
export const signOutUser = async () => {
  try {
    const auth = getFirebaseAuth();
    await signOut(auth);
    
    // Clear any local storage
    window.localStorage.removeItem('emailForSignIn');
    
    return { success: true };
  } catch (error) {
    console.error('Sign out error:', error);
    throw {
      code: error.code,
      message: error.message,
      details: error
    };
  }
};

/**
 * Get current user.
 */
export const getCurrentUser = () => {
  const auth = getFirebaseAuth();
  return auth.currentUser;
};

/**
 * Subscribe to auth state changes.
 */
export const subscribeToAuthState = (callback) => {
  const auth = getFirebaseAuth();
  return onAuthStateChanged(auth, callback);
};

/**
 * Get user ID token.
 */
export const getUserIdToken = async (forceRefresh = false) => {
  try {
    const auth = getFirebaseAuth();
    const user = auth.currentUser;
    
    if (!user) {
      throw new Error('No user signed in');
    }
    
    return await user.getIdToken(forceRefresh);
  } catch (error) {
    console.error('Get ID token error:', error);
    throw error;
  }
};

/**
 * Check if email link is valid for sign-in.
 */
export const isValidSignInEmailLink = (emailLink) => {
  const auth = getFirebaseAuth();
  return isSignInWithEmailLink(auth, emailLink);
};