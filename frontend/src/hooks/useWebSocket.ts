import { useEffect, useRef } from 'react';
import { useChatStore } from '../store/chatStore';
import { getWsUrl } from '../config/api';

export function useWebSocket() {
  const { setConnected, setWs } = useChatStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    let unmounted = false;

    function connect() {
      if (unmounted) return;

      const wsUrl = getWsUrl('/ws/chat');

      try {
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          if (unmounted) {
            socket.close();
            return;
          }
          setConnected(true);
          setWs(socket);
          wsRef.current = socket;
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            const store = useChatStore.getState();

            if (data.type === 'chunk' && data.content) {
              const msgs = store.messages;
              const lastMsg = msgs[msgs.length - 1];
              if (lastMsg && lastMsg.role === 'assistant') {
                useChatStore.setState({
                  messages: msgs.map((m, idx) =>
                    idx === msgs.length - 1
                      ? { ...m, content: m.content + data.content }
                      : m
                  ),
                });
              }
            } else if (data.type === 'done') {
              const msgs = useChatStore.getState().messages;
              const lastMsg = msgs[msgs.length - 1];
              useChatStore.setState({
                isLoading: false,
                messages: msgs.map((m, idx, arr) =>
                  idx === arr.length - 1 ? { ...m, streaming: false } : m
                ),
              });

              if (useChatStore.getState().voiceEnabled && lastMsg && lastMsg.content) {
                useChatStore.getState().speakMessage(lastMsg.id, lastMsg.content);
              }
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        socket.onerror = () => {
          setConnected(false);
        };

        socket.onclose = () => {
          setConnected(false);
          setWs(null);
          wsRef.current = null;
          if (!unmounted) {
            reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
          }
        };
      } catch (err) {
        setConnected(false);
        if (!unmounted) {
          reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
        }
      }
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [setConnected, setWs]);
}
