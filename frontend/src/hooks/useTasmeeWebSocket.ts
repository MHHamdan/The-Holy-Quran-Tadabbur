/**
 * useTasmeeWebSocket - WebSocket hook for Tasmeeʿ word-by-word follow-along
 *
 * Handles:
 * - Session authentication (first frame carries the session token)
 * - Audio capture with ScriptProcessorNode (4096 samples = 256ms)
 * - Float32 to Int16 conversion for transmission
 * - Binary audio streaming over WebSocket
 * - Progressive reveal message handling
 * - Practice without speech recognition: when STT is unavailable the words
 *   are revealed locally, with no socket at all
 *
 * `error` holds a language-neutral code ("PERMISSION_DENIED",
 * "STT_UNAVAILABLE:ai_quota_exceeded", ...). The page turns it into Arabic
 * or English text; the hook never produces user-facing copy.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';
import { wsUrl } from '../lib/config';

// ---------------------------------------------------------------------------
// Sessions created on this device (id + token), for "delete my data".
// The server keeps Tasmee rows for TASMEE_RETENTION_DAYS (90) at most.
// ---------------------------------------------------------------------------

export const TASMEE_SESSIONS_STORAGE_KEY = 'tadabbur-tasmee-sessions';
const REMEMBER_DAYS = 90;

export interface RememberedTasmeeSession {
  id: string;
  token: string;
  createdAt: number;
}

export function listTasmeeSessions(): RememberedTasmeeSession[] {
  try {
    const rows = JSON.parse(localStorage.getItem(TASMEE_SESSIONS_STORAGE_KEY) ?? '[]');
    return Array.isArray(rows) ? rows.filter((r) => r && typeof r.id === 'string' && typeof r.token === 'string') : [];
  } catch {
    return [];
  }
}

export function rememberTasmeeSession(id: string, token: string): void {
  const cutoff = Date.now() - REMEMBER_DAYS * 86_400_000;
  const rows = listTasmeeSessions().filter((r) => r.createdAt >= cutoff && r.id !== id);
  rows.push({ id, token, createdAt: Date.now() });
  // Pruned by age only: the server keeps rows for up to 90 days, so every key
  // from that window must stay here or its row could not be deleted on request
  // (deleteRememberedTasmeeSessions batches by 200).
  try { localStorage.setItem(TASMEE_SESSIONS_STORAGE_KEY, JSON.stringify(rows)); } catch { /* storage unavailable */ }
}

/**
 * Delete every Tasmee session this device created (server rows, their events
 * and possible slips), then forget them locally. Returns the server count.
 */
export async function deleteRememberedTasmeeSessions(): Promise<number> {
  const rows = listTasmeeSessions();
  let deleted = 0;
  for (let i = 0; i < rows.length; i += 200) {
    const batch = rows.slice(i, i + 200).map(({ id, token }) => ({ id, token }));
    const res = await api.post<{ deleted: number }>('/tasmee/sessions/delete', { sessions: batch });
    deleted += res.data.deleted;
  }
  try { localStorage.removeItem(TASMEE_SESSIONS_STORAGE_KEY); } catch { /* storage unavailable */ }
  return deleted;
}

// Types
export interface ProgressiveWord {
  word: string;
  position: number;
  isRevealed: boolean;
  status: 'completed' | 'current' | 'pending' | 'error';
  mistakeType?: string;
}

export interface MistakeAlert {
  position: number;
  mistakeType: string;
  severity: string;
  expectedWord: string;
  actualWord?: string;
  timestamp: number;
  isSkip: boolean;
}

export type RevealMode = 'auto' | 'smart_tap' | 'hybrid';

export interface TasmeeWSConfig {
  revealMode: RevealMode;
  tapRevealCount: 1 | 3;
  hybridThreshold: number;
}

export interface TasmeeWSState {
  isConnected: boolean;
  isStreaming: boolean;
  pointer: number;
  revealedUpTo: number;
  totalWords: number;
  words: ProgressiveWord[];
  mistakes: MistakeAlert[];
  config: TasmeeWSConfig;
  audioLevel: number;
  error: string | null;
  isComplete: boolean;
  /** Speech recognition is unavailable: practise by revealing words locally. */
  sttUnavailable: boolean;
}

export interface TasmeeWSOptions {
  sessionId: string;
  token: string;
  onPointerUpdate?: (position: number, progress: number) => void;
  onWordsRevealed?: (words: ProgressiveWord[], source: 'alignment' | 'tap') => void;
  onMistakeAlert?: (mistake: MistakeAlert) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

/** Server close codes (see backend/app/api/routes/tasmee.py). */
const CLOSE_CODE_ERRORS: Record<number, string> = {
  4001: 'SESSION_UNAUTHORIZED',
  4004: 'SESSION_NOT_FOUND',
  4008: 'SESSION_LIMIT',
  4009: 'SESSION_NOT_ACTIVE',
  4029: 'RATE_LIMITED',
};

const TARGET_SAMPLE_RATE = 16000;  // What backend expects
const BUFFER_SIZE = 4096; // ~256ms chunks at browser sample rate

// Resample audio from source rate to target rate using linear interpolation
function resample(inputBuffer: Float32Array, fromRate: number, toRate: number): Float32Array {
  if (fromRate === toRate) {
    return inputBuffer;
  }
  const ratio = fromRate / toRate;
  const outputLength = Math.round(inputBuffer.length / ratio);
  const output = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i++) {
    const srcIndex = i * ratio;
    const srcIndexFloor = Math.floor(srcIndex);
    const srcIndexCeil = Math.min(srcIndexFloor + 1, inputBuffer.length - 1);
    const fraction = srcIndex - srcIndexFloor;
    output[i] = inputBuffer[srcIndexFloor] * (1 - fraction) + inputBuffer[srcIndexCeil] * fraction;
  }
  return output;
}

function micErrorCode(name: string | undefined): string {
  switch (name) {
    case 'NotAllowedError':
    case 'PermissionDeniedError':
      return 'PERMISSION_DENIED';
    case 'NotFoundError':
    case 'DevicesNotFoundError':
      return 'NO_MICROPHONE';
    case 'NotReadableError':
    case 'TrackStartError':
      return 'MIC_IN_USE';
    case 'SecurityError':
      return 'HTTPS_REQUIRED';
    case 'NotSupportedError':
      return 'MIC_UNSUPPORTED';
    default:
      return 'MIC_ERROR';
  }
}

export function useTasmeeWebSocket(options: TasmeeWSOptions) {
  const { sessionId, token, onPointerUpdate, onWordsRevealed, onMistakeAlert, onComplete, onError } = options;

  // State
  const [state, setState] = useState<TasmeeWSState>({
    isConnected: false,
    isStreaming: false,
    pointer: 0,
    revealedUpTo: 0,
    totalWords: 0,
    words: [],
    mistakes: [],
    config: {
      revealMode: 'auto',
      tapRevealCount: 1,
      hybridThreshold: 0.7,
    },
    audioLevel: 0,
    error: null,
    isComplete: false,
    sttUnavailable: false,
  });

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  // Releases the microphone; set to stopStreaming below (used by handlers created earlier).
  const releaseMicRef = useRef<() => void>(() => undefined);
  // Latest state for callbacks that must not be re-created on every update.
  const stateRef = useRef(state);
  stateRef.current = state;

  /** Seed the word list (from POST /sessions) so practice works without a socket. */
  const loadWords = useCallback((words: Array<{ word: string; position: number }>) => {
    setState(prev => (prev.words.length > 0 ? prev : {
      ...prev,
      totalWords: words.length,
      words: words.map((w, i) => ({
        word: w.word,
        position: w.position ?? i,
        isRevealed: false,
        status: i === 0 ? 'current' : 'pending',
      })),
    }));
  }, []);

  /** Switch to practice without speech recognition (local reveal). */
  const markSttUnavailable = useCallback((reason = 'unavailable') => {
    setState(prev => ({ ...prev, sttUnavailable: true, error: `STT_UNAVAILABLE:${reason}` }));
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'init':
        setState(prev => ({
          ...prev,
          totalWords: data.total_words,
          pointer: data.pointer,
          revealedUpTo: data.revealed_up_to,
          sttUnavailable: false,
          error: null,
          words: data.words.map((w: any) => ({
            word: w.word,
            position: w.position,
            isRevealed: w.is_revealed,
            status: w.is_revealed ? 'completed' : 'pending',
          })),
        }));
        break;

      case 'pointer_update':
        setState(prev => ({
          ...prev,
          pointer: data.position,
          revealedUpTo: data.revealed_up_to,
          isComplete: data.is_complete,
          words: prev.words.map((word, idx) => ({
            ...word,
            status: idx < data.position ? (word.status === 'error' ? 'error' : 'completed') : idx === data.position ? 'current' : word.status,
            isRevealed: idx < data.revealed_up_to,
          })),
        }));
        onPointerUpdate?.(data.position, data.progress);
        if (data.is_complete) {
          onComplete?.();
        }
        break;

      case 'reveal_words': {
        setState(prev => {
          const newWords = [...prev.words];
          data.words.forEach((w: any) => {
            if (newWords[w.position]) {
              newWords[w.position] = { ...newWords[w.position], isRevealed: true };
            }
          });
          return { ...prev, revealedUpTo: data.revealed_up_to, words: newWords };
        });
        const revealedWords = data.words.map((w: any) => ({
          word: w.word,
          position: w.position,
          isRevealed: true,
          status: 'pending' as const,
        }));
        onWordsRevealed?.(revealedWords, data.reveal_source);
        break;
      }

      case 'mistake_alert': {
        const mistake: MistakeAlert = {
          position: data.position,
          mistakeType: data.mistake_type,
          severity: data.severity,
          expectedWord: data.expected_word,
          actualWord: data.actual_word,
          timestamp: data.timestamp,
          isSkip: data.is_skip,
        };
        setState(prev => ({
          ...prev,
          mistakes: [...prev.mistakes, mistake],
          words: prev.words.map((word, idx) =>
            idx === data.position
              ? { ...word, status: 'error', mistakeType: data.mistake_type }
              : word
          ),
        }));
        onMistakeAlert?.(mistake);
        break;
      }

      case 'config_updated':
        setState(prev => ({
          ...prev,
          config: {
            revealMode: data.reveal_mode,
            tapRevealCount: data.tap_reveal_count,
            hybridThreshold: data.hybrid_threshold,
          },
        }));
        break;

      case 'stt_unavailable':
        // Speech recognition (HF) failed for an audio window; the server closes
        // the socket with 4003 after repeated failures.
        setState(prev => ({ ...prev, error: `STT_UNAVAILABLE:${data.reason ?? 'unavailable'}` }));
        break;

      case 'session_limit':
        setState(prev => ({ ...prev, error: 'SESSION_LIMIT' }));
        break;

      case 'reset_complete':
        setState(prev => ({
          ...prev,
          pointer: 0,
          revealedUpTo: 0,
          mistakes: [],
          isComplete: false,
          words: prev.words.map(w => ({
            ...w,
            isRevealed: false,
            status: 'pending',
            mistakeType: undefined,
          })),
        }));
        break;
    }
  }, [onPointerUpdate, onWordsRevealed, onMistakeAlert, onComplete]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!sessionId || !token) return;
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return;

    const ws = new WebSocket(wsUrl(`/api/v1/tasmee/ws/${encodeURIComponent(sessionId)}`));
    wsRef.current = ws;

    ws.onopen = () => {
      // The token travels in the first frame, never in the URL.
      ws.send(JSON.stringify({ type: 'auth', token }));
      setState(prev => ({ ...prev, isConnected: true, error: prev.sttUnavailable ? prev.error : null }));
    };

    ws.onmessage = (event) => {
      try {
        handleMessage(JSON.parse(event.data));
      } catch {
        /* ignore malformed frames */
      }
    };

    ws.onerror = () => {
      onError?.('CONNECTION_ERROR');
    };

    ws.onclose = (event) => {
      if (wsRef.current === ws) wsRef.current = null;
      // Never keep the microphone open without a server to stream to.
      releaseMicRef.current();
      setState(prev => ({ ...prev, isConnected: false, isStreaming: false }));
      if (event.code === 4003) {
        setState(prev => ({
          ...prev,
          sttUnavailable: true,
          error: prev.error?.startsWith('STT_UNAVAILABLE') ? prev.error : 'STT_UNAVAILABLE:unavailable',
        }));
      } else if (CLOSE_CODE_ERRORS[event.code]) {
        setState(prev => ({ ...prev, error: CLOSE_CODE_ERRORS[event.code] }));
      } else if (event.code !== 1000 && event.code !== 1001) {
        setState(prev => ({ ...prev, error: 'CONNECTION_LOST' }));
      }
    };
  }, [sessionId, token, handleMessage, onError]);

  // Audio chunk counter
  const actualSampleRateRef = useRef(TARGET_SAMPLE_RATE);

  // Check if microphone API is available
  const checkMicrophoneSupport = useCallback((): string | null => {
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!window.isSecureContext && !isLocalhost) return 'HTTPS_REQUIRED';
    if (!navigator.mediaDevices?.getUserMedia) return 'MIC_UNSUPPORTED';
    return null;
  }, []);

  /** Start streaming the microphone. Resolves true only if streaming started. */
  const startStreaming = useCallback(async (): Promise<boolean> => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setState(prev => ({ ...prev, error: prev.sttUnavailable ? prev.error : 'NOT_CONNECTED' }));
      return false;
    }
    if (streamRef.current) return true;

    const unsupported = checkMicrophoneSupport();
    if (unsupported) {
      setState(prev => ({ ...prev, error: unsupported, isStreaming: false }));
      onError?.(unsupported);
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        throw Object.assign(new Error('No audio tracks in stream'), { name: 'NotFoundError' });
      }

      streamRef.current = stream;

      // Interruptions: the OS can end the track (incoming call, another app
      // taking the mic, permission revoked in Settings, headset unplugged).
      const interrupted = (why: 'system' | 'background') => {
        if (streamRef.current !== stream) return;
        releaseMicRef.current();
        setState(prev => ({ ...prev, error: `RECORDING_INTERRUPTED:${why}` }));
      };
      audioTracks[0].addEventListener('ended', () => interrupted('system'));

      audioContextRef.current = new AudioContext();
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }

      const ctx = audioContextRef.current;
      ctx.onstatechange = () => {
        // iOS reports "interrupted" during calls/Siri; other platforms suspend.
        if ((ctx.state as string) === 'interrupted') {
          interrupted('system');
        } else if (ctx.state === 'suspended' && streamRef.current === stream) {
          ctx.resume().catch(() => interrupted('system'));
        }
      };

      actualSampleRateRef.current = audioContextRef.current.sampleRate;
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      scriptProcessorRef.current = audioContextRef.current.createScriptProcessor(BUFFER_SIZE, 1, 1);

      scriptProcessorRef.current.onaudioprocess = (event) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }
        const inputBuffer = event.inputBuffer.getChannelData(0);

        // Audio level for the UI (RMS)
        let sum = 0;
        for (let i = 0; i < inputBuffer.length; i++) {
          sum += inputBuffer[i] * inputBuffer[i];
        }
        const rms = Math.sqrt(sum / inputBuffer.length);
        setState(prev => ({ ...prev, audioLevel: rms }));

        const resampledBuffer = resample(inputBuffer, actualSampleRateRef.current, TARGET_SAMPLE_RATE);
        const int16Array = new Int16Array(resampledBuffer.length);
        for (let i = 0; i < resampledBuffer.length; i++) {
          const s = Math.max(-1, Math.min(1, resampledBuffer[i]));
          int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        wsRef.current.send(int16Array.buffer);
      };

      sourceRef.current.connect(scriptProcessorRef.current);
      scriptProcessorRef.current.connect(audioContextRef.current.destination);

      setState(prev => ({ ...prev, isStreaming: true, error: null }));
      return true;
    } catch (error: any) {
      releaseMicRef.current();
      const code = micErrorCode(error?.name);
      setState(prev => ({ ...prev, error: code, isStreaming: false }));
      onError?.(code);
      return false;
    }
  }, [onError, checkMicrophoneSupport]);

  // Stop audio streaming
  const stopStreaming = useCallback(() => {
    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    setState(prev => ({ ...prev, isStreaming: false, audioLevel: 0 }));
  }, []);
  releaseMicRef.current = stopStreaming;

  // Release the microphone when the app/tab goes to the background (mobile
  // WebViews keep running briefly; recording in the background is not intended).
  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden && streamRef.current) {
        stopStreaming();
        setState(prev => ({ ...prev, error: 'RECORDING_INTERRUPTED:background' }));
      }
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [stopStreaming]);

  /** Reveal the next words: through the server, or locally when there is no socket. */
  const sendRevealRequest = useCallback((count?: number) => {
    const requestCount = count || stateRef.current.config.tapRevealCount;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'reveal_request', count: requestCount }));
      return;
    }
    // Practice without speech recognition: reveal and advance locally.
    setState(prev => {
      if (prev.words.length === 0) return prev;
      const upTo = Math.min(prev.revealedUpTo + requestCount, prev.words.length);
      return {
        ...prev,
        revealedUpTo: upTo,
        pointer: upTo,
        isComplete: upTo >= prev.words.length,
        words: prev.words.map((w, i) => ({
          ...w,
          isRevealed: i < upTo,
          status: i < upTo ? 'completed' : i === upTo ? 'current' : 'pending',
        })),
      };
    });
  }, []);

  /** Update reveal configuration (server expects snake_case keys). */
  const updateConfig = useCallback((config: Partial<TasmeeWSConfig>) => {
    setState(prev => ({ ...prev, config: { ...prev.config, ...config } }));
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'config_update',
        ...(config.revealMode && { reveal_mode: config.revealMode }),
        ...(config.tapRevealCount && { tap_reveal_count: config.tapRevealCount }),
        ...(config.hybridThreshold !== undefined && { hybrid_threshold: config.hybridThreshold }),
      }));
    }
  }, []);

  // Reset session
  const reset = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'reset' }));
    }
  }, []);

  // Disconnect
  const disconnect = useCallback(() => {
    stopStreaming();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setState(prev => ({ ...prev, isConnected: false, isStreaming: false }));
  }, [stopStreaming]);

  /** Drop all words and progress (new session). */
  const clear = useCallback(() => {
    setState(prev => ({
      ...prev,
      pointer: 0,
      revealedUpTo: 0,
      totalWords: 0,
      words: [],
      mistakes: [],
      error: null,
      isComplete: false,
      sttUnavailable: false,
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // State
    ...state,

    // Actions
    connect,
    startStreaming,
    stopStreaming,
    sendRevealRequest,
    updateConfig,
    reset,
    disconnect,
    loadWords,
    markSttUnavailable,
    clear,
  };
}

export default useTasmeeWebSocket;
