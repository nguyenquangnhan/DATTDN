/**
 * Frontend constants - Updated for Python backend
 */

export const SUPPORTED_FILE_TYPES = {
  "application/pdf": {
    extension: ".pdf",
    name: "PDF Document",
    maxSize: 10 * 1024 * 1024, // 10MB
  },
  "image/png": {
    extension: ".png",
    name: "PNG Image",
    maxSize: 10 * 1024 * 1024,
  },
  "image/jpeg": {
    extension: ".jpg",
    name: "JPEG Image",
    maxSize: 10 * 1024 * 1024,
  },
  "image/webp": {
    extension: ".webp",
    name: "WebP Image",
    maxSize: 10 * 1024 * 1024,
  },
};

export const ACCEPTED_FILE_EXTENSIONS = ".pdf,.png,.jpg,.jpeg,.webp,.bmp,.tiff";

export const API_LIMITS = {
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFilesPerUpload: 10,
  maxUrlContentLength: 1000000,
  requestTimeout: 60000, // 60 seconds (processing can be slow)
};

export const UI_CONSTANTS = {
  maxChatMessages: 100,
  maxDocumentNameLength: 100,
  debounceDelay: 300,
};
