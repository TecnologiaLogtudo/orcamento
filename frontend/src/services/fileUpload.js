import api from './api';

export const fileUploadAPI = {
  upload: async (file, metadata = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      // Log the error for debugging, but re-throw to allow component-level handling
      console.error('File upload failed:', error);
      throw error;
    }
  },
};
