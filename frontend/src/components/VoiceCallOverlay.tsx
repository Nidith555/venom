import React from 'react';
import { Mic, MicOff, Radio, Volume2, PhoneOff, Sparkles } from 'lucide-react';
import { useChatStore } from '../store/chatStore';

export const VoiceCallOverlay: React.FC = () => {
  const {
    voiceCallActive,
    setVoiceCallActive,
    voiceStatus,
    voiceTranscript,
    isSpeaking,
    stopSpeaking,
  } = useChatStore();

  if (!voiceCallActive) return null;

  const getStatusLabel = () => {
    switch (voiceStatus) {
      case 'detected':
        return 'VENOM AWAKENED · LISTENING';
      case 'processing':
        return 'NEURAL LINK COMMUNICATING...';
      case 'speaking':
        return 'VENOM VOCALIZING...';
      case 'listening':
      default:
        return 'CALL "VENOM" · SYMBIOTE LISTENING';
    }
  };

  return (
    <div className="relative mx-4 sm:mx-6 mb-3 p-3 bg-[#0d0e12]/95 border border-[#00ff66]/30 shadow-[0_0_25px_rgba(0,255,102,0.15)] backdrop-blur-md transition-all duration-300">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Left Status & Waveform */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-sm bg-[#00ff66]/10 border border-[#00ff66]/40 text-[#00ff66]">
            {voiceStatus === 'speaking' ? (
              <Volume2 size={16} className="animate-pulse" />
            ) : (
              <Mic size={16} className={voiceStatus === 'detected' ? 'animate-bounce' : 'animate-pulse'} />
            )}
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[#00ff66] rounded-full animate-ping" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-['Orbitron'] font-bold tracking-widest text-[#00ff66]">
                {getStatusLabel()}
              </span>
              <span className="flex items-center gap-1 text-[9px] text-[#f4f4f6]/40 font-mono border border-[#f4f4f6]/10 px-1.5 py-0.2">
                <Sparkles size={8} />
                WAKE WORD: "VENOM"
              </span>
            </div>

            <div className="text-[11px] text-[#f4f4f6]/70 font-mono mt-0.5 truncate max-w-md sm:max-w-lg">
              {voiceTranscript ? (
                <span>&ldquo;{voiceTranscript}&rdquo;</span>
              ) : (
                <span className="text-[#f4f4f6]/40 italic">
                  Speak &ldquo;Venom...&rdquo; or ask anything hands-free
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Center/Right Animated Frequency Bars */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          <div className="flex items-center gap-1 h-5 px-2 bg-[#000000]/40 border border-[#f4f4f6]/10">
            {[40, 75, 55, 90, 60, 85, 45, 95, 65, 50].map((height, i) => (
              <div
                key={i}
                className="w-1 bg-[#00ff66] transition-all duration-150"
                style={{
                  height:
                    voiceStatus === 'speaking' || voiceStatus === 'detected'
                      ? `${height}%`
                      : `${Math.max(20, (height * 0.35))}%`,
                  opacity: voiceStatus === 'listening' ? 0.4 : 0.9,
                }}
              />
            ))}
          </div>

          {/* End Call Button */}
          <button
            onClick={() => {
              if (isSpeaking) stopSpeaking();
              setVoiceCallActive(false);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#ff0033]/20 hover:bg-[#ff0033]/30 text-[#ff0033] border border-[#ff0033]/40 text-[10px] font-['Orbitron'] font-bold tracking-widest uppercase transition-all"
            title="End Voice Call session"
          >
            <PhoneOff size={11} />
            <span>DISCONNECT</span>
          </button>
        </div>
      </div>
    </div>
  );
};
