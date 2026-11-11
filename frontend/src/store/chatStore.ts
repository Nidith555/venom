import { create } from 'zustand';
import { getApiUrl } from '../config/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  streaming?: boolean;
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
  sendMessage: (content: string) => Promise<void>;
  clearHistory: () => Promise<void>;
  fetchInitialState: () => Promise<void>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isLoading: false,
  isConnected: false,
  currentModel: 'gemini-3.1-flash-lite',
  availableModels: ['gemini-3.1-flash-lite', 'gemini-3.8-flash', 'gemini-3.5-flash', 'llama3.2', 'gpt-4o'],
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
        set({
          availableModels: mData.available_models || [mData.current_model],
          currentModel: mData.current_model || 'gemini-1.5-flash',
        });
      }
    } catch {
      set({ isConnected: false });
    }
  },

  sendMessage: async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || get().isLoading) return;

    const userMessage: Message = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
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
      ws.send(JSON.stringify({ message: trimmed }));
      return;
    }

    try {
      const response = await fetch(getApiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, stream: true }),
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
