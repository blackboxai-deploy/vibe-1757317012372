/**
 * Firebase Storage service for file uploads.
 */

import { ref, uploadBytes, getDownloadURL, deleteObject } from 'firebase/storage';
import { getFirebaseStorage } from './firebase';
import { v4 as uuidv4 } from 'uuid';

/**
 * Upload file to Firebase Storage.
 */
export const uploadFile = async (file, folder = 'uploads', uid = null) => {
  try {
    const storage = getFirebaseStorage();
    
    // Generate unique filename
    const fileExtension = file.name.split('.').pop();
    const uniqueFileName = `${uuidv4()}.${fileExtension}`;
    
    // Create reference
    const path = uid ? `${folder}/${uid}/${uniqueFileName}` : `${folder}/${uniqueFileName}`;
    const storageRef = ref(storage, path);
    
    // Upload file
    const snapshot = await uploadBytes(storageRef, file);
    
    // Get download URL
    const downloadURL = await getDownloadURL(snapshot.ref);
    
    return {
      success: true,
      downloadURL,
      path: snapshot.ref.fullPath,
      filename: uniqueFileName,
      originalName: file.name,
      size: file.size,
      type: file.type
    };
    
  } catch (error) {
    console.error('File upload error:', error);
    return {
      success: false,
      error: error.message,
      downloadURL: null
    };
  }
};

/**
 * Upload audio blob (for voice recordings).
 */
export const uploadAudio = async (audioBlob, uid) => {
  try {
    const storage = getFirebaseStorage();
    
    // Create a unique filename for the audio
    const uniqueFileName = `audio_${Date.now()}.wav`;
    const path = `audio/${uid}/${uniqueFileName}`;
    const storageRef = ref(storage, path);
    
    // Upload audio blob
    const snapshot = await uploadBytes(storageRef, audioBlob);
    
    // Get download URL
    const downloadURL = await getDownloadURL(snapshot.ref);
    
    return {
      success: true,
      downloadURL,
      path: snapshot.ref.fullPath,
      filename: uniqueFileName,
      size: audioBlob.size,
      type: audioBlob.type || 'audio/wav'
    };
    
  } catch (error) {
    console.error('Audio upload error:', error);
    return {
      success: false,
      error: error.message,
      downloadURL: null
    };
  }
};

/**
 * Delete file from Firebase Storage.
 */
export const deleteFile = async (path) => {
  try {
    const storage = getFirebaseStorage();
    const storageRef = ref(storage, path);
    
    await deleteObject(storageRef);
    
    return {
      success: true,
      message: 'File deleted successfully'
    };
    
  } catch (error) {
    console.error('File deletion error:', error);
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * Get file metadata.
 */
export const getFileMetadata = async (path) => {
  try {
    const storage = getFirebaseStorage();
    const storageRef = ref(storage, path);
    
    const metadata = await storageRef.getMetadata();
    
    return {
      success: true,
      metadata
    };
    
  } catch (error) {
    console.error('Get file metadata error:', error);
    return {
      success: false,
      error: error.message,
      metadata: null
    };
  }
};

/**
 * Create a file from text content.
 */
export const uploadTextAsFile = async (textContent, filename, uid, contentType = 'text/plain') => {
  try {
    // Create blob from text
    const blob = new Blob([textContent], { type: contentType });
    
    // Create a file-like object
    const file = new File([blob], filename, { type: contentType });
    
    // Upload using the regular upload function
    return await uploadFile(file, 'documents', uid);
    
  } catch (error) {
    console.error('Upload text as file error:', error);
    return {
      success: false,
      error: error.message,
      downloadURL: null
    };
  }
};

/**
 * Upload conversation transcript.
 */
export const uploadConversationTranscript = async (conversation, uid) => {
  try {
    const timestamp = new Date().toISOString();
    const filename = `conversation_${timestamp.replace(/[:.]/g, '-')}.json`;
    
    const transcript = {
      timestamp,
      uid,
      conversation,
      metadata: {
        messageCount: conversation.length,
        createdAt: timestamp
      }
    };
    
    const textContent = JSON.stringify(transcript, null, 2);
    
    return await uploadTextAsFile(textContent, filename, uid, 'application/json');
    
  } catch (error) {
    console.error('Upload conversation transcript error:', error);
    return {
      success: false,
      error: error.message,
      downloadURL: null
    };
  }
};

/**
 * Validate file before upload.
 */
export const validateFile = (file, options = {}) => {
  const {
    maxSize = 10 * 1024 * 1024, // 10MB default
    allowedTypes = ['image/', 'text/', 'application/pdf', 'application/msword'],
    maxFiles = 1
  } = options;
  
  const errors = [];
  
  // Check file size
  if (file.size > maxSize) {
    errors.push(`File size must be less than ${maxSize / (1024 * 1024)}MB`);
  }
  
  // Check file type
  const isValidType = allowedTypes.some(type => 
    file.type.startsWith(type) || file.type === type
  );
  
  if (!isValidType) {
    errors.push(`File type ${file.type} is not allowed`);
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};