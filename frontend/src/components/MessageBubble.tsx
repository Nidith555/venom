import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Check, Volume2, Square, FileText } from 'lucide-react';
import { Message, useChatStore } from '../store/chatStore';
import { VenomLogo } from './VenomLogo';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const { isSpeaking, speakingMessageId, speakMessage, stopSpeaking } = useChatStore();

  const isCurrentSpeaking = isSpeaking && speakingMessageId === message.id;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleVoiceToggle = () => {
    if (isCurrentSpeaking) {
      stopSpeaking();
    } else {
      speakMessage(message.id, message.content);
    }
  };

  return (
    <div
      className={`flex gap-3.5 my-4 px-2 sm:px-4 ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar */}
      <div className="flex-shrink-0 pt-1">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-[#f4f4f6] text-[#000000] flex items-center justify-center font-bold text-xs font-mono shadow-[0_0_10px_rgba(244,244,246,0.3)]">
            HOST
          </div>
        ) : (
          <div className="w-8 h-8 rounded-sm bg-[#111214] border border-[#f4f4f6]/20 flex items-center justify-center shadow-[0_0_10px_rgba(0,0,0,0.8)]">
            <VenomLogo size={20} />
          </div>
        )}
      </div>

      {/* Bubble Container */}
      <div className={`max-w-[85%] sm:max-w-[75%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`relative px-4 py-3.5 text-xs sm:text-sm leading-relaxed transition-all duration-200 group ${
            isUser
              ? 'bg-[#f4f4f6] text-[#000000] font-sans font-medium'
              : `bg-[#111214]/95 text-[#f4f4f6] border font-mono shadow-[0_4px_24px_rgba(0,0,0,0.6)] ${
                  isCurrentSpeaking
                    ? 'border-[#00ff66]/60 shadow-[0_0_20px_rgba(0,255,102,0.2)]'
                    : 'border-[#f4f4f6]/15'
                }`
          }`}
          style={{
            clipPath: isUser
              ? 'polygon(0 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%)'
              : 'polygon(10px 0, 100% 0, 100% 100%, 0 100%, 0 10px)',
          }}
        >
          {/* Subtle Symbiote Tendril Highlight for Assistant */}
          {!isUser && (
            <div className="absolute inset-0 bg-gradient-to-br from-[#00ff66]/[0.02] to-transparent pointer-events-none" />
          )}

          {/* Action Buttons Header */}
          <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* Speaker / Vocalize Button (ElevenLabs Voice cgSgspJ2msm6clMCkdW9) */}
            {!isUser && message.content && (
              <button
                onClick={handleVoiceToggle}
                className={`p-1 transition-colors ${
                  isCurrentSpeaking
                    ? 'text-[#00ff66] animate-pulse'
                    : 'text-[#f4f4f6]/40 hover:text-[#00ff66]'
                }`}
                title={isCurrentSpeaking ? 'Stop Vocalization' : 'Speak (ElevenLabs Voice)'}
              >
                {isCurrentSpeaking ? <Square size={12} fill="#00ff66" /> : <Volume2 size={12} />}
              </button>
            )}

            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className={`p-1 transition-colors ${
                isUser
                  ? 'text-[#000000]/60 hover:text-[#000000]'
                  : 'text-[#f4f4f6]/40 hover:text-[#f4f4f6]'
              }`}
              title="Copy message"
            >
              {copied ? <Check size={12} className="text-[#00ff66]" /> : <Copy size={12} />}
            </button>
          </div>

          {/* Attached Files Badges */}
          {message.files && message.files.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2.5">
              {message.files.map((file, idx) => (
                <div
                  key={idx}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono border rounded ${
                    isUser
                      ? 'bg-black/10 border-black/20 text-black'
                      : 'bg-[#00ff66]/10 border-[#00ff66]/30 text-[#00ff66]'
                  }`}
                >
                  <FileText size={12} />
                  <span className="font-semibold truncate max-w-[150px]">{file.filename}</span>
                  <span className="opacity-60 text-[9px]">
                    ({file.size_bytes > 1024 ? `${Math.round(file.size_bytes / 1024)}KB` : `${file.size_bytes}B`})
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Content */}
          <div className="markdown-body select-text pr-4">
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <ReactMarkdown>{message.content || '...'}</ReactMarkdown>
            )}
          </div>
        </div>

        {/* Timestamp & Voice indicator */}
        <div className="flex items-center gap-2 mt-1 px-1 text-[10px] text-[#f4f4f6]/30 font-mono tracking-wider uppercase">
          <span>{isUser ? 'Host' : 'Venom'} · {message.timestamp}</span>
          {isCurrentSpeaking && (
            <span className="text-[#00ff66] flex items-center gap-1 font-bold">
              <span>●</span> SPEAKING
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
