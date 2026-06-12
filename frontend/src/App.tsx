import React, { useState } from 'react';
import { Bot, RotateCcw, Activity, RefreshCw } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { ChatPanel } from './components/ChatPanel';
import { Diagnostics } from './components/Diagnostics';
import { useDocuments } from './hooks/useDocuments';
import { useChat } from './hooks/useChat';
import { api } from './services/api';

function App() {
  const { documents, loadDocuments, error: docError, setError: setDocError } = useDocuments();
  const { messages, sendMessage, loading: chatLoading, clearChat } = useChat();

  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  const handleReset = async () => {
    if (!confirm('Warning: This will delete all data. Proceed?')) return;
    try {
      await api.resetSystem();
      clearChat();
      loadDocuments();
      setSelectedDocId(null);
      setSelectedCategory(null);
    } catch {
      setDocError('Failed to reset system.');
    }
  };

  const handleClean = async () => {
    try {
      const res = await api.cleanSystem();
      alert(`System Cleared!\nZombies Killed: ${res.zombies_killed}`);
    } catch {
      setDocError('Failed to clean system.');
    }
  };

  const selectedDocument = documents.find(d => d.id === selectedDocId) || null;

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0c] text-white overflow-hidden">
      <header className="flex justify-between items-center px-6 py-4 border-b border-gray-800 bg-[#0d0d12]">
        <div className="flex items-center gap-3">
          <Bot className="text-blue-500" />
          <h1 className="text-xl font-semibold">JPL RAG Console</h1>
          <span className="text-xs bg-blue-900/40 text-blue-400 px-2 py-0.5 rounded border border-blue-800">v1.0.0 (TSX)</span>
        </div>
        <div className="flex items-center gap-3">
          {docError && <span className="text-red-400 text-sm">{docError}</span>}
          <button onClick={() => setShowDiagnostics(true)} className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded transition-colors"><Activity size={14}/> Diagnostics</button>
          <button onClick={handleClean} className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded transition-colors"><RefreshCw size={14}/> Clean Processes</button>
          <button onClick={handleReset} className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-900/50 hover:bg-red-900/80 text-red-300 border border-red-800/50 rounded transition-colors"><RotateCcw size={14}/> Reset Workspace</button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          documents={documents}
          selectedCategory={selectedCategory}
          selectedDocId={selectedDocId}
          onSelectCategory={setSelectedCategory}
          onSelectDocument={setSelectedDocId}
          onRefreshDocuments={loadDocuments}
          onError={setDocError}
        />
        <div className="flex-1 flex flex-col border-l border-gray-800">
          <ChatPanel 
            messages={messages}
            loading={chatLoading}
            selectedDocument={selectedDocument}
            selectedCategory={selectedCategory}
            documents={documents}
            onSendMessage={(q) => sendMessage({ question: q, document_id: selectedDocId, category: selectedCategory })}
            onClearDocument={() => setSelectedDocId(null)}
            onClearCategory={() => setSelectedCategory(null)}
          />
        </div>
      </div>

      {showDiagnostics && <Diagnostics onClose={() => setShowDiagnostics(false)} />}
    </div>
  );
}

export default App;
