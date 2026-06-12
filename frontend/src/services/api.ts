import { API_BASE_URL } from '../config/constants';
import { ChatRequest, ChatResponse, Document } from '../types';

export const api = {
  fetchDocuments: async (): Promise<Document[]> => {
    const res = await fetch(`${API_BASE_URL}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  uploadDocument: async (file: File, category: string | null = null): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    if (category) formData.append('category', category);

    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  deleteDocument: async (id: number): Promise<{ message: string; id: number }> => {
    const res = await fetch(`${API_BASE_URL}/documents/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  },

  resetSystem: async (): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/documents`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to reset system');
    return res.json();
  },

  cleanSystem: async (): Promise<any> => {
    const res = await fetch(`${API_BASE_URL}/clean-system`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to clean system');
    return res.json();
  },

  askQuestion: async (req: ChatRequest): Promise<ChatResponse> => {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Chat request failed');
    }
    return res.json();
  },
};
