import { useEffect, useRef, useCallback } from 'react';
import { useChatStore } from '../store/chatStore';
import { playWakeChime, playListeningTone, playSleepTone } from '../utils/audioEffects';

// Type definitions for Web Speech API
interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

const WAKE_WORDS = [
  'venom',
  'hey venom',
  'ok venom',
  'okay venom',
  'yo venom',
  'call venom',
  'wake up venom',
  'hello venom',
  'hi venom',
  'we are venom',
];

export function useVoiceWake() {
  const {
    voiceCallActive,
    setVoiceCallActive,
    isListening,
    setIsListening,
    voiceStatus,
    setVoiceStatus,
    voiceTranscript,
    setVoiceTranscript,
    sendMessage,
    isSpeaking,
    speakMessage,
  } = useChatStore();

  const recognitionRef = useRef<any>(null);
  const restartTimerRef = useRef<number | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const lastProcessedRef = useRef<string>('');
  const isAwakeRef = useRef<boolean>(false);

  // Check if browser supports speech recognition
  const isSupported =
    typeof window !== 'undefined' &&
    Boolean((window as unknown as IWindow).SpeechRecognition || (window as unknown as IWindow).webkitSpeechRecognition);

  const stopRecognition = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, [setIsListening]);

  const handleWakePhraseDetected = useCallback(
    async (rawText: string) => {
      const lower = rawText.toLowerCase().trim();
      if (!lower) return;

      // Avoid re-processing the exact same sentence
      if (lastProcessedRef.current === lower) return;
      lastProcessedRef.current = lower;

      // Check for wake word
      let matchedWake = false;
      let command = lower;

      for (const wake of WAKE_WORDS) {
        if (lower.startsWith(wake)) {
          matchedWake = true;
          command = lower.slice(wake.length).trim();
          break;
        } else if (lower.includes(wake)) {
          matchedWake = true;
          const idx = lower.indexOf(wake);
          command = lower.slice(idx + wake.length).trim();
          break;
        }
      }

      // If already in an active awakened call session, any speech counts
      if (!matchedWake && isAwakeRef.current) {
        matchedWake = true;
        command = lower;
      }

      if (!matchedWake) return;

      // Symbiote triggered!
      playWakeChime();
      setVoiceStatus('detected');
      isAwakeRef.current = true;

      // Clean up punctuation leading from command
      command = command.replace(/^[,.?!:\s-]+/, '').trim();

      if (!command) {
        // User called "Venom!" without immediate command
        setVoiceTranscript("Venom awakened...");
        const greetings = [
          "We are Venom. We hear you, host. What is your desire?",
          "We are awake. The symbiote is listening. Speak to us.",
          "Our bond is strong. What do you require, host?",
        ];
        const greeting = greetings[Math.floor(Math.random() * greetings.length)];
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

        await speakMessage(greetingId, greeting);
      } else {
        // User called with a query
        setVoiceTranscript(command);
        setVoiceStatus('processing');
        await sendMessage(command);
      }
    },
    [sendMessage, setVoiceStatus, setVoiceTranscript, speakMessage]
  );

  const startRecognition = useCallback(() => {
    if (!isSupported) return;
    stopRecognition();

    const SpeechRecognition =
      (window as unknown as IWindow).SpeechRecognition ||
      (window as unknown as IWindow).webkitSpeechRecognition;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setVoiceStatus(isAwakeRef.current ? 'listening' : 'idle');
    };

    recognition.onresult = (event: any) => {
      let interim = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const item = event.results[i];
        if (item.isFinal) {
          finalTranscript += item[0].transcript;
        } else {
          interim += item[0].transcript;
        }
      }

      const activeText = (finalTranscript || interim).trim();
      if (activeText) {
        setVoiceTranscript(activeText);

        // Reset silence timer
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
        }

        // Check if wake word or complete speech is ready
        if (finalTranscript.trim()) {
          handleWakePhraseDetected(finalTranscript.trim());
        } else {
          // Pause detection debounce
          silenceTimerRef.current = window.setTimeout(() => {
            if (activeText.length > 2) {
              handleWakePhraseDetected(activeText);
            }
          }, 1200);
        }
      }
    };

    recognition.onerror = (event: any) => {
      console.warn('Speech recognition status:', event.error);
      if (event.error === 'not-allowed') {
        setVoiceCallActive(false);
        stopRecognition();
        return;
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      // If voice call is active and Venom isn't currently speaking, restart listening automatically
      const state = useChatStore.getState();
      if (state.voiceCallActive && !state.isSpeaking) {
        restartTimerRef.current = window.setTimeout(() => {
          startRecognition();
        }, 300);
      }
    };

    try {
      recognition.start();
      recognitionRef.current = recognition;
    } catch (e) {
      console.warn('Failed to start speech recognition:', e);
    }
  }, [
    isSupported,
    stopRecognition,
    setIsListening,
    setVoiceStatus,
    setVoiceTranscript,
    handleWakePhraseDetected,
    setVoiceCallActive,
  ]);

  // Handle Voice Call toggle
  useEffect(() => {
    if (voiceCallActive) {
      playListeningTone();
      isAwakeRef.current = true;
      startRecognition();
    } else {
      if (recognitionRef.current) {
        playSleepTone();
      }
      isAwakeRef.current = false;
      stopRecognition();
      setVoiceTranscript('');
      setVoiceStatus('idle');
    }
    return () => {
      stopRecognition();
    };
  }, [voiceCallActive, startRecognition, stopRecognition, setVoiceStatus, setVoiceTranscript]);

  // Pause speech recognition while Venom is speaking so it doesn't hear itself
  useEffect(() => {
    if (isSpeaking) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
      setIsListening(false);
      setVoiceStatus('speaking');
    } else if (voiceCallActive) {
      // Resume listening when speaking ends
      setVoiceStatus('listening');
      startRecognition();
    }
  }, [isSpeaking, voiceCallActive, startRecognition, setIsListening, setVoiceStatus]);

  const toggleVoiceCall = useCallback(() => {
    setVoiceCallActive(!voiceCallActive);
  }, [setVoiceCallActive, voiceCallActive]);

  return {
    isSupported,
    voiceCallActive,
    toggleVoiceCall,
    isListening,
    voiceStatus,
    voiceTranscript,
    startRecognition,
    stopRecognition,
  };
}
