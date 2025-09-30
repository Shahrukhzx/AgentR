'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ResponseDisplay } from '@/components/rover/ResponseDisplay';
import { QueryInput } from '@/components/rover/QueryInput';
import { ParticlesBackground } from '@/components/ui/ParticlesBackground';
import { ToggleSwitch } from '@/components/ui/ToggleSwitch';

interface Message {
  type: 'thought' | 'action' | 'dom_update' | 'interaction' | 'browser_action' | 
        'rag_action' | 'review' | 'close_tab' | 'subtopics' | 'subtopic_answer' |
        'subtopic_status' | 'compile' | 'final_answer' | 'conversation_history' |
        'cleanup' | 'error' | 'final_response' | 'user_input';
  content: string;
}

type AgentType = 'research' | 'deep_research';

export default function AgentPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const currentAgent: AgentType = 'deep_research';

  const handleDisconnect = async () => {
    try {
      const response = await fetch('http://localhost:8000/cleanup', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to cleanup browser');
      }
      
      await router.push('/');
    } catch (error) {
      console.error('Failed to cleanup browser:', error);
      // Still try to navigate even if cleanup fails
      await router.push('/');
    }
  };

  const handleStreamingResponse = async (response: Response) => {
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response reader');

    const decoder = new TextDecoder();
    let buffer = '';

    const processSSEMessage = (message: string) => {
      try {
        const jsonStr = message.replace(/^data: /, '').trim();
        const data = JSON.parse(jsonStr);
        
        if (data.type === 'keepalive') return;
        
        // Clean content if it matches the pattern
        const cleanContent = (content: any) => {
          if (content == null) return ''; // handle null or undefined safely
          // If content is already an array, return it directly
          if (Array.isArray(content)) {
            return content;
          }
          
          if (typeof content === 'string') {
            try {
              // Try to parse as JSON
              const parsed = JSON.parse(content);
              if (Array.isArray(parsed)) {
                return parsed;
              }
              // If it's a string with ["..."] pattern
              if (content.startsWith('["') && content.endsWith('"]')) {
                return content.slice(2, -2);
              }
            } catch {
              // If parsing fails and it has the pattern
              if (content.startsWith('["') && content.endsWith('"]')) {
                return content.slice(2, -2);
              }
            }
          }
          return content;
        };

        const processedData = {
          type: data.type || 'unknown',
          content: cleanContent(data.content)
        };
        
        switch (data.type) {
          case 'thought':
          case 'action':
          case 'browser_action':
          case 'final_answer':
          case 'final_response':
          case 'dom_update':
          case 'interaction':
          case 'rag_action':
          case 'review':
          case 'close_tab':
          case 'cleanup':
          case 'subtopics':
          case 'subtopic_answer':
          case 'subtopic_status':
          case 'compile':
          case 'error':
            setMessages((prev) => [...prev, processedData]);
            break;
          default:
            console.warn('Unhandled SSE type:', data.type, data);
        }
      } catch (e) {
        console.error('Failed to parse SSE message:', message, e);
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      // Find complete SSE messages
      const messages = buffer.match(/data: {[\s\S]*?}\n\n/g);
      
      if (messages) {
        messages.forEach(processSSEMessage);
        // Remove processed messages from buffer
        buffer = buffer.slice(buffer.lastIndexOf('}') + 1);
      }
    }
  };

  const handleSubmit = async (e?: React.FormEvent<HTMLFormElement>) => {
    if (e) {
      e.preventDefault();
    }
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    // Add user message to the chat history
    setMessages(prev => [...prev, { type: 'user_input', content: query }]);
    const currentQuery = query;
    setQuery(''); // Clear input after sending

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: currentQuery,
          agent_type: currentAgent 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send query');
      }

      await handleStreamingResponse(response);
    } catch (error: any) {
      console.error('Query failed:', error);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: error?.message || 'Failed to process query. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-slate-950 via-indigo-950/20 to-black">
      
      {/* Header with Toggles */}
      <header className="fixed top-0 left-0 right-0 p-4 backdrop-blur-xl bg-black/30 z-50
                      border-b border-zinc-800/50 shadow-lg shadow-black/20">
        <div className="flex justify-between items-center max-w-[1600px] mx-auto">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 
                        text-transparent bg-clip-text animate-flow bg-[length:200%_auto]">
            AgentR
          </h1>
          

          <button
            onClick={handleDisconnect}
            className="px-4 py-2 rounded-full whitespace-nowrap
                     bg-gradient-to-r from-rose-500/10 to-pink-500/10
                     border border-rose-500/50 text-rose-400
                     hover:bg-rose-500/20 hover:border-rose-500/70 hover:text-rose-300
                     transition-all duration-300"
          >
            Disconnect Browser
          </button>
        </div>
      </header>

      {/* Input Bar */}
      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-40 w-full max-w-[800px] px-4">
        <QueryInput
          value={query}
          onChange={setQuery}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>

      {/* Main Content */}
      <main className="relative pt-24 pb-32 z-10 overflow-y-auto h-[calc(100vh-140px)]">
        <div className="w-full pb-16">
          <ResponseDisplay messages={messages} />
        </div>
      </main>
      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed top-20 right-4 z-50 px-4 py-2 rounded-lg bg-black/80 backdrop-blur-sm 
                       border border-indigo-500/30 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-indigo-400">Processing query...</span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {messages.length === 0 && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center pt-24 pb-32">
          <div className="text-center max-w-md mx-auto px-6">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 
                           border border-indigo-500/30 flex items-center justify-center">
              <svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Ready to Research</h3>
            <p className="text-zinc-400 mb-6">
              Ask me anything and I'll use advanced research capabilities to find comprehensive answers.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-sm">
                Deep Research
              </span>
              <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-sm">
                Web Browsing
              </span>
              <span className="px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/30 text-pink-400 text-sm">
                Real-time Data
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}