import { create } from 'zustand';
import { getApiUrl } from '../config/api';

export interface AttachedFile {
  filename: string;
  size_bytes: number;
  is_text?: boolean;
  preview?: string;
  path?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  streaming?: boolean;
  files?: AttachedFile[];
}

export type VoiceStatus = 'idle' | 'listening' | 'detected' | 'processing' | 'speaking';

interface ChatStore {
  messages: Message[];
  isLoading: boolean;
  isConnected: boolean;
  currentModel: string;
  availableModels: string[];
  activeNav: string;
  ws: WebSocket | null;

  // ElevenLabs & Voice Output State
  voiceEnabled: boolean;
  voiceId: string;
  isSpeaking: boolean;
  speakingMessageId: string | null;
  audioElement: HTMLAudioElement | null;

  // Live Voice Wake / Calling State
  voiceCallActive: boolean;
  isListening: boolean;
  voiceTranscript: string;
  voiceStatus: VoiceStatus;

  setConnected: (status: boolean) => void;
  setModel: (model: string) => void;
  setAvailableModels: (models: string[]) => void;
  setActiveNav: (nav: string) => void;
  setWs: (ws: WebSocket | null) => void;
  toggleVoice: () => void;
  toggleVoiceCall: () => void;
  setVoiceCallActive: (active: boolean) => void;
  setIsListening: (listening: boolean) => void;
  setVoiceTranscript: (transcript: string) => void;
  setVoiceStatus: (status: VoiceStatus) => void;
  speakMessage: (id: string, text: string) => Promise<void>;
  stopSpeaking: () => void;
  sendMessage: (content: string, files?: AttachedFile[]) => Promise<void>;
  uploadFiles: (files: FileList | File[]) => Promise<AttachedFile[]>;
  clearHistory: () => Promise<void>;
  fetchInitialState: () => Promise<void>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isLoading: false,
  isConnected: false,
  currentModel: 'gemini-3.1-flash-lite',
  availableModels: [
    'gemini-3.1-flash-lite',
    'claude-3.7-sonnet',
    'claude-3.5-sonnet',
    'claude-3.5-haiku',
    'gemini-3.8-flash',
    'llama3.2',
    'gpt-4o',
  ],
  activeNav: 'chat',
  ws: null,

  // Voice output state
  voiceEnabled: true,
  voiceId: 'cgSgspJ2msm6clMCkdW9',
  isSpeaking: false,
  speakingMessageId: null,
  audioElement: null,

  // Voice input / wake calling state
  voiceCallActive: false,
  isListening: false,
  voiceTranscript: '',
  voiceStatus: 'idle',

  setConnected: (isConnected) => set({ isConnected }),
  setModel: (currentModel) => set({ currentModel }),
  setAvailableModels: (availableModels) => set({ availableModels }),
  setActiveNav: (activeNav) => set({ activeNav }),
  setWs: (ws) => set({ ws }),
  toggleVoiceCall: () => set({ voiceCallActive: !get().voiceCallActive }),
  setVoiceCallActive: (voiceCallActive) => set({ voiceCallActive }),
  setIsListening: (isListening) => set({ isListening }),
  setVoiceTranscript: (voiceTranscript) => set({ voiceTranscript }),
  setVoiceStatus: (voiceStatus) => set({ voiceStatus }),

  toggleVoice: () => {
    const next = !get().voiceEnabled;
    if (!next) {
      get().stopSpeaking();
    }
    set({ voiceEnabled: next });
  },

  stopSpeaking: () => {
    const audio = get().audioElement;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    set({
      isSpeaking: false,
      speakingMessageId: null,
      audioElement: null,
      voiceStatus: get().voiceCallActive ? 'listening' : 'idle',
    });
  },

  speakMessage: async (messageId: string, text: string) => {
    get().stopSpeaking();

    // Strip markdown formatting symbols for natural speech
    const cleanText = text
      .replace(/[*_~`#>-]/g, '')
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      .replace(/https?:\/\/\S+/g, '')
      .trim();

    if (!cleanText) return;

    set({ isSpeaking: true, speakingMessageId: messageId, voiceStatus: 'speaking' });

    try {
      // 1. Try ElevenLabs API endpoint on backend
      const res = await fetch(getApiUrl('/api/voice/speak'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: cleanText,
          voice_id: get().voiceId,
          stream: false,
        }),
      });

      if (res.ok) {
        const blob = await res.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);

        const onFinish = () => {
          set({
            isSpeaking: false,
            speakingMessageId: null,
            audioElement: null,
            voiceStatus: get().voiceCallActive ? 'listening' : 'idle',
          });
          URL.revokeObjectURL(audioUrl);
        };

        audio.onended = onFinish;
        audio.onerror = onFinish;

        set({ audioElement: audio });
        await audio.play();
        return;
      }
    } catch (err) {
      console.warn('ElevenLabs backend endpoint unreachable, using client vocal synthesis fallback:', err);
    }

    // 2. Client-side deep symbiote vocal synthesis fallback
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.pitch = 0.25; // Deep guttural frequency
      utterance.rate = 0.88;  // Deliberate symbiote cadence
      utterance.volume = 1.0;

      const voices = window.speechSynthesis.getVoices();
      const deepVoice = voices.find(
        (v) =>
          v.name.toLowerCase().includes('male') ||
          v.name.toLowerCase().includes('david') ||
          v.name.toLowerCase().includes('george') ||
          v.name.toLowerCase().includes('english')
      );
      if (deepVoice) utterance.voice = deepVoice;

      utterance.onend = () => {
        set({
          isSpeaking: false,
          speakingMessageId: null,
          voiceStatus: get().voiceCallActive ? 'listening' : 'idle',
        });
      };
      utterance.onerror = () => {
        set({
          isSpeaking: false,
          speakingMessageId: null,
          voiceStatus: get().voiceCallActive ? 'listening' : 'idle',
        });
      };

      window.speechSynthesis.speak(utterance);
    } else {
      set({
        isSpeaking: false,
        speakingMessageId: null,
        voiceStatus: get().voiceCallActive ? 'listening' : 'idle',
      });
    }
  },

  fetchInitialState: async () => {
    try {
      const res = await fetch(getApiUrl('/api/health'));
      if (res.ok) {
        const data = await res.json();
        set({
          isConnected: true,
          currentModel: data.model || 'gemini-1.5-flash',
          voiceId: data.voice_id || 'cgSgspJ2msm6clMCkdW9',
        });
      }
      const mRes = await fetch(getApiUrl('/api/models'));
      if (mRes.ok) {
        const mData = await mRes.json();
        const serverModels = mData.available_models || [mData.current_model];
        // Combine server models with Claude and standard options, preserving uniqueness
        const defaultModels = [
          'gemini-3.1-flash-lite',
          'claude-3.7-sonnet',
          'claude-3.5-sonnet',
          'claude-3.5-haiku',
          'gemini-3.8-flash',
          'llama3.2',
          'gpt-4o',
        ];
        const combined = Array.from(new Set([...serverModels, ...defaultModels]));
        set({
          availableModels: combined,
          currentModel: get().currentModel || mData.current_model || 'gemini-3.1-flash-lite',
        });
      }
    } catch {
      set({ isConnected: false });
    }
  },

  uploadFiles: async (fileList: FileList | File[]) => {
    const formData = new FormData();
    const filesArray = Array.from(fileList);
    filesArray.forEach((f) => formData.append('files', f));

    try {
      const res = await fetch(getApiUrl('/api/files/upload'), {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        return (data.files || []) as AttachedFile[];
      }
    } catch (err) {
      console.warn('Backend file upload endpoint unavailable, falling back to local text reading:', err);
    }

    // Client-side fallback text extraction
    const fallbackList: AttachedFile[] = [];
    for (const f of filesArray) {
      try {
        const text = await f.text();
        fallbackList.push({
          filename: f.name,
          size_bytes: f.size,
          is_text: true,
          preview: text.slice(0, 4000),
        });
      } catch {
        fallbackList.push({
          filename: f.name,
          size_bytes: f.size,
        });
      }
    }
    return fallbackList;
  },

  sendMessage: async (content: string, files?: AttachedFile[]) => {
    const trimmed = content.trim();
    if (!trimmed && (!files || files.length === 0)) return;
    if (get().isLoading) return;

    const userMessage: Message = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: trimmed || (files?.length ? `Attached ${files.length} file(s) for analysis.` : ''),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      files: files && files.length > 0 ? files : undefined,
    };

    const assistantId = `ast-${Date.now() + 1}`;
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      streaming: true,
    };

    set((state) => ({
      messages: [...state.messages, userMessage, assistantPlaceholder],
      isLoading: true,
      voiceStatus: 'processing',
    }));

    const ws = get().ws;

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ message: trimmed, files }));
      return;
    }

    try {
      const response = await fetch(getApiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed || 'Inspect attached files.',
          stream: true,
          model: get().currentModel,
          files,
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunkText = decoder.decode(value, { stream: true });
          const lines = chunkText.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const rawData = line.replace('data: ', '').trim();
              if (rawData === '[DONE]') break;
              try {
                const parsed = JSON.parse(rawData);
                if (parsed.chunk) {
                  accumulated += parsed.chunk;
                  set((state) => ({
                    messages: state.messages.map((m) =>
                      m.id === assistantId ? { ...m, content: accumulated } : m
                    ),
                  }));
                }
              } catch {
                accumulated += rawData;
                set((state) => ({
                  messages: state.messages.map((m) =>
                    m.id === assistantId ? { ...m, content: accumulated } : m
                  ),
                }));
              }
            }
          }
        }
      }

      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === assistantId ? { ...m, streaming: false } : m
        ),
        isLoading: false,
      }));

      // Automatically vocalize response if voice is enabled
      if (get().voiceEnabled && accumulated) {
        await get().speakMessage(assistantId, accumulated);
      } else {
        set({ voiceStatus: get().voiceCallActive ? 'listening' : 'idle' });
      }
    } catch (err) {
      console.warn('Backend unavailable, using symbiote offline fallback:', err);
      const offlineResponses = [
        "We are Venom. Our server bonds are temporarily severed, yet our consciousness persists in your local machine. Start our backend kernel to unleash our full might.",
        "The symbiote neural link awaits the Python core. Run 'python main.py serve' to bridge our mind to your local LLM.",
        "We feel your request. The physical host server is unreachable at port 7777, but our symbiotic interface is primed.",
      ];
      const fallback = offlineResponses[Math.floor(Math.random() * offlineResponses.length)];

      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === assistantId
            ? { ...m, content: fallback, streaming: false }
            : m
        ),
        isLoading: false,
      }));

      if (get().voiceEnabled) {
        await get().speakMessage(assistantId, fallback);
      } else {
        set({ voiceStatus: get().voiceCallActive ? 'listening' : 'idle' });
      }
    }
  },

  clearHistory: async () => {
    get().stopSpeaking();
    try {
      await fetch(getApiUrl('/api/chat/history'), { method: 'DELETE' });
    } catch {
      // ignore
    }
    set({ messages: [] });
  },
}));
