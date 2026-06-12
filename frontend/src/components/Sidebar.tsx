import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, Trash2, RefreshCw } from 'lucide-react';
import { Document } from '../types';
import { api } from '../services/api';
import { formatBytes } from '../utils/format';

interface SidebarProps {
  documents: Document[];
  selectedCategory: string | null;
  selectedDocId: number | null;
  onSelectCategory: (cat: string | null) => void;
  onSelectDocument: (id: number | null) => void;
  onRefreshDocuments: () => void;
  onError: (msg: string) => void;
}

export function Sidebar({
  documents,
  selectedCategory,
  selectedDocId,
  onSelectCategory,
  onSelectDocument,
  onRefreshDocuments,
  onError,
}: SidebarProps) {
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const categories = Array.from(new Set(documents.map(d => d.category).filter(Boolean))) as string[];

  const handleUpload = async (file: File) => {
    if (file.type !== 'application/pdf') {
      onError('Only PDF files are supported.');
      return;
    }
    setUploading(true);
    try {
      await api.uploadDocument(file, uploadCategory);
      setUploadCategory('');
      onRefreshDocuments();
    } catch (err: any) {
      onError(err.message || 'File upload failed.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.deleteDocument(id);
      if (selectedDocId === id) onSelectDocument(null);
      onRefreshDocuments();
    } catch {
      onError('Failed to delete document.');
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <h2 className="sidebar-section-title">Ingest Documents</h2>
        <input 
          type="text" 
          placeholder="Category Name (Optional)"
          value={uploadCategory}
          onChange={(e) => setUploadCategory(e.target.value)}
          style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
        />
        <div 
          className="dropzone-container"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]); }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input type="file" ref={fileInputRef} hidden accept=".pdf" onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} />
          {uploading ? <RefreshCw className="animate-spin" /> : <UploadCloud />}
          <span>{uploading ? 'Uploading...' : 'Drop PDF here'}</span>
        </div>
      </div>

      <div className="sidebar-section">
        <h2 className="sidebar-section-title">Categories</h2>
        <div className="flex-wrap gap-2">
          {categories.map(cat => (
            <button 
              key={cat}
              className={`citation-pill ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => { onSelectCategory(selectedCategory === cat ? null : cat); onSelectDocument(null); }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-section flex-1 overflow-auto">
        <h2 className="sidebar-section-title">Documents ({documents.length})</h2>
        {documents.map(doc => (
          <div 
            key={doc.id} 
            className={`document-card ${selectedDocId === doc.id ? 'active' : ''}`}
            onClick={() => { onSelectDocument(selectedDocId === doc.id ? null : doc.id); onSelectCategory(null); }}
          >
            <div className="flex items-center gap-2">
              <FileText size={18} />
              <div>
                <div className="font-bold">{doc.filename}</div>
                <div className="text-xs text-gray-500">{formatBytes(doc.file_size)} • {doc.status}</div>
              </div>
            </div>
            <button onClick={(e) => handleDelete(doc.id, e)}><Trash2 size={14} /></button>
          </div>
        ))}
      </div>
    </aside>
  );
}
