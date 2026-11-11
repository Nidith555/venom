import React, { useEffect, useState } from 'react';
import { VenomBackground } from './components/VenomBackground';
import { Sidebar } from './components/Sidebar';
import { StatusBar } from './components/StatusBar';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { VoiceCallOverlay } from './components/VoiceCallOverlay';
import { SymbioteLoader } from './components/SymbioteLoader';
import { useWebSocket } from './hooks/useWebSocket';
import { useVoiceWake } from './hooks/useVoiceWake';
import { useChatStore } from './store/chatStore';

import { getApiUrl } from './config/api';

export const App: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const { activeNav, fetchInitialState, currentModel } = useChatStore();

  useWebSocket();
  useVoiceWake();

  useEffect(() => {
    fetchInitialState();
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1200);
    return () => clearTimeout(timer);
  }, [fetchInitialState]);

  // Handle URL Wake Word launch (?wake=true)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const isWake = urlParams.get('wake') === 'true';
    const cmd = urlParams.get('cmd');

    if (isWake) {
      window.history.replaceState({}, document.title, window.location.pathname);
      const timer = setTimeout(async () => {
        useChatStore.getState().setVoiceCallActive(true);
        if (cmd) {
          useChatStore.getState().sendMessage(cmd);
        } else {
          const greeting = "We are Venom. What do you require, host?";
          const greetingId = `ast-wake-${Date.now()}`;
          useChatStore.setState((state) => ({
            messages: [
              ...state.messages,
              {
                id: greetingId,
                role: 'assistant',
                content: greeting,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              },
            ],
          }));
          await useChatStore.getState().speakMessage(greetingId, greeting);
        }
      }, 1400);
      return () => clearTimeout(timer);
    }
  }, []);

  // Listen for background desktop wake events when page is already open
  useEffect(() => {
    let lastHandledTs = Date.now() / 1000;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(getApiUrl('/api/voice/wake'));
        if (res.ok) {
          const data = await res.json();
          if (data.timestamp && data.timestamp > lastHandledTs) {
            lastHandledTs = data.timestamp;
            useChatStore.getState().setVoiceCallActive(true);
            if (data.command) {
              useChatStore.getState().sendMessage(data.command);
            } else {
              const greeting = "We are Venom. What do you require, host?";
              const greetingId = `ast-wake-${Date.now()}`;
              useChatStore.setState((state) => ({
                messages: [
                  ...state.messages,
                  {
                    id: greetingId,
                    role: 'assistant',
                    content: greeting,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  },
                ],
              }));
              await useChatStore.getState().speakMessage(greetingId, greeting);
            }
          }
        }
      } catch {}
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <SymbioteLoader />;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#000000] text-[#f4f4f6] relative font-mono">
      {/* Dynamic Symbiote Spider Web Canvas */}
      <VenomBackground />

      {/* Main UI Layout */}
      <div className="relative z-10 flex w-full h-full">
        {/* Left Sidebar */}
        <Sidebar />

        {/* Content Area */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#000000]/60 backdrop-blur-sm">
          <StatusBar />

          {activeNav === 'chat' && (
            <>
              <ChatWindow />
              <VoiceCallOverlay />
              <ChatInput />
            </>
          )}

          {activeNav === 'memory' && (
            <div className="flex-1 p-8 overflow-y-auto">
              <h2 className="text-xl font-black tracking-widest font-['Orbitron'] mb-4 text-[#f4f4f6]">
                SYMBIOTIC MEMORY VAULT
              </h2>
              <p className="text-xs text-[#f4f4f6]/50 mb-6">
                Direct neural memory traces retained across turns with the host.
              </p>
              <div className="bg-[#111214] border border-[#f4f4f6]/10 p-6">
                <div className="text-xs text-[#f4f4f6]/70 leading-relaxed space-y-2">
                  <div className="flex justify-between border-b border-[#f4f4f6]/10 pb-2">
                    <span className="font-bold">STATUS</span>
                    <span className="text-[#00ff66]">ACTIVE</span>
                  </div>
                  <div className="flex justify-between border-b border-[#f4f4f6]/10 pb-2">
                    <span className="font-bold">CAPACITY</span>
                    <span>50 CONVERSATION TURNS</span>
                  </div>
                  <div className="flex justify-between border-b border-[#f4f4f6]/10 pb-2">
                    <span className="font-bold">VECTOR STORE</span>
                    <span>CHROMADB (HYBRID)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeNav === 'models' && (
            <div className="flex-1 p-8 overflow-y-auto">
              <h2 className="text-xl font-black tracking-widest font-['Orbitron'] mb-4 text-[#f4f4f6]">
                NEURAL ENGINES & CATALOG
              </h2>
              <p className="text-xs text-[#f4f4f6]/50 mb-6">
                Manage local hardware inference runtimes (Ollama, vLLM, llama.cpp) and cloud APIs (Gemini, OpenAI).
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#111214] border border-[#f4f4f6]/15 p-5">
                  <div className="text-xs uppercase tracking-widest text-[#00ff66] mb-1 font-bold">
                    Connected
                  </div>
                  <div className="text-base font-bold font-['Orbitron']">{currentModel}</div>
                  <div className="text-xs text-[#f4f4f6]/40 mt-2 font-mono">
                    Active Symbiote Inference Runtime
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeNav === 'tools' && (
            <div className="flex-1 p-8 overflow-y-auto">
              <h2 className="text-xl font-black tracking-widest font-['Orbitron'] mb-4 text-[#f4f4f6]">
                SYMBIOTE EXTENSIONS & TOOLS
              </h2>
              <p className="text-xs text-[#f4f4f6]/50 mb-6">
                Model Context Protocol (MCP) and built-in symbiote capabilities.
              </p>
              <div className="space-y-3">
                {['Web Retrieval Engine', 'Voice Wake & Recognition', 'ElevenLabs Neural Vocalizer', 'File System I/O', 'Telemetry Monitor'].map(
                  (tool) => (
                    <div
                      key={tool}
                      className="bg-[#111214] border border-[#f4f4f6]/10 p-4 flex justify-between items-center"
                    >
                      <span className="text-xs font-bold font-mono">{tool}</span>
                      <span className="text-[10px] text-[#00ff66] bg-[#00ff66]/10 px-2 py-0.5 uppercase tracking-widest border border-[#00ff66]/20">
                        Bonded
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>
          )}

          {activeNav === 'settings' && (
            <div className="flex-1 p-8 overflow-y-auto">
              <h2 className="text-xl font-black tracking-widest font-['Orbitron'] mb-4 text-[#f4f4f6]">
                HOST & SYMBIOTE CONFIGURATION
              </h2>
              <p className="text-xs text-[#f4f4f6]/50 mb-6">
                Adjust system directives, temperature, voice wake word, and backend endpoints.
              </p>
              <div className="bg-[#111214] border border-[#f4f4f6]/10 p-6 space-y-4 max-w-xl text-xs font-mono">
                <div>
                  <label className="block text-[#f4f4f6]/60 mb-1">VOICE WAKE WORD</label>
                  <input
                    type="text"
                    disabled
                    value='Say "Venom" or "Hey Venom"'
                    className="w-full bg-[#0a0a0c] border border-[#f4f4f6]/15 px-3 py-2 text-[#00ff66]"
                  />
                </div>
                <div>
                  <label className="block text-[#f4f4f6]/60 mb-1">ELEVENLABS VOICE ID</label>
                  <input
                    type="text"
                    disabled
                    value="cgSgspJ2msm6clMCkdW9 (Venom Custom Voice)"
                    className="w-full bg-[#0a0a0c] border border-[#f4f4f6]/15 px-3 py-2 text-[#f4f4f6]"
                  />
                </div>
                <div>
                  <label className="block text-[#f4f4f6]/60 mb-1">SERVER PORT</label>
                  <input
                    type="text"
                    disabled
                    value="7777"
                    className="w-full bg-[#0a0a0c] border border-[#f4f4f6]/15 px-3 py-2 text-[#f4f4f6]"
                  />
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
