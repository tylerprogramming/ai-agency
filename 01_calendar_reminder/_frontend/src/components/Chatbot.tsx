import React, { useState, useRef, useEffect } from 'react';
import { Bot, User, Send, Loader2, Calendar, Clock } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: Date;
}

interface ChatbotProps {
  calendarEvents?: any[];
  userName?: string;
}

export const Chatbot: React.FC<ChatbotProps> = ({ calendarEvents, userName }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  // Add welcome message on component mount
  useEffect(() => {
    const welcomeMessage: Message = {
      role: 'assistant',
      content: `Hello ${userName || 'there'}! 👋 I'm your calendar assistant. I can help you with:\n\n📅 Finding events in your calendar\n⏰ Checking your schedule\n📊 Summarizing your day\n❓ Answering calendar questions\n\nWhat would you like to know about your schedule?`,
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
  }, [userName]);

  const openaiKey = typeof window !== 'undefined' ? localStorage.getItem('openai_api_key') : null;

  const scrollToBottom = () => {
    setTimeout(() => {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const systemPrompt: Message = {
    role: 'system',
    content: `You are a helpful assistant that can answer questions about the user's Google Calendar. If asked, you can summarize, find events, or help schedule. The user's name is ${userName || 'User'}.`,
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || !openaiKey) return;
    
    setError(null);
    const userMessage = input.trim();
    const newMessages = [systemPrompt, ...messages, { role: 'user' as const, content: userMessage }] as Message[];
    
    setMessages(prev => [...prev, { role: 'user', content: userMessage, timestamp: new Date() }]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages, openai_api_key: openaiKey }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response');
      }
      
      const data = await response.json();
      const assistantMsg = data.response || 'I apologize, but I encountered an issue generating a response.';
      
      setMessages(prev => [...prev, { role: 'assistant', content: assistantMsg, timestamp: new Date() }]);
      scrollToBottom();
      
    } catch (err: any) {
      console.error('Chat error:', err);
      setError(err.message || 'Error getting response');
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again or check your settings.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  // Quick action suggestions
  const quickActions = [
    "What's on my schedule today?",
    "Show me tomorrow's events",
    "Summarize my week",
    "What's my next meeting?"
  ];

  const handleQuickAction = (action: string) => {
    setInput(action);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col h-[600px] max-w-2xl mx-auto bg-white rounded-xl shadow-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-full">
            <Calendar size={20} className="text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Calendar Assistant</h3>
            <p className="text-sm text-gray-600">Ask me about your schedule</p>
          </div>
        </div>
        <div className="text-xs text-gray-500">
          {calendarEvents ? `${calendarEvents.length} events loaded` : 'Ready to help'}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex items-start space-x-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="p-2 bg-blue-100 rounded-full flex-shrink-0">
                <Bot size={16} className="text-blue-600" />
              </div>
            )}
            <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-[80%]`}>
              <div
                className={`px-4 py-3 rounded-2xl text-sm whitespace-pre-line shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white rounded-br-md'
                    : 'bg-gray-100 text-gray-900 rounded-bl-md border'
                }`}
              >
                {msg.content}
              </div>
              {msg.timestamp && (
                <span className="text-xs text-gray-400 mt-1 px-2">
                  {formatTime(msg.timestamp)}
                </span>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="p-2 bg-blue-500 rounded-full flex-shrink-0">
                <User size={16} className="text-white" />
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-blue-100 rounded-full">
              <Bot size={16} className="text-blue-600" />
            </div>
            <div className="flex items-center space-x-2 px-4 py-3 bg-gray-100 rounded-2xl rounded-bl-md border">
              <Loader2 size={16} className="animate-spin text-gray-600" />
              <span className="text-sm text-gray-600">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Quick Actions */}
      {messages.length <= 1 && !loading && (
        <div className="px-4 py-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Quick questions:</p>
          <div className="flex flex-wrap gap-2">
            {quickActions.map((action, i) => (
              <button
                key={i}
                onClick={() => handleQuickAction(action)}
                className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
                disabled={!openaiKey}
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error/Warning */}
      {(!openaiKey || error) && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-100">
          <div className="text-red-700 text-sm flex items-center space-x-2">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span>{!openaiKey ? 'Please add your OpenAI API key in Settings to use the chatbot.' : error}</span>
          </div>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSend} className="flex items-center border-t border-gray-200 p-4 gap-3 bg-gray-50 rounded-b-xl">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white shadow-sm"
          placeholder={openaiKey ? "Ask me about your calendar..." : "Add OpenAI API key in Settings first"}
          disabled={loading || !openaiKey}
        />
        <button
          type="submit"
          className="p-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center justify-center"
          disabled={loading || !input.trim() || !openaiKey}
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </button>
      </form>
    </div>
  );
}; 