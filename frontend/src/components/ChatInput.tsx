import React, { useState, useRef, useEffect } from 'react';
import { CornerDownLeft, Mic, MicOff, PhoneCall, Paperclip, X, FileText, Loader2 } from 'lucide-react';
import { useChatStore, AttachedFile } from '../store/chatStore';
import { useVoiceWake } from '../hooks/useVoiceWake';

export const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { sendMessage, uploadFiles, isLoading, voiceCallActive, toggleVoiceCall } = useChatStore();
  const { isSupported } = useVoiceWake();

  const [isDictating, setIsDictating] = useState(false);
  const dictationRecognitionRef = useRef<any>(null);

  const handleSend = () => {
    if ((!input.trim() && attachedFiles.length === 0) || isLoading || isUploading) return;
    sendMessage(input, attachedFiles);
    setInput('');
    setAttachedFiles([]);
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

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setIsUploading(true);
    try {
      const uploaded = await uploadFiles(e.target.files);
      setAttachedFiles((prev) => [...prev, ...uploaded]);
    } catch (err) {
      console.error('Failed to attach files:', err);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeAttachedFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
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
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Attached Files Chips Bar */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3 px-1">
          {attachedFiles.map((f, idx) => (
            <div
              key={idx}
              className="inline-flex items-center gap-2 px-3 py-1 bg-[#111214] border border-[#00ff66]/40 text-[#f4f4f6] text-xs font-mono rounded shadow-[0_0_10px_rgba(0,255,102,0.1)]"
            >
              <FileText size={13} className="text-[#00ff66]" />
              <span className="truncate max-w-[180px] font-semibold">{f.filename}</span>
              <span className="text-[10px] text-[#f4f4f6]/50">
                ({f.size_bytes > 1024 ? `${Math.round(f.size_bytes / 1024)}KB` : `${f.size_bytes}B`})
              </span>
              <button
                onClick={() => removeAttachedFile(idx)}
                className="text-[#f4f4f6]/40 hover:text-red-400 ml-1 p-0.5"
                title="Remove attachment"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div
        className="flex items-end gap-2 sm:gap-3 bg-[#0d0d0f] border border-[#f4f4f6]/15 focus-within:border-[#f4f4f6]/40 focus-within:shadow-[0_0_20px_rgba(244,244,246,0.06)] p-3 transition-all duration-200"
        style={{
          clipPath:
            'polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)',
        }}
      >
        {/* Paperclip File Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading || isUploading}
          title="Upload / attach files from your laptop"
          className="flex items-center justify-center p-2 text-[#f4f4f6]/50 hover:text-[#00ff66] hover:bg-[#00ff66]/10 transition-all rounded"
        >
          {isUploading ? <Loader2 size={16} className="animate-spin text-[#00ff66]" /> : <Paperclip size={16} />}
        </button>

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
              : attachedFiles.length > 0
              ? "Add a message or instructions for these files..."
              : "Speak to us, attach files, or give laptop commands..."
          }
          rows={1}
          disabled={isLoading || isUploading}
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
          disabled={(!input.trim() && attachedFiles.length === 0) || isLoading || isUploading}
          className={`flex items-center gap-1.5 px-4 py-2 font-['Orbitron'] text-[11px] font-bold tracking-widest uppercase transition-all duration-200 ${
            (input.trim() || attachedFiles.length > 0) && !isLoading && !isUploading
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
          <span>Enter to send · Click 📎 to attach laptop files</span>
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
        <span>{attachedFiles.length > 0 ? `${attachedFiles.length} file(s) attached` : `${input.length} chars`}</span>
      </div>
    </div>
  );
};
