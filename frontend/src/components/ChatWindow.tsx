import React, { useRef, useEffect } from 'react';
import { useChatStore } from '../store/chatStore';
import { MessageBubble } from './MessageBubble';
import { VenomLogo } from './VenomLogo';

export const ChatWindow: React.FC = () => {
  const { messages, isLoading } = useChatStore();
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-2 sm:px-6 py-6 space-y-2 relative z-10 custom-scrollbar">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-center select-none py-12">
          <div className="animate-pulse duration-1000">
            <VenomLogo size={100} />
          </div>
          <h2 className="mt-6 text-xl sm:text-2xl font-black tracking-[0.25em] text-[#f4f4f6]/90 font-['Orbitron']">
            WE ARE READY
          </h2>
          <p className="mt-2 text-xs uppercase tracking-widest text-[#f4f4f6]/40 max-w-sm">
            The symbiotic bond awaits your command. Speak to awaken our collective cognition.
          </p>

          <div className="mt-8 flex flex-wrap gap-2 justify-center max-w-md">
            {[
              'Who are you?',
              'Analyze system vitals',
              'Summarize local context',
              'We are Venom',
            ].map((prompt) => (
              <button
                key={prompt}
                onClick={() => useChatStore.getState().sendMessage(prompt)}
                className="px-3 py-1.5 bg-[#111214] hover:bg-[#f4f4f6]/10 border border-[#f4f4f6]/10 text-[11px] text-[#f4f4f6]/60 hover:text-[#f4f4f6] font-mono transition-all"
                style={{
                  clipPath:
                    'polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px)',
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <>
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Thinking indicator */}
          {isLoading && messages[messages.length - 1]?.role === 'user' && (
            <div className="flex items-center gap-3 my-4 px-4 text-xs font-mono text-[#f4f4f6]/50">
              <div className="w-8 h-8 rounded-sm bg-[#111214] border border-[#f4f4f6]/20 flex items-center justify-center">
                <VenomLogo size={18} />
              </div>
              <div className="flex items-center gap-2">
                <span className="tracking-widest uppercase font-['Orbitron'] text-[10px]">
                  Venom is processing
                </span>
                <span className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-[#00ff66] rounded-full animate-bounce" />
                  <span className="w-1.5 h-1.5 bg-[#00ff66] rounded-full animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 bg-[#00ff66] rounded-full animate-bounce [animation-delay:0.4s]" />
                </span>
              </div>
            </div>
          )}
        </>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
