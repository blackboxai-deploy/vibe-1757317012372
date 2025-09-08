/**
 * API service for communicating with Saathi backend.
 */

import axios from 'axios';
import { getUserIdToken } from './auth';

// API base URL from environment
const API_BASE = import.meta.env.REACT_APP_API_BASE || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    try {
      // Add Firebase ID token to requests
      const token = await getUserIdToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      // Continue without token if not authenticated
      console.warn('Could not get auth token:', error);
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
      return Promise.reject({
        status: error.response.status,
        message: error.response.data.error || 'An error occurred',
        data: error.response.data
      });
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request);
      return Promise.reject({
        status: 0,
        message: 'Network error. Please check your connection.',
        data: null
      });
    } else {
      // Something else happened
      console.error('Request Error:', error.message);
      return Promise.reject({
        status: -1,
        message: error.message || 'An unexpected error occurred',
        data: null
      });
    }
  }
);

/**
 * Send a chat message to the AI.
 */
export const sendChat = async (uid, message, history = [], context = {}) => {
  try {
    const response = await api.post('/chat/', {
      uid,
      message,
      history,
      context,
      session_id: `session_${uid}_${Date.now()}`
    });
    
    return response.data;
  } catch (error) {
    console.error('Send chat error:', error);
    throw error;
  }
};

/**
 * Transcribe audio file to text.
 */
export const transcribeAudio = async (audioBlob) => {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    
    const response = await api.post('/transcribe/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // Longer timeout for transcription
    });
    
    return response.data;
  } catch (error) {
    console.error('Transcribe audio error:', error);
    throw error;
  }
};

/**
 * Ingest a file for RAG processing.
 */
export const ingestFile = async (fileUrl, uid, filename) => {
  try {
    const response = await api.post('/ingest-file/', {
      fileUrl,
      uid,
      filename
    });
    
    return response.data;
  } catch (error) {
    console.error('Ingest file error:', error);
    throw error;
  }
};

/**
 * Get or update user profile.
 */
export const getUserProfile = async (uid) => {
  try {
    const response = await api.get(`/profile/?uid=${uid}`);
    return response.data;
  } catch (error) {
    console.error('Get user profile error:', error);
    throw error;
  }
};

export const updateUserProfile = async (profileData) => {
  try {
    const response = await api.post('/profile/', profileData);
    return response.data;
  } catch (error) {
    console.error('Update user profile error:', error);
    throw error;
  }
};

/**
 * Submit screening assessment.
 */
export const submitScreening = async (uid, screeningType, responses) => {
  try {
    const response = await api.post('/screening/', {
      uid,
      screening_type: screeningType,
      responses
    });
    
    return response.data;
  } catch (error) {
    console.error('Submit screening error:', error);
    throw error;
  }
};

/**
 * Get screening history.
 */
export const getScreeningHistory = async (uid) => {
  try {
    const response = await api.get(`/screening/history/?uid=${uid}`);
    return response.data;
  } catch (error) {
    console.error('Get screening history error:', error);
    throw error;
  }
};

/**
 * Get conversation history.
 */
export const getConversationHistory = async (uid) => {
  try {
    const response = await api.get(`/conversations/?uid=${uid}`);
    return response.data;
  } catch (error) {
    console.error('Get conversation history error:', error);
    throw error;
  }
};

/**
 * Get user memories.
 */
export const getUserMemories = async (uid) => {
  try {
    const response = await api.get(`/profile/memory/?uid=${uid}`);
    return response.data;
  } catch (error) {
    console.error('Get user memories error:', error);
    throw error;
  }
};

/**
 * Send OTP for email authentication.
 */
export const sendOTP = async (email) => {
  try {
    const response = await api.post('/auth/send-otp/', { email });
    return response.data;
  } catch (error) {
    console.error('Send OTP error:', error);
    throw error;
  }
};

/**
 * Verify OTP for email authentication.
 */
export const verifyOTP = async (email, otp) => {
  try {
    const response = await api.post('/auth/verify-otp/', { email, otp });
    return response.data;
  } catch (error) {
    console.error('Verify OTP error:', error);
    throw error;
  }
};

/**
 * Health check endpoint.
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/health/');
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

// Export axios instance for custom requests
export { api };
export default api;