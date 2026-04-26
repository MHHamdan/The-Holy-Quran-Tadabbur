/**
 * useTasmeeWebSocket - WebSocket hook for real-time Tasmeeʿ audio streaming
 *
 * Handles:
 * - Audio capture with ScriptProcessorNode (4096 samples = 256ms)
 * - Float32 to Int16 conversion for transmission
 * - Binary audio streaming over WebSocket
 * - Progressive reveal message handling
 */

import { useCallback, useEffect, useRef, useState } from 'react';

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
}

export interface TasmeeWSOptions {
  sessionId: number;
  onPointerUpdate?: (position: number, progress: number) => void;
  onWordsRevealed?: (words: ProgressiveWord[], source: 'alignment' | 'tap') => void;
  onMistakeAlert?: (mistake: MistakeAlert) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

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

export function useTasmeeWebSocket(options: TasmeeWSOptions) {
  const { sessionId, onPointerUpdate, onWordsRevealed, onMistakeAlert, onComplete, onError } = options;

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
  });

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  // Get WebSocket URL
  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // Use backend API endpoint
    const apiBase = import.meta.env.VITE_API_URL || `${protocol}//${host}`;
    return `${apiBase.replace('http', 'ws')}/api/v1/tasmee/ws/${sessionId}`;
  }, [sessionId]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[TasmeeWS] Already connected');
      return;
    }

    const wsUrl = getWsUrl();
    console.log('[TasmeeWS] Connecting to:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[TasmeeWS] Connection opened');
      setState(prev => ({ ...prev, isConnected: true, error: null }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[TasmeeWS] Message received:', data.type);
        handleMessage(data);
      } catch (e) {
        console.error('[TasmeeWS] Failed to parse message:', e);
      }
    };

    ws.onerror = (event) => {
      console.error('[TasmeeWS] Error:', event);
      const errorMsg = 'WebSocket connection error';
      setState(prev => ({ ...prev, error: errorMsg }));
      onError?.(errorMsg);
    };

    ws.onclose = (event) => {
      console.log('[TasmeeWS] Closed:', event.code, event.reason);
      setState(prev => ({ ...prev, isConnected: false, isStreaming: false }));
      if (event.code !== 1000 && event.code !== 1001) {
        const errorMsg = event.reason || `WebSocket closed (code: ${event.code})`;
        setState(prev => ({ ...prev, error: errorMsg }));
      }
    };
  }, [getWsUrl, onError]);

  // Handle incoming messages
  const handleMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'init':
        setState(prev => ({
          ...prev,
          totalWords: data.total_words,
          pointer: data.pointer,
          revealedUpTo: data.revealed_up_to,
          words: data.words.map((w: any) => ({
            word: w.word,
            position: w.position,
            isRevealed: w.is_revealed,
            status: w.is_revealed ? 'completed' : 'pending',
          })),
        }));
        break;

      case 'pointer_update':
        console.log(`[TasmeeWS] Pointer update: position=${data.position}, revealed_up_to=${data.revealed_up_to}, progress=${data.progress}`);
        setState(prev => ({
          ...prev,
          pointer: data.position,
          revealedUpTo: data.revealed_up_to,
          isComplete: data.is_complete,
          words: prev.words.map((word, idx) => ({
            ...word,
            status: idx < data.position ? 'completed' : idx === data.position ? 'current' : word.status,
            isRevealed: idx < data.revealed_up_to,
          })),
        }));
        onPointerUpdate?.(data.position, data.progress);
        if (data.is_complete) {
          onComplete?.();
        }
        break;

      case 'reveal_words': {
        console.log(`[TasmeeWS] Reveal words: ${data.words.length} words, revealed_up_to=${data.revealed_up_to}, source=${data.reveal_source}`);
        setState(prev => {
          const newWords = [...prev.words];
          data.words.forEach((w: any) => {
            if (newWords[w.position]) {
              newWords[w.position] = {
                ...newWords[w.position],
                isRevealed: true,
              };
            }
          });
          return {
            ...prev,
            revealedUpTo: data.revealed_up_to,
            words: newWords,
          };
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
        console.log('[TasmeeWS] Config updated from server:', data);
        setState(prev => ({
          ...prev,
          config: {
            revealMode: data.reveal_mode,
            tapRevealCount: data.tap_reveal_count,
            hybridThreshold: data.hybrid_threshold,
          },
        }));
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

  // Audio chunk counter for logging
  const chunkCountRef = useRef(0);
  const actualSampleRateRef = useRef(TARGET_SAMPLE_RATE);

  // Check if microphone API is available
  const checkMicrophoneSupport = useCallback((): { supported: boolean; error?: string } => {
    // Check secure context first (required for getUserMedia except localhost)
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const isSecure = window.isSecureContext;

    console.log(`[TasmeeAudio] Security check: hostname=${window.location.hostname}, isSecureContext=${isSecure}, isLocalhost=${isLocalhost}`);

    if (!isSecure && !isLocalhost) {
      return {
        supported: false,
        error: `HTTPS_REQUIRED: Microphone requires HTTPS. You are accessing via HTTP (${window.location.protocol}//${window.location.host}). Solutions: 1) Use https:// URL, 2) Access via http://localhost:3000, or 3) Configure HTTPS on your server.`
      };
    }

    // Check if mediaDevices API exists
    if (!navigator.mediaDevices) {
      return {
        supported: false,
        error: 'MEDIA_DEVICES_UNAVAILABLE: navigator.mediaDevices is not available. This may be due to HTTP context or old browser.'
      };
    }

    // Check if getUserMedia exists
    if (!navigator.mediaDevices.getUserMedia) {
      return {
        supported: false,
        error: 'GET_USER_MEDIA_UNAVAILABLE: getUserMedia is not available. Please use a modern browser (Chrome, Firefox, Safari, Edge).'
      };
    }

    return { supported: true };
  }, []);

  // Start audio streaming
  const startStreaming = useCallback(async () => {
    console.log('[TasmeeAudio] startStreaming called');

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      const errorMsg = 'WebSocket not connected - cannot start streaming';
      console.error('[TasmeeAudio]', errorMsg);
      setState(prev => ({ ...prev, error: errorMsg }));
      return;
    }

    // Check if already streaming
    if (streamRef.current) {
      console.log('[TasmeeAudio] Already streaming, ignoring');
      return;
    }

    // Check microphone support first
    const supportCheck = checkMicrophoneSupport();
    if (!supportCheck.supported) {
      console.error('[TasmeeAudio]', supportCheck.error);
      setState(prev => ({ ...prev, error: supportCheck.error!, isStreaming: false }));
      onError?.(supportCheck.error!);
      return;
    }

    try {
      console.log('[TasmeeAudio] Requesting microphone access...');

      // Request microphone access with modern API
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Verify we got audio tracks
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        throw new Error('No audio tracks in stream');
      }
      console.log(`[TasmeeAudio] Microphone access granted. Track: ${audioTracks[0].label}, enabled: ${audioTracks[0].enabled}, readyState: ${audioTracks[0].readyState}`);

      streamRef.current = stream;

      // Create audio context with browser's default sample rate
      audioContextRef.current = new AudioContext();

      // Resume AudioContext if suspended (browser autoplay policy)
      if (audioContextRef.current.state === 'suspended') {
        console.log('[TasmeeAudio] AudioContext suspended, resuming...');
        await audioContextRef.current.resume();
      }

      actualSampleRateRef.current = audioContextRef.current.sampleRate;
      console.log(`[TasmeeAudio] AudioContext created. State: ${audioContextRef.current.state}, Browser rate: ${actualSampleRateRef.current}Hz, Target: ${TARGET_SAMPLE_RATE}Hz`);

      if (actualSampleRateRef.current !== TARGET_SAMPLE_RATE) {
        console.log(`[TasmeeAudio] Will resample from ${actualSampleRateRef.current}Hz to ${TARGET_SAMPLE_RATE}Hz`);
      }

      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);

      // Create script processor for audio data
      scriptProcessorRef.current = audioContextRef.current.createScriptProcessor(BUFFER_SIZE, 1, 1);
      chunkCountRef.current = 0;

      scriptProcessorRef.current.onaudioprocess = (event) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }

        const inputBuffer = event.inputBuffer.getChannelData(0);

        // Calculate audio level for UI (RMS as percentage)
        let sum = 0;
        for (let i = 0; i < inputBuffer.length; i++) {
          sum += inputBuffer[i] * inputBuffer[i];
        }
        const rms = Math.sqrt(sum / inputBuffer.length);
        setState(prev => ({ ...prev, audioLevel: rms }));

        // Resample to 16kHz if needed
        const resampledBuffer = resample(inputBuffer, actualSampleRateRef.current, TARGET_SAMPLE_RATE);

        // Convert Float32 to Int16
        const int16Array = new Int16Array(resampledBuffer.length);
        for (let i = 0; i < resampledBuffer.length; i++) {
          const s = Math.max(-1, Math.min(1, resampledBuffer[i]));
          int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send binary audio data
        wsRef.current.send(int16Array.buffer);

        // Log every 10th chunk to avoid spam
        chunkCountRef.current++;
        if (chunkCountRef.current % 10 === 1) {
          console.log(`[TasmeeAudio] Sent chunk #${chunkCountRef.current}: ${int16Array.byteLength} bytes (from ${inputBuffer.length} samples), RMS: ${rms.toFixed(4)}`);
        }
      };

      // Connect audio nodes
      sourceRef.current.connect(scriptProcessorRef.current);
      scriptProcessorRef.current.connect(audioContextRef.current.destination);

      console.log('[TasmeeAudio] Audio pipeline connected, streaming started');
      setState(prev => ({ ...prev, isStreaming: true, error: null }));

    } catch (error: any) {
      console.error('[TasmeeAudio] Failed to start audio streaming:', error);
      console.error('[TasmeeAudio] Error details - name:', error.name, 'message:', error.message);

      // Provide specific error messages based on error type
      let errorMsg = 'Failed to access microphone';

      switch (error.name) {
        case 'NotAllowedError':
        case 'PermissionDeniedError':
          errorMsg = 'PERMISSION_DENIED: Microphone permission denied. Please click the lock icon in your browser address bar and allow microphone access.';
          break;
        case 'NotFoundError':
        case 'DevicesNotFoundError':
          errorMsg = 'NO_MICROPHONE: No microphone found. Please connect a microphone and try again.';
          break;
        case 'NotReadableError':
        case 'TrackStartError':
          errorMsg = 'MIC_IN_USE: Microphone is in use by another application. Please close other apps using the mic.';
          break;
        case 'OverconstrainedError':
          errorMsg = 'MIC_CONSTRAINTS: Microphone does not support requested settings. Try with different audio settings.';
          break;
        case 'SecurityError':
          errorMsg = 'SECURITY_ERROR: Microphone access blocked due to security policy. HTTPS is required.';
          break;
        case 'TypeError':
          errorMsg = 'API_ERROR: getUserMedia API error. This may indicate the API is not available.';
          break;
        case 'AbortError':
          errorMsg = 'ABORTED: Microphone access was aborted. Please try again.';
          break;
        default:
          errorMsg = `MIC_ERROR (${error.name}): ${error.message || 'Unknown error accessing microphone'}`;
      }

      setState(prev => ({ ...prev, error: errorMsg, isStreaming: false }));
      onError?.(errorMsg);
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

  // Send reveal request (tap to reveal)
  const sendRevealRequest = useCallback((count?: number) => {
    const requestCount = count || state.config.tapRevealCount;
    console.log(`[TasmeeWS] sendRevealRequest called, count: ${requestCount}`);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        type: 'reveal_request',
        count: requestCount,
      };
      console.log('[TasmeeWS] Sending reveal_request:', message);
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[TasmeeWS] Cannot send reveal_request - WebSocket not open');
    }
  }, [state.config.tapRevealCount]);

  // Update configuration
  const updateConfig = useCallback((config: Partial<TasmeeWSConfig>) => {
    console.log('[TasmeeWS] updateConfig called with:', config);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        type: 'config_update',
        ...config,
      };
      console.log('[TasmeeWS] Sending config_update:', message);
      wsRef.current.send(JSON.stringify(message));

      // Also update local state immediately for responsiveness
      setState(prev => ({
        ...prev,
        config: { ...prev.config, ...config },
      }));
    } else {
      console.warn('[TasmeeWS] Cannot send config_update - WebSocket not open');
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
  };
}

export default useTasmeeWebSocket;
