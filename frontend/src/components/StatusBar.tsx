import React from 'react';
import { Trash2, Volume2, VolumeX, Radio, Mic, MicOff, PhoneCall } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useVoiceWake } from '../hooks/useVoiceWake';

export const StatusBar: React.FC = () => {
  const {
    messages,
    currentModel,
    setModel,
    availableModels,
    clearHistory,
    voiceEnabled,
    toggleVoice,
    isSpeaking,
    voiceId,
  } = useChatStore();

  const { isSupported, voiceCallActive, toggleVoiceCall, voiceStatus } = useVoiceWake();

  const exchangeCount = Math.floor(messages.filter((m) => m.role === 'user').length);

  return (
    <header className="h-14 bg-[#0a0a0c]/80 border-b border-[#f4f4f6]/10 px-4 sm:px-6 flex items-center justify-between backdrop-blur-md relative z-10">
      <div className="flex items-center gap-3">
        <span className="text-xs tracking-[0.25em] text-[#f4f4f6]/90 font-['Orbitron'] font-bold uppercase glitch-title">
          WE ARE VENOM
        </span>

        {isSpeaking && (
          <span className="flex items-center gap-1.5 px-2 py-0.5 bg-[#00ff66]/10 border border-[#00ff66]/30 text-[#00ff66] text-[10px] tracking-widest font-mono uppercase animate-pulse">
            <Radio size={10} />
            <span>VOCALIZING</span>
          </span>
        )}

        {voiceCallActive && !isSpeaking && (
          <span className="flex items-center gap-1.5 px-2 py-0.5 bg-[#00ff66]/15 border border-[#00ff66]/40 text-[#00ff66] text-[10px] tracking-widest font-mono uppercase animate-pulse">
            <Mic size={10} />
            <span>LISTENING FOR "VENOM"</span>
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 sm:gap-3 text-xs font-mono">
        <span className="text-[#f4f4f6]/40 hidden lg:inline">
          {exchangeCount} {exchangeCount === 1 ? 'turn' : 'turns'}
        </span>

        {/* Voice Call / Wake Word Button */}
        {isSupported && (
          <button
            onClick={toggleVoiceCall}
            title={voiceCallActive ? 'Voice Call Active (Say "Venom" to talk)' : 'Start Hands-Free Voice Call (Wake word: "Venom")'}
            className={`flex items-center gap-1.5 px-3 py-1 transition-all text-[11px] tracking-wider uppercase border font-['Orbitron'] font-bold ${
              voiceCallActive
                ? 'bg-[#00ff66] text-[#000000] border-[#00ff66] shadow-[0_0_15px_#00ff66]'
                : 'bg-[#111214] text-[#00ff66] border-[#00ff66]/30 hover:bg-[#00ff66]/10'
            }`}
            style={{
              clipPath: 'polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px)',
            }}
          >
            <PhoneCall size={12} className={voiceCallActive ? 'animate-bounce' : ''} />
            <span>{voiceCallActive ? 'CALL: ACTIVE' : 'CALL "VENOM"'}</span>
          </button>
        )}

        {/* ElevenLabs Voice Audio Output Toggle */}
        <button
          onClick={toggleVoice}
          title={`ElevenLabs Voice: ${voiceId} (${voiceEnabled ? 'Audio Output On' : 'Muted'})`}
          className={`flex items-center gap-1.5 px-2.5 py-1 transition-all text-[11px] tracking-wider uppercase border ${
            voiceEnabled
              ? 'bg-[#00ff66]/10 text-[#00ff66] border-[#00ff66]/30 shadow-[0_0_10px_rgba(0,255,102,0.15)]'
              : 'bg-transparent text-[#f4f4f6]/30 border-[#f4f4f6]/10 hover:text-[#f4f4f6]'
          }`}
          style={{
            clipPath: 'polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px)',
          }}
        >
          {voiceEnabled ? <Volume2 size={13} /> : <VolumeX size={13} />}
          <span className="hidden md:inline font-['Orbitron'] text-[10px]">
            {voiceEnabled ? 'VOICE ON' : 'MUTED'}
          </span>
        </button>

        {/* Model dropdown */}
        <select
          value={currentModel}
          onChange={(e) => setModel(e.target.value)}
          className="bg-[#111214] text-[#f4f4f6] text-[11px] px-2.5 py-1 border border-[#f4f4f6]/15 outline-none tracking-wider font-mono cursor-pointer"
          style={{
            clipPath: 'polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px)',
          }}
        >
          {availableModels.map((m) => (
            <option key={m} value={m} className="bg-[#111214] text-[#f4f4f6]">
              {m}
            </option>
          ))}
        </select>

        {/* Clear chat button */}
        <button
          onClick={clearHistory}
          title="Sever current memory"
          className="flex items-center gap-1.5 px-2.5 py-1 bg-transparent hover:bg-[#ff0033]/15 text-[#f4f4f6]/40 hover:text-[#ff0033] border border-[#f4f4f6]/10 hover:border-[#ff0033]/40 transition-colors text-[11px] tracking-wider uppercase"
          style={{
            clipPath: 'polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px)',
          }}
        >
          <Trash2 size={12} />
          <span className="hidden sm:inline">Purge</span>
        </button>
      </div>
    </header>
  );
};
