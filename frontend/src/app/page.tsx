'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { SpotlightCard } from '@/components/ui/SpotlightCard';

export default function Home() {
  const router = useRouter();
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    setIsConnecting(true);
    setError(null);
    
    try {
      console.log('Attempting to connect...');
      const response = await fetch('http://localhost:8000/setup-browser', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: 'https://www.google.com' }),
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to setup browser');
      }

      console.log('Connection successful, redirecting...');
      await router.push('/agent');
    } catch (error) {
      console.error('Failed to connect:', error);
      setError(error instanceof Error ? error.message : 'Failed to connect to browser');
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6">
      <div className="w-full max-w-4xl mx-auto">
        
        <SpotlightCard 
          className="backdrop-blur-sm bg-white/5 border border-white/10 shadow-2xl"
          spotlightColor="rgba(59, 130, 246, 0.1)"
          gradient="from-blue-500/5 via-indigo-500/5 to-purple-500/5"
        >
          <div className="p-12 md:p-16">
            
            {/* Clean header */}
            <div className="text-center mb-16">
              <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
                <span className="bg-gradient-to-r from-blue-400 via-purple-500 to-indigo-400 text-transparent bg-clip-text">
                  AgentR
                </span>
              </h1>
              
              <p className="text-xl md:text-2xl text-zinc-300 font-light tracking-wide">
                Your AI Co-pilot for Web Research
              </p>
              <div className="w-24 h-0.5 bg-gradient-to-r from-transparent via-blue-500 to-transparent mx-auto mt-4"></div>
            </div>

            {/* Capabilities grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
              
              <div className="space-y-6">
                <div className="p-6 rounded-xl bg-gradient-to-br from-blue-500/10 to-transparent border border-blue-500/20 hover:border-blue-500/40 transition-all duration-300">
                  <div className="flex items-center mb-4">
                    <div className="text-3xl mr-3">🧭</div>
                    <div>
                      <h3 className="text-lg font-semibold text-zinc-100 mb-1">Autonomous Web Exploration</h3>
                      <div className="w-12 h-0.5 bg-blue-500"></div>
                    </div>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed">
                    AgentR intelligently navigates complex web data streams, pinpointing the most relevant and trustworthy sources — empowering your research journey with precision.
                  </p>
                </div>

                <div className="p-6 rounded-xl bg-gradient-to-br from-purple-500/10 to-transparent border border-purple-500/20 hover:border-purple-500/40 transition-all duration-300">
                  <div className="flex items-center mb-4">
                    <div className="text-3xl mr-3">📚</div>
                    <div>
                      <h3 className="text-lg font-semibold text-zinc-100 mb-1">AI-Powered Research</h3>
                      <div className="w-12 h-0.5 bg-purple-500"></div>
                    </div>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed">
                    Convert scattered information into cohesive, insightful summaries. AgentR synthesizes findings into crisp narratives, accelerating your understanding and writing.
                  </p>
                </div>
              </div>

              <div className="space-y-6">
                <div className="p-6 rounded-xl bg-gradient-to-br from-indigo-500/10 to-transparent border border-indigo-500/20 hover:border-indigo-500/40 transition-all duration-300">
                  <div className="flex items-center mb-4">
                    <div className="text-3xl mr-3">🤖</div>
                    <div>
                      <h3 className="text-lg font-semibold text-zinc-100 mb-1">Context-Aware Language Intelligence</h3>
                      <div className="w-12 h-0.5 bg-indigo-500"></div>
                    </div>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed">
                    Leveraging advanced language models, AgentR comprehends nuance and context, guiding each interaction with intelligent, adaptive responses.
                  </p>
                </div>

                <div className="p-6 rounded-xl bg-gradient-to-br from-cyan-500/10 to-transparent border border-cyan-500/20 hover:border-cyan-500/40 transition-all duration-300">
                  <div className="flex items-center mb-4">
                    <div className="text-3xl mr-3">⚡</div>
                    <div>
                      <h3 className="text-lg font-semibold text-zinc-100 mb-1">Real-Time Browser Streaming</h3>
                      <div className="w-12 h-0.5 bg-cyan-500"></div>
                    </div>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed">
                    Watch live streams of AgentR’s browsing process as it explores, extracts, and analyzes web content — keeping you connected to every step in real time.
                  </p>
                </div>
              </div>
            </div>

            {/* Connection interface */}
            <div className="text-center">

              <button
                onClick={handleConnect}
                disabled={isConnecting}
                className="w-full p-6 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-lg hover:shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <div className="flex items-center justify-center space-x-3">
                  {isConnecting ? (
                    <>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce delay-100"></div>
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce delay-200"></div>
                      </div>
                      <span>Connecting To Browser</span>
                    </>
                  ) : (
                    <>
                      <span>Connect to Browser</span>
                    </>
                  )}
                </div>
              </button>

              {error && (
                <div className="mt-6 p-4 bg-red-900/20 border border-red-500/30 rounded-xl">
                  <div className="flex items-center space-x-3">
                    <div className="text-red-400 text-xl">⚠️</div>
                    <div className="text-left">
                      <p className="text-red-300 font-medium text-sm">SYSTEM ERROR DETECTED</p>
                      <p className="text-red-400 text-xs font-mono">{error}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}