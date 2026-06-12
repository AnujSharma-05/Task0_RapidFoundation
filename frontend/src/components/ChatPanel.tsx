import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, FileCheck, X, Database, FileText } from 'lucide-react';
import { Message, Document } from '../types';

interface ChatPanelProps {
  messages: Message[];
  loading: boolean;
  selectedDocument: Document | null;
  selectedCategory: string | null;
  onSendMessage: (question: string) => void;
  onClearDocument: () => void;
  onClearCategory: () => void;
  documents: Document[];
}

export function ChatPanel({
  messages,
  loading,
  selectedDocument,
  selectedCategory,
  onSendMessage,
  onClearDocument,
  onClearCategory,
  documents,
}: ChatPanelProps) {
  const [question, setQuestion] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [activeCitation, setActiveCitation] = useState<{msgId: number, idx: number} | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    onSendMessage(question);
    setQuestion('');
  };

  const getDocName = (id: number) => documents.find(d => d.id === id)?.filename || `Doc #${id}`;

  return (
    <main className="chat-workspace flex flex-col h-full">
      <div className="chat-history flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="welcome-screen flex flex-col items-center justify-center h-full text-center">
            <FileCheck size={48} className="mb-4 text-blue-500" />
            <h2 className="text-2xl font-bold mb-2">Enterprise Knowledge Navigator</h2>
            <p className="text-gray-400 max-w-md">Upload documents in the sidebar and start asking questions.</p>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`message-bubble ${msg.role} flex gap-4 mb-6`}>
              <div className="avatar mt-1">
                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div className="message-content flex-1">
                <div className={`p-4 rounded-lg ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-800'}`}>
                  {msg.text}
                </div>
                {msg.citations && msg.citations.length > 0 && (
                  <div className="citations mt-2">
                    <div className="text-xs text-gray-500 mb-1 flex items-center gap-1"><Database size={12}/> Sources</div>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((cit, idx) => (
                        <button 
                          key={idx} 
                          onClick={() => setActiveCitation(activeCitation?.msgId === msg.id && activeCitation.idx === idx ? null : {msgId: msg.id, idx})}
                          className="text-xs bg-gray-700 px-2 py-1 rounded border border-gray-600 hover:bg-gray-600"
                        >
                          {getDocName(cit.document_id)} (p.{cit.chunk_index})
                        </button>
                      ))}
                    </div>
                    {activeCitation?.msgId === msg.id && (
                      <div className="mt-2 p-3 bg-gray-900 border border-gray-700 rounded text-sm relative">
                        <button onClick={() => setActiveCitation(null)} className="absolute top-2 right-2"><X size={14}/></button>
                        <div className="font-bold text-xs mb-1 text-gray-400">Excerpt:</div>
                        "{msg.citations[activeCitation.idx].content_preview}"
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && <div className="text-gray-400 italic flex gap-2"><Bot size={20} /> Thinking...</div>}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-container p-4 border-t border-gray-800">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex gap-2 mb-2">
            {selectedDocument && (
              <span className="flex items-center gap-1 bg-blue-900/30 text-blue-400 px-2 py-1 rounded text-xs border border-blue-800">
                <FileText size={12}/> {selectedDocument.filename} 
                <X size={12} className="cursor-pointer ml-1 hover:text-white" onClick={onClearDocument}/>
              </span>
            )}
            {selectedCategory && (
              <span className="flex items-center gap-1 bg-purple-900/30 text-purple-400 px-2 py-1 rounded text-xs border border-purple-800">
                <Database size={12}/> {selectedCategory} 
                <X size={12} className="cursor-pointer ml-1 hover:text-white" onClick={onClearCategory}/>
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <input 
              type="text" 
              className="flex-1 bg-gray-800 border border-gray-700 rounded p-3 text-white outline-none focus:border-blue-500"
              placeholder="Ask a question..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={!question.trim() || loading} className="bg-blue-600 text-white p-3 rounded hover:bg-blue-700 disabled:opacity-50">
              <Send size={20} />
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
