import { useState } from 'react';
import { api } from '../services/api';
import { Message, ChatRequest } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (request: ChatRequest) => {
    const userMsgId = Date.now();
    const newMessages: Message[] = [
      ...messages,
      { id: userMsgId, role: 'user', text: request.question },
    ];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response = await api.askQuestion(request);
      setMessages([
        ...newMessages,
        {
          id: userMsgId + 1,
          role: 'assistant',
          text: response.answer,
          citations: response.citations,
        },
      ]);
    } catch (err: any) {
      setMessages([
        ...newMessages,
        {
          id: userMsgId + 1,
          role: 'assistant',
          text: err.message || 'An error occurred',
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => setMessages([]);

  return { messages, sendMessage, loading, clearChat };
}
