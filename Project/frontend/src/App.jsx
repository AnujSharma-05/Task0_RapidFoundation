import React, { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  Send, 
  Trash2, 
  RotateCcw, 
  UploadCloud, 
  Database, 
  Bot, 
  User, 
  Check, 
  RefreshCw, 
  X,
  AlertTriangle,
  FileCheck,
  Activity
} from 'lucide-react';
import * as api from './api';

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [uploadCategory, setUploadCategory] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Keeps track of which citation details card is currently expanded: { messageId, citationIndex }
  const [activeCitation, setActiveCitation] = useState(null);

  const [diagResults, setDiagResults] = useState(null);
  const [diagRunning, setDiagRunning] = useState(false);
  
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Fetch initial document list on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  // Poll for document status updates if any document is in a non-final state ('uploaded' or 'processing')
  useEffect(() => {
    const hasPendingDocs = documents.some(
      doc => doc.status === 'uploaded' || doc.status === 'processing'
    );
    
    if (!hasPendingDocs) return;

    const interval = setInterval(() => {
      loadDocuments(true); // silent load (don't show major loading indicator)
    }, 3000);

    return () => clearInterval(interval);
  }, [documents]);

  // Scroll to bottom of chat whenever messages or loading state changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadDocuments = async (silent = false) => {
    try {
      const data = await api.fetchDocuments();
      setDocuments(data);
    } catch (err) {
      if (!silent) {
        setErrorMsg('Failed to load documents from backend.');
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const handleFileChange = async (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const uploadFile = async (file) => {
    if (file.type !== 'application/pdf') {
      setErrorMsg('Only PDF files are supported.');
      return;
    }
    setUploading(true);
    setErrorMsg('');
    try {
      await api.uploadDocument(file, uploadCategory);
      setUploadCategory('');
      await loadDocuments();
    } catch (err) {
      setErrorMsg(err.message || 'File upload failed.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteDoc = async (id, e) => {
    e.stopPropagation(); // prevent selecting the document filter
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.deleteDocument(id);
      if (selectedDocId === id) {
        setSelectedDocId(null);
      }
      await loadDocuments();
    } catch (err) {
      setErrorMsg('Failed to delete document.');
    }
  };

  const handleReset = async () => {
    if (!confirm('Warning: This will delete all documents, chunks, and clear vectors. Proceed?')) return;
    
    try {
      await api.resetSystem();
      setDocuments([]);
      setSelectedDocId(null);
      setMessages([]);
      setActiveCitation(null);
      setErrorMsg('');
    } catch (err) {
      setErrorMsg('Failed to reset system.');
    }
  };

  const handleCleanProcesses = async () => {
    if (!confirm('Free system memory and clean zombie processes? This preserves the current server.')) return;
    try {
      const res = await api.cleanSystem();
      alert(`System Cleared!\n\nGarbage Collected: Yes\nZombie Python Processes Killed: ${res.zombies_killed}`);
    } catch (err) {
      setErrorMsg('Failed to clean system processes.');
    }
  };

  const handleSendQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userText = question;
    setQuestion('');
    setLoading(true);
    setErrorMsg('');
    
    // Add User message
    const userMsgId = Date.now();
    const newMessages = [
      ...messages,
      { id: userMsgId, role: 'user', text: userText }
    ];
    setMessages(newMessages);

    try {
      const response = await api.askQuestion(userText, selectedDocId, selectedCategory);
      setMessages([
        ...newMessages,
        {
          id: userMsgId + 1,
          role: 'assistant',
          text: response.answer,
          citations: response.citations || []
        }
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          id: userMsgId + 1,
          role: 'assistant',
          text: 'An error occurred while retrieving answer from the service.',
          isError: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 KB';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getDocName = (docId) => {
    const doc = documents.find(d => d.id === docId);
    return doc ? doc.filename : `Document #${docId}`;
  };

  const getSelectedDocName = () => {
    const doc = documents.find(d => d.id === selectedDocId);
    return doc ? doc.filename : '';
  };

  const toggleCitation = (msgId, index) => {
    if (activeCitation?.messageId === msgId && activeCitation?.index === index) {
      setActiveCitation(null);
    } else {
      setActiveCitation({ messageId: msgId, index });
    }
  };

  const runDiagnostics = async () => {
    setDiagRunning(true);
    setDiagResults([]);
    const results = [];

    const addResult = (name, status, message) => {
      results.push({ name, status, message });
      setDiagResults([...results]);
    };

    // Test 1: Ping
    try {
      const res = await fetch('http://127.0.0.1:8000/ping');
      if (res.ok) {
        addResult('Backend Ping', 'success', 'Connection alive');
      } else {
        addResult('Backend Ping', 'failed', `Status ${res.status}`);
      }
    } catch (err) {
      addResult('Backend Ping', 'failed', 'Connection refused');
      setDiagRunning(false);
      return;
    }

    // Test 2: Fetch Documents
    try {
      const docs = await api.fetchDocuments();
      addResult('Database Query', 'success', `Retrieved ${docs.length} documents`);
    } catch (err) {
      addResult('Database Query', 'failed', err.message);
    }

    // Test 3: Chat generation
    try {
      const res = await api.askQuestion('Test query', null, 1);
      addResult('RAG Ingestion & Gemini', 'success', 'Response received');
    } catch (err) {
      addResult('RAG Ingestion & Gemini', 'failed', err.message);
    }

    setDiagRunning(false);
  };

  return (
    <div className="app-container">
      {/* ================= HEADER ================= */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">
            <Bot size={20} color="#fff" />
          </div>
          <h1 className="brand-title">JPL RAG Console</h1>
          <span className="brand-tag">v1.0.0</span>
        </div>
        
        <div className="header-actions">
          {errorMsg && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f87171', fontSize: '13px', marginRight: '12px' }}>
              <AlertTriangle size={16} />
              <span>{errorMsg}</span>
              <X size={14} style={{ cursor: 'pointer' }} onClick={() => setErrorMsg('')} />
            </div>
          )}
          
          <button className="btn btn-primary" onClick={runDiagnostics} style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#fff', border: '1px solid rgba(255, 255, 255, 0.1)', marginRight: '10px' }} disabled={diagRunning}>
            <Activity size={15} />
            Run Diagnostics
          </button>

          <button className="btn btn-primary" onClick={handleCleanProcesses} style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#fff', border: '1px solid rgba(255, 255, 255, 0.1)', marginRight: '10px' }}>
            <RefreshCw size={15} />
            Clean Processes
          </button>

          <button className="btn btn-danger" onClick={handleReset}>
            <RotateCcw size={15} />
            Reset Workspace
          </button>
        </div>
      </header>

      {/* ================= MAIN CONTENT ================= */}
      <div className="main-content">
        {/* ================= SIDEBAR (DOCUMENTS) ================= */}
        <aside className="sidebar">
          {/* File Upload Dropzone */}
          <div className="sidebar-section">
            <h2 className="sidebar-section-title">Ingest Documents</h2>
            <div style={{ marginBottom: '10px' }} onClick={(e) => e.stopPropagation()}>
              <input 
                type="text" 
                placeholder="Category Name (Optional)"
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 'var(--radius-sm)',
                  color: '#fff',
                  fontSize: '13px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <div 
              className="dropzone-container"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                style={{ display: 'none' }} 
                accept=".pdf" 
                onChange={handleFileChange}
              />
              {uploading ? (
                <>
                  <RefreshCw size={24} className="dropzone-icon" style={{ animation: 'spin 1.5s linear infinite' }} />
                  <span className="dropzone-text">Uploading and Processing...</span>
                </>
              ) : (
                <>
                  <UploadCloud size={24} className="dropzone-icon" />
                  <span className="dropzone-text">Drag & Drop PDF or click to browse</span>
                  <span className="dropzone-subtext">PDF Files up to 50MB</span>
                </>
              )}
            </div>
          </div>

          {/* Category Workspaces */}
          <div className="sidebar-section" style={{ flex: 'none', display: 'flex', flexDirection: 'column' }}>
            <h2 className="sidebar-section-title">
              <span>Category Workspaces</span>
            </h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', padding: '6px 0' }}>
              {Array.from(new Set(documents.map(d => d.category).filter(Boolean))).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', padding: '4px 0' }}>
                  No active categories yet.
                </div>
              ) : (
                Array.from(new Set(documents.map(d => d.category).filter(Boolean))).map(cat => (
                  <button
                    key={cat}
                    className={`citation-pill ${selectedCategory === cat ? 'active-filter' : ''}`}
                    onClick={() => {
                      setSelectedCategory(selectedCategory === cat ? null : cat);
                      setSelectedDocId(null);
                    }}
                    style={{
                      border: selectedCategory === cat ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.1)',
                      background: selectedCategory === cat ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                      color: selectedCategory === cat ? '#60a5fa' : 'hsl(var(--text-muted))',
                      cursor: 'pointer',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                      outline: 'none'
                    }}
                  >
                    {cat}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Document Directory list */}
          <div className="sidebar-section" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <h2 className="sidebar-section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Document Directory</span>
              <span style={{ fontSize: '11px', textTransform: 'none', color: 'hsl(var(--text-muted))' }}>
                {documents.length} item(s)
              </span>
            </h2>
            
            <div className="document-list-container">
              {documents.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'hsl(var(--text-muted))', padding: '24px 0', fontSize: '13px' }}>
                  No documents uploaded yet.
                </div>
              ) : (
                documents.map(doc => (
                  <div 
                    key={doc.id} 
                    className={`document-card ${selectedDocId === doc.id ? 'active-filter' : ''}`}
                    onClick={() => {
                      setSelectedDocId(selectedDocId === doc.id ? null : doc.id);
                      setSelectedCategory(null);
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', minWidth: 0, flex: 1 }}>
                      <FileText size={18} style={{ color: selectedDocId === doc.id ? 'hsl(var(--primary-hover))' : 'hsl(var(--text-muted))' }} />
                      <div className="document-info">
                        <span className="document-name" title={doc.filename}>{doc.filename}</span>
                        <div className="document-meta" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                          <span>{formatBytes(doc.file_size)}</span>
                          <span className={`status-badge status-${doc.status}`}>
                            {doc.status}
                          </span>
                          {doc.category && (
                            <span className="status-badge" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                              {doc.category}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="document-actions">
                      <button 
                        className="btn btn-ghost" 
                        title="Delete Document"
                        onClick={(e) => handleDeleteDoc(doc.id, e)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>

        {/* ================= CHAT PANEL ================= */}
        <main className="chat-workspace">
          <div className="chat-history">
            {messages.length === 0 ? (
              <div className="welcome-screen">
                <div className="welcome-logo">
                  <FileCheck size={28} />
                </div>
                <h2 className="welcome-title">Enterprise Knowledge Navigator</h2>
                <p className="welcome-subtitle">
                  Upload document PDFs in the sidebar panel. Once processed, you can query across the dataset or select an individual file to lock vector searches to that document.
                </p>
              </div>
            ) : (
              messages.map(msg => (
                <div key={msg.id} className={`message-bubble ${msg.role}`}>
                  <div className="avatar">
                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  
                  <div className="message-content-wrapper">
                    <div className="message-text" style={msg.isError ? { borderLeft: '3px solid #ef4444' } : {}}>
                      {msg.text}
                    </div>

                    {/* Citations section if assistant response contains them */}
                    {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                      <div className="citations-panel">
                        <div className="citations-header">
                          <Database size={11} />
                          <span>Sources Grounding</span>
                        </div>
                        <div className="citations-list">
                          {msg.citations.map((cit, idx) => (
                            <button
                              key={idx}
                              className="citation-pill"
                              onClick={() => toggleCitation(msg.id, idx)}
                            >
                              <span>{getDocName(cit.document_id)}</span>
                              <span style={{ color: 'hsl(var(--text-muted))' }}>p.{cit.chunk_index}</span>
                              <span className="citation-score">{(cit.score * 100).toFixed(0)}%</span>
                            </button>
                          ))}
                        </div>

                        {/* Citation Detail Card */}
                        {activeCitation?.messageId === msg.id && (
                          <div className="citation-detail-card">
                            <div className="citation-detail-header">
                              <span>Source Segment {activeCitation.index + 1} ({getDocName(msg.citations[activeCitation.index].document_id)})</span>
                              <X 
                                size={12} 
                                style={{ cursor: 'pointer' }} 
                                onClick={() => setActiveCitation(null)} 
                              />
                            </div>
                            <div className="citation-detail-content">
                              "{msg.citations[activeCitation.index].content_preview}..."
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="message-bubble assistant">
                <div className="avatar">
                  <Bot size={16} />
                </div>
                <div className="message-content-wrapper">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* ================= CHAT INPUT ================= */}
          <div className="chat-input-container">
            <form onSubmit={handleSendQuestion}>
              <div className="input-box-wrapper">
                {selectedDocId && (
                  <div className="filter-badge">
                    <FileText size={12} />
                    <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {getSelectedDocName()}
                    </span>
                    <X 
                      size={12} 
                      style={{ cursor: 'pointer', marginLeft: '4px' }} 
                      onClick={() => setSelectedDocId(null)}
                    />
                  </div>
                )}
                {selectedCategory && (
                  <div className="filter-badge" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                    <Database size={12} />
                    <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      Workspace: {selectedCategory}
                    </span>
                    <X 
                      size={12} 
                      style={{ cursor: 'pointer', marginLeft: '4px' }} 
                      onClick={() => setSelectedCategory(null)}
                    />
                  </div>
                )}
                
                <input 
                  type="text"
                  className="chat-input"
                  placeholder="Ask a question about the document dataset..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={loading}
                />
                
                <div className="input-controls">
                  <button 
                    type="submit" 
                    className="btn btn-primary btn-icon-circle"
                    disabled={!question.trim() || loading}
                  >
                    <Send size={15} />
                  </button>
                </div>
              </div>
            </form>
          </div>
        </main>
      </div>
      {/* ================= DIAGNOSTIC MODAL ================= */}
      {diagResults && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
        }}>
          <div style={{
            background: 'hsl(var(--bg-card))', border: '1px solid rgba(255,255,255,0.08)',
            padding: '24px', borderRadius: 'var(--radius-lg)', width: '420px',
            boxShadow: 'var(--shadow-lg)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600 }}>System Diagnostics</h3>
              <button className="btn btn-ghost" onClick={() => setDiagResults(null)} disabled={diagRunning}>
                <X size={16} />
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
              {diagResults.map((r, idx) => (
                <div key={idx} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 12px', background: 'rgba(255,255,255,0.02)',
                  borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.04)'
                }}>
                  <span style={{ fontSize: '14px', fontWeight: 500 }}>{r.name}</span>
                  <span style={{
                    fontSize: '12px', fontWeight: 600,
                    color: r.status === 'success' ? '#34d399' : '#f87171'
                  }}>
                    {r.status === 'success' ? 'PASS' : 'FAIL'} ({r.message})
                  </span>
                </div>
              ))}
              {diagRunning && (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', padding: '10px 0', fontSize: '13px', color: 'hsl(var(--text-muted))' }}>
                  <RefreshCw size={14} style={{ animation: 'spin 1.5s linear infinite' }} />
                  <span>Running diagnostic suite...</span>
                </div>
              )}
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={() => setDiagResults(null)} disabled={diagRunning}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
