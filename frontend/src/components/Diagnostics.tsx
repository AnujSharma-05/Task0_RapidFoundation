import React, { useState } from 'react';
import { X, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { DiagResult } from '../types';

interface DiagnosticsProps {
  onClose: () => void;
}

export function Diagnostics({ onClose }: DiagnosticsProps) {
  const [results, setResults] = useState<DiagResult[]>([]);
  const [running, setRunning] = useState(false);

  const runDiagnostics = async () => {
    setRunning(true);
    setResults([]);
    const newResults: DiagResult[] = [];

    const addResult = (name: string, status: 'success' | 'failed', message: string) => {
      newResults.push({ name, status, message });
      setResults([...newResults]);
    };

    try {
      const res = await fetch('http://127.0.0.1:8000/ping');
      if (res.ok) addResult('Backend Ping', 'success', 'Connection alive');
      else addResult('Backend Ping', 'failed', `Status ${res.status}`);
    } catch {
      addResult('Backend Ping', 'failed', 'Connection refused');
    }

    try {
      const docs = await api.fetchDocuments();
      addResult('Database Query', 'success', `Retrieved ${docs.length} documents`);
    } catch (err: any) {
      addResult('Database Query', 'failed', err.message);
    }

    try {
      await api.askQuestion({ question: 'Test', top_k: 5 });
      addResult('RAG Ingestion & Gemini', 'success', 'Response received');
    } catch (err: any) {
      addResult('RAG Ingestion & Gemini', 'failed', err.message);
    }

    setRunning(false);
  };

  React.useEffect(() => {
    runDiagnostics();
  }, []);

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl w-[420px] shadow-2xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">System Diagnostics</h3>
          <button onClick={onClose} disabled={running}><X size={16} /></button>
        </div>
        
        <div className="flex flex-col gap-3 mb-5">
          {results.map((r, i) => (
            <div key={i} className="flex justify-between items-center p-3 bg-gray-800/50 rounded border border-gray-700/50">
              <span className="text-sm font-medium">{r.name}</span>
              <span className={`text-xs font-bold ${r.status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                {r.status === 'success' ? 'PASS' : 'FAIL'} ({r.message})
              </span>
            </div>
          ))}
          {running && <div className="flex justify-center items-center gap-2 text-sm text-gray-500 py-2"><RefreshCw size={14} className="animate-spin" /> Running tests...</div>}
        </div>
        
        <div className="flex justify-end">
          <button onClick={onClose} disabled={running} className="bg-blue-600 px-4 py-2 rounded text-sm hover:bg-blue-700">Close</button>
        </div>
      </div>
    </div>
  );
}
