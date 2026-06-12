import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Document } from '../types';

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await api.fetchDocuments();
      setDocuments(data);
      setError(null);
    } catch (err: any) {
      if (!silent) setError(err.message || 'Failed to load documents');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // Poll for status updates if any doc is processing
  useEffect(() => {
    const hasPending = documents.some(d => d.status === 'uploaded' || d.status === 'processing');
    if (!hasPending) return;

    const interval = setInterval(() => {
      loadDocuments(true);
    }, 3000);

    return () => clearInterval(interval);
  }, [documents]);

  return { documents, loadDocuments, loading, error, setError };
}
