import React, { useState, useRef, useEffect } from 'react';
import { CornerDownLeft, Mic, MicOff, PhoneCall } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useVoiceWake } from '../hooks/useVoiceWake';

export const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const { sendMessage, isLoading, voiceCallActive, toggleVoiceCall } = useChatStore();
  const { isSupported } = useVoiceWake();

  const [isDictating, setIsDictating] = useState(false);
  const dictationRecognitionRef = useRef<any>(null);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  // Push-to-talk dictation toggle
  const toggleDictation = () => {
    if (!isSupported) {
      alert("Voice recognition is not supported in this browser. Please use Chrome, Edge, or Brave.");
      return;
    }

    if (isDictating) {
      if (dictationRecognitionRef.current) {
        try {
          dictationRecognitionRef.current.stop();
        } catch {}
      }
      setIsDictating(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsDictating(true);
    };

    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript.trim()) {
        setInput(transcript);
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
        }
      }
    };

    recognition.onerror = () => {
      setIsDictating(false);
    };

    recognition.onend = () => {
      setIsDictating(false);
    };

    try {
      recognition.start();
      dictationRecognitionRef.current = recognition;
    } catch {
      setIsDictating(false);
    }
  };

  useEffect(() => {
    return () => {
      if (dictationRecognitionRef.current) {
        try {
          dictationRecognitionRef.current.stop();
        } catch {}
      }
    };
  }, []);

  return (
    <div className="p-4 sm:p-6 bg-[#0a0a0c]/90 border-t border-[#f4f4f6]/10 backdrop-blur-md relative z-10">
      <div
        className="flex items-end gap-2 sm:gap-3 bg-[#0d0d0f] border border-[#f4f4f6]/15 focus-within:border-[#f4f4f6]/40 focus-within:shadow-[0_0_20px_rgba(244,244,246,0.06)] p-3 transition-all duration-200"
        style={{
          clipPath:
            'polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)',
        }}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            isDictating
              ? "Listening to your voice..."
              : voiceCallActive
              ? "Speak 'Venom...' to call the symbiote or type..."
              : "Speak to us... or click the mic to talk."
          }
          rows={1}
          disabled={isLoading}
          className="flex-1 bg-transparent text-[#f4f4f6] text-xs sm:text-sm font-mono placeholder-[#f4f4f6]/25 outline-none resize-none max-h-36 leading-relaxed"
        />

        {/* Dictation Mic Button */}
        {isSupported && (
          <button
            onClick={toggleDictation}
            title={isDictating ? "Stop listening" : "Click to speak to Venom"}
            className={`flex items-center justify-center p-2 transition-all ${
              isDictating
                ? 'bg-[#00ff66]/20 text-[#00ff66] border border-[#00ff66]/50 shadow-[0_0_15px_rgba(0,255,102,0.4)] animate-pulse'
                : 'text-[#f4f4f6]/50 hover:text-[#00ff66] hover:bg-[#00ff66]/10'
            }`}
            style={{
              clipPath:
                'polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px)',
            }}
          >
            {isDictating ? <Mic size={16} /> : <MicOff size={16} />}
          </button>
        )}

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className={`flex items-center gap-1.5 px-4 py-2 font-['Orbitron'] text-[11px] font-bold tracking-widest uppercase transition-all duration-200 ${
            input.trim() && !isLoading
              ? 'bg-[#f4f4f6] text-[#000000] hover:bg-[#00ff66] hover:shadow-[0_0_15px_#00ff66]'
              : 'bg-[#f4f4f6]/10 text-[#f4f4f6]/30 cursor-not-allowed'
          }`}
          style={{
            clipPath:
              'polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px)',
          }}
        >
          <span>SEND</span>
          <CornerDownLeft size={12} />
        </button>
      </div>

      <div className="flex justify-between items-center text-[10px] text-[#f4f4f6]/30 mt-2 px-1 font-mono">
        <div className="flex items-center gap-3">
          <span>Enter to send · Shift+Enter for newline</span>
          <button
            onClick={toggleVoiceCall}
            className={`hidden sm:inline-flex items-center gap-1 hover:underline ${
              voiceCallActive ? 'text-[#00ff66]' : 'text-[#f4f4f6]/40 hover:text-[#00ff66]'
            }`}
          >
            <PhoneCall size={10} />
            <span>Wake Word: "Venom" {voiceCallActive ? '(Active)' : '(Click to Enable)'}</span>
          </button>
        </div>
        <span>{input.length} chars</span>
      </div>
    </div>
  );
};
