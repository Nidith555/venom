/// <reference types="vite/client" />

/**
 * Venom API & WebSocket Configuration
 * Automatically switches between local dev and hosted cloud endpoints.
 */

const env = (import.meta as any).env || {};

export const API_BASE_URL: string = (env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export function getApiUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (!API_BASE_URL) return cleanPath;
  return `${API_BASE_URL}${cleanPath}`;
}

export function getWsUrl(path: string = '/ws/chat'): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (env.VITE_WS_URL) {
    return `${env.VITE_WS_URL.replace(/\/$/, '')}${cleanPath}`;
  }
  if (API_BASE_URL) {
    const wsProto = API_BASE_URL.startsWith('https') ? 'wss:' : 'ws:';
    const host = API_BASE_URL.replace(/^https?:\/\//, '');
    return `${wsProto}//${host}${cleanPath}`;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname || 'localhost';
  const port = window.location.port === '5173' ? '7777' : window.location.port;
  return `${protocol}//${host}${port ? `:${port}` : ''}${cleanPath}`;
}
