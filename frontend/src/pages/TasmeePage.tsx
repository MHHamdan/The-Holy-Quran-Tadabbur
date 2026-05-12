/**
 * Tasmeeʿ (Memorization) Page - Progressive Reveal
 *
 * A Quran memorization practice tool with real-time speech recognition,
 * progressive word reveal, and mistake detection.
 *
 * Features:
 * - Select Surah and Ayah range
 * - Real-time audio streaming via WebSocket
 * - Progressive word reveal (blank-first display)
 * - Multiple reveal modes: Auto, Smart Tap, Hybrid
 * - Word-by-word highlighting
 * - Mistake detection and alerts
 * - Progress tracking
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Mic,
  MicOff,
  RotateCcw,
  Check,
  AlertTriangle,
  Volume2,
  VolumeX,
  BookOpen,
  Trophy,
  AlertCircle,
  Eye,
  EyeOff,
  Hand,
  Zap,
  Settings2,
} from 'lucide-react';
import clsx from 'clsx';
import { api } from '../lib/api';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import {
  useTasmeeWebSocket,
  type MistakeAlert,
  type RevealMode,
} from '../hooks/useTasmeeWebSocket';

// Types
interface TasmeeSession {
  id: number;
  status: string;
  sura_no: number;
  sura_name_ar?: string;
  sura_name_en?: string;
  aya_start: number;
  aya_end: number;
  total_words: number;
  words_completed: number;
  mistakes_count: number;
  accuracy_score?: number;
  completion_percentage: number;
  expected_text?: string;
  highlighted_words?: Array<{
    word: string;
    normalized: string;
    position: number;
    status: string;
    mistake_type?: string;
  }>;
}

interface Surah {
  number: number;
  name_ar: string;
  name_en: string;
  total_verses: number;
}

// Surah list
const SURAHS: Surah[] = [
  { number: 1, name_ar: 'الفاتحة', name_en: 'Al-Fatiha', total_verses: 7 },
  { number: 2, name_ar: 'البقرة', name_en: 'Al-Baqarah', total_verses: 286 },
  { number: 3, name_ar: 'آل عمران', name_en: "Ali 'Imran", total_verses: 200 },
  { number: 36, name_ar: 'يس', name_en: 'Ya-Sin', total_verses: 83 },
  { number: 55, name_ar: 'الرحمن', name_en: 'Ar-Rahman', total_verses: 78 },
  { number: 56, name_ar: 'الواقعة', name_en: "Al-Waqi'ah", total_verses: 96 },
  { number: 67, name_ar: 'الملك', name_en: 'Al-Mulk', total_verses: 30 },
  { number: 78, name_ar: 'النبأ', name_en: 'An-Naba', total_verses: 40 },
  { number: 112, name_ar: 'الإخلاص', name_en: 'Al-Ikhlas', total_verses: 4 },
  { number: 113, name_ar: 'الفلق', name_en: 'Al-Falaq', total_verses: 5 },
  { number: 114, name_ar: 'الناس', name_en: 'An-Nas', total_verses: 6 },
];

// Alert sound (base64 encoded short beep)
const ALERT_SOUND =
  'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1mZ2llhIyNjI2LhoJ+enZ1eHuAhImLjY2Ni4eFgn57eHd4e3+Dh4qMjY2MioeDgHx5d3Z3en2BhYiLjI2MioiEgX15dnd3eXyAg4eJi4yMi4mGg4B8eXd2d3l8f4OGiYuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDf3x5d3Z3eXx/g4aIi4yMi4mGg398eXd2d3l8f4OGiIuMjIuJhoN/fHl3dnd5fH+DhoiLjIyLiYaDf3x5d3Z3eXx/g4aIi4yMi4mGg398eXd2d3l8f4OGiIuMjIuJhoN/fHl3dnd5fH+DhoiLjIyLiYaDf3x5d3Z3eXx/g4aIi4yMi4mGg398eXd2d3l8f4OGiIuMjIuJhoN/fHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fA==';

export default function TasmeePage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  // Selection state
  const [selectedSurah, setSelectedSurah] = useState<number>(1);
  const [ayaStart, setAyaStart] = useState<number>(1);
  const [ayaEnd, setAyaEnd] = useState<number>(7);

  // Session state
  const [session, setSession] = useState<TasmeeSession | null>(null);
  const [showMistakeBanner, setShowMistakeBanner] = useState(false);
  const [lastMistake, setLastMistake] = useState<MistakeAlert | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);

  // Settings state
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showFullText, setShowFullText] = useState(false);
  const [_showSettings, _setShowSettings] = useState(false);
  const [showDebug, setShowDebug] = useState(true);  // Debug panel visible by default

  // Timer ref
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const alertAudioRef = useRef<HTMLAudioElement | null>(null);

  // WebSocket hook
  const ws = useTasmeeWebSocket({
    sessionId: session?.id || 0,
    onPointerUpdate: (position, progress) => {
      setSession((prev) =>
        prev
          ? {
              ...prev,
              words_completed: position,
              completion_percentage: progress * 100,
            }
          : null
      );
    },
    onMistakeAlert: (mistake) => {
      showMistakeAlertBanner(mistake);
    },
    onComplete: () => {
      handleComplete();
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  // Initialize alert audio
  useEffect(() => {
    alertAudioRef.current = new Audio(ALERT_SOUND);
    alertAudioRef.current.volume = 0.5;
  }, []);

  // Get current surah
  const currentSurah = SURAHS.find((s) => s.number === selectedSurah) || SURAHS[0];

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/tasmee/sessions', {
        sura_no: selectedSurah,
        aya_start: ayaStart,
        aya_end: ayaEnd,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setSession(data);
    },
  });

  // Complete session mutation
  const completeSessionMutation = useMutation({
    mutationFn: async () => {
      if (!session) return null;
      const response = await api.post(`/tasmee/sessions/${session.id}/complete`);
      return response.data;
    },
    onSuccess: (data) => {
      if (data) {
        setSession((prev) =>
          prev
            ? {
                ...prev,
                status: 'completed',
                accuracy_score: data.accuracy_score,
                completion_percentage: data.completion_percentage,
              }
            : null
        );
        stopRecording();
      }
    },
  });

  // Show mistake alert
  const showMistakeAlertBanner = useCallback(
    (mistake: MistakeAlert) => {
      setLastMistake(mistake);
      setShowMistakeBanner(true);

      // Play alert sound
      if (soundEnabled && alertAudioRef.current) {
        alertAudioRef.current.currentTime = 0;
        alertAudioRef.current.play().catch(() => {});
      }

      // Hide banner after 3 seconds
      setTimeout(() => {
        setShowMistakeBanner(false);
      }, 3000);
    },
    [soundEnabled]
  );

  // Connect WebSocket when session is created
  useEffect(() => {
    if (session?.id && session.status === 'active') {
      ws.connect();
    }
    return () => {
      ws.disconnect();
    };
  }, [session?.id, session?.status]);

  // Start recording
  const startRecording = async () => {
    console.log('[TasmeePage] startRecording called, ws.isConnected:', ws.isConnected);
    try {
      await ws.startStreaming();
      console.log('[TasmeePage] startStreaming completed');

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('[TasmeePage] startRecording error:', error);
    }
  };

  // Stop recording
  const stopRecording = () => {
    ws.stopStreaming();
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  // Handle complete
  const handleComplete = () => {
    completeSessionMutation.mutate();
  };

  // Reset session
  const resetSession = () => {
    stopRecording();
    ws.disconnect();
    setSession(null);
    setRecordingTime(0);
    setShowMistakeBanner(false);
  };

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get mistake type label
  const getMistakeLabel = (type: string) => {
    const labels: Record<string, { ar: string; en: string }> = {
      substitution: { ar: 'كلمة خاطئة', en: 'Wrong word' },
      deletion: { ar: 'كلمة محذوفة', en: 'Skipped word' },
      insertion: { ar: 'كلمة زائدة', en: 'Extra word' },
      repetition: { ar: 'تكرار', en: 'Repetition' },
      mispronunciation: { ar: 'نطق خاطئ', en: 'Mispronunciation' },
    };
    return labels[type]?.[language] || type;
  };

  // Get reveal mode label
  const getRevealModeLabel = (mode: RevealMode) => {
    const labels: Record<RevealMode, { ar: string; en: string }> = {
      auto: { ar: 'تلقائي', en: 'Auto' },
      smart_tap: { ar: 'بالنقر', en: 'Smart Tap' },
      hybrid: { ar: 'مختلط', en: 'Hybrid' },
    };
    return labels[mode][language];
  };

  // Handle tap to reveal
  const handleTapToReveal = () => {
    console.log('[TasmeePage] handleTapToReveal called, mode:', ws.config.revealMode, 'showFullText:', showFullText);
    if (ws.config.revealMode !== 'auto' || showFullText) {
      console.log('[TasmeePage] Sending reveal request');
      ws.sendRevealRequest();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  // Calculate progress
  const progress = ws.totalWords > 0 ? (ws.pointer / ws.totalWords) * 100 : 0;

  return (
    <div className="min-h-screen bg-gray-50" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex items-center gap-3 mb-2">
            <BookOpen className="w-8 h-8" />
            <h1 className={clsx('text-3xl font-bold', isArabic && 'font-arabic')}>{t('tasmee_title', language)}</h1>
          </div>
          <p className={clsx('text-emerald-100', isArabic && 'font-arabic')}>{t('tasmee_subtitle', language)}</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Selection Panel (shown when no active session) */}
        {!session && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className={clsx('text-xl font-semibold text-gray-800 mb-4', isArabic && 'font-arabic')}>
              {t('tasmee_select_range', language)}
            </h2>

            {/* Surah Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('tasmee_surah', language)}
              </label>
              <select
                value={selectedSurah}
                onChange={(e) => {
                  const surah = SURAHS.find((s) => s.number === Number(e.target.value));
                  setSelectedSurah(Number(e.target.value));
                  setAyaStart(1);
                  setAyaEnd(surah?.total_verses || 1);
                }}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                {SURAHS.map((surah) => (
                  <option key={surah.number} value={surah.number}>
                    {surah.number}. {isArabic ? surah.name_ar : surah.name_en}
                  </option>
                ))}
              </select>
            </div>

            {/* Ayah Range */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('tasmee_aya_start', language)}
                </label>
                <input
                  type="number"
                  min={1}
                  max={currentSurah.total_verses}
                  value={ayaStart}
                  onChange={(e) => setAyaStart(Math.min(Number(e.target.value), ayaEnd))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('tasmee_aya_end', language)}
                </label>
                <input
                  type="number"
                  min={ayaStart}
                  max={currentSurah.total_verses}
                  value={ayaEnd}
                  onChange={(e) => setAyaEnd(Math.max(Number(e.target.value), ayaStart))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>

            {/* Start Button */}
            <button
              onClick={() => createSessionMutation.mutate()}
              disabled={createSessionMutation.isPending}
              className="w-full bg-emerald-600 text-white py-4 rounded-lg font-semibold hover:bg-emerald-700 transition-colors disabled:bg-gray-400"
            >
              {createSessionMutation.isPending
                ? t('loading', language)
                : t('tasmee_start_session', language)}
            </button>
          </div>
        )}

        {/* Active Session */}
        {session && (
          <>
            {/* Session Info */}
            <div className="bg-white rounded-xl shadow-lg p-4 mb-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">
                    {isArabic ? session.sura_name_ar : session.sura_name_en}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {t('tasmee_verses', language)} {session.aya_start} - {session.aya_end}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  {/* Progress */}
                  <div className="text-center">
                    <div className="text-2xl font-bold text-emerald-600">
                      {Math.round(progress)}%
                    </div>
                    <div className="text-xs text-gray-500">{t('tasmee_progress', language)}</div>
                  </div>
                  {/* Mistakes */}
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-500">{ws.mistakes.length}</div>
                    <div className="text-xs text-gray-500">{t('tasmee_mistakes', language)}</div>
                  </div>
                  {/* Time */}
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-700">
                      {formatTime(recordingTime)}
                    </div>
                    <div className="text-xs text-gray-500">{t('tasmee_time', language)}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Reveal Mode Controls */}
            <div className="bg-white rounded-xl shadow-lg p-4 mb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700">
                    {t('reveal_mode', language)}:
                  </span>
                  <div className="flex gap-1">
                    {(['auto', 'smart_tap', 'hybrid'] as RevealMode[]).map((mode) => (
                      <button
                        key={mode}
                        onClick={() => ws.updateConfig({ revealMode: mode })}
                        className={clsx(
                          'px-3 py-1 text-sm rounded-full transition-colors',
                          ws.config.revealMode === mode
                            ? 'bg-emerald-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        )}
                      >
                        {mode === 'auto' && <Zap className="w-3 h-3 inline me-1" />}
                        {mode === 'smart_tap' && <Hand className="w-3 h-3 inline me-1" />}
                        {mode === 'hybrid' && <Settings2 className="w-3 h-3 inline me-1" />}
                        {getRevealModeLabel(mode)}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Words per tap (for tap modes) */}
                  {(ws.config.revealMode === 'smart_tap' || ws.config.revealMode === 'hybrid') && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">{t('words_per_tap', language)}:</span>
                      <select
                        value={ws.config.tapRevealCount}
                        onChange={(e) =>
                          ws.updateConfig({ tapRevealCount: Number(e.target.value) as 1 | 3 })
                        }
                        className="text-sm border border-gray-300 rounded px-2 py-1"
                      >
                        <option value={1}>1</option>
                        <option value={3}>3</option>
                      </select>
                    </div>
                  )}

                  {/* Show full text toggle */}
                  <button
                    onClick={() => setShowFullText(!showFullText)}
                    className={clsx(
                      'p-2 rounded-lg transition-colors',
                      showFullText ? 'bg-emerald-100 text-emerald-600' : 'bg-gray-100 text-gray-600'
                    )}
                    title={t('show_full_text', language)}
                  >
                    {showFullText ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Debug Panel */}
            {showDebug && (
              <div className="bg-gray-800 text-green-400 font-mono text-xs p-4 mb-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-white">🔧 Debug Panel</span>
                  <button
                    onClick={() => setShowDebug(false)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-gray-500">WS Status:</span>{' '}
                    <span className={ws.isConnected ? 'text-green-400' : 'text-red-400'}>
                      {ws.isConnected ? '✓ Connected' : '✗ Disconnected'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Streaming:</span>{' '}
                    <span className={ws.isStreaming ? 'text-green-400' : 'text-yellow-400'}>
                      {ws.isStreaming ? '🎤 Active' : '⏸ Inactive'}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Mode:</span>{' '}
                    <span className="text-cyan-400">{ws.config.revealMode}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Pointer:</span>{' '}
                    <span className="text-yellow-400">{ws.pointer} / {ws.totalWords}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Revealed:</span>{' '}
                    <span className="text-yellow-400">{ws.revealedUpTo} / {ws.totalWords}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Mistakes:</span>{' '}
                    <span className="text-red-400">{ws.mistakes.length}</span>
                  </div>

                  {/* Audio Level Meter - full width */}
                  <div className="col-span-2 mt-2">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500 w-20">Audio Level:</span>
                      <div className="flex-1 h-4 bg-gray-700 rounded overflow-hidden">
                        <div
                          className={clsx(
                            'h-full transition-all duration-75',
                            ws.audioLevel > 0.1 ? 'bg-green-500' : ws.audioLevel > 0.01 ? 'bg-yellow-500' : 'bg-gray-600'
                          )}
                          style={{ width: `${Math.min(ws.audioLevel * 500, 100)}%` }}
                        />
                      </div>
                      <span className="text-cyan-400 w-12 text-right">{(ws.audioLevel * 100).toFixed(1)}%</span>
                    </div>
                    {ws.isStreaming && ws.audioLevel < 0.001 && (
                      <div className="text-yellow-400 mt-1 text-[10px]">
                        ⚠ No audio detected - check microphone
                      </div>
                    )}
                  </div>

                  {ws.error && (
                    <div className="col-span-2">
                      <span className="text-gray-500">Error:</span>{' '}
                      <span className="text-red-400">{ws.error}</span>
                    </div>
                  )}
                </div>
                <div className="mt-2 text-gray-500 text-[10px]">
                  Open browser DevTools console (F12) for detailed logs
                </div>
              </div>
            )}

            {/* Show Debug Toggle when hidden */}
            {!showDebug && (
              <button
                onClick={() => setShowDebug(true)}
                className="text-xs text-gray-400 mb-2 hover:text-gray-600"
              >
                🔧 Show Debug
              </button>
            )}

            {/* Microphone Error Banner */}
            {ws.error && (
              <div className={clsx(
                "border-l-4 p-4 mb-4 rounded-r-lg",
                ws.error.includes('HTTPS_REQUIRED') ? "bg-amber-100 border-amber-500" : "bg-red-100 border-red-500"
              )}>
                <div className="flex items-start gap-3">
                  {ws.error.includes('HTTPS_REQUIRED') ? (
                    <AlertCircle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <MicOff className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <div className={clsx(
                      "font-semibold",
                      ws.error.includes('HTTPS_REQUIRED') ? "text-amber-700" : "text-red-700"
                    )}>
                      {ws.error.includes('HTTPS_REQUIRED') ? '🔒 HTTPS Required for Microphone' : 'Microphone Error'}
                    </div>
                    <div className={clsx(
                      "text-sm mt-1",
                      ws.error.includes('HTTPS_REQUIRED') ? "text-amber-600" : "text-red-600"
                    )}>
                      {ws.error.includes('HTTPS_REQUIRED') ? (
                        <>
                          <p>Microphone access requires a secure connection (HTTPS).</p>
                          <p className="mt-2 font-medium">Solutions:</p>
                          <ul className="list-disc ml-4 mt-1 space-y-1">
                            <li>Access via <code className="bg-amber-200 px-1 rounded">http://localhost:3000</code> (allowed for local testing)</li>
                            <li>Configure HTTPS on your server with a valid certificate</li>
                            <li>Use a reverse proxy (nginx/Caddy) with HTTPS</li>
                          </ul>
                          <p className="mt-2 text-xs text-amber-500">
                            Current URL: {window.location.href}
                          </p>
                        </>
                      ) : (
                        <p>{ws.error.split(': ').slice(1).join(': ') || ws.error}</p>
                      )}
                    </div>
                    {!ws.error.includes('HTTPS_REQUIRED') && (
                      <button
                        onClick={() => ws.startStreaming()}
                        className="mt-2 text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                      >
                        Try Again
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Mistake Banner */}
            {showMistakeBanner && lastMistake && (
              <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-r-lg animate-pulse">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-red-500" />
                  <div>
                    <div className="font-semibold text-red-700">
                      {getMistakeLabel(lastMistake.mistakeType)}
                    </div>
                    <div className="text-sm text-red-600">
                      {t('tasmee_expected', language)}:{' '}
                      <span className="font-arabic text-lg">{lastMistake.expectedWord}</span>
                      {lastMistake.actualWord && (
                        <>
                          {' '}
                          | {t('tasmee_heard', language)}:{' '}
                          <span className="font-arabic text-lg">{lastMistake.actualWord}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Quran Text Display - Progressive Reveal */}
            <div
              className="bg-white rounded-xl shadow-lg p-6 mb-4 cursor-pointer"
              onClick={handleTapToReveal}
            >
              {/* Tap to reveal hint */}
              {ws.config.revealMode !== 'auto' && !showFullText && (
                <div className="text-center text-sm text-gray-400 mb-4">
                  {t('tap_to_reveal', language)}
                </div>
              )}

              <div className="text-3xl leading-loose text-right font-arabic" dir="rtl">
                {ws.words.map((word, idx) => {
                  const isRevealed = showFullText || word.isRevealed;
                  const isCurrent = idx === ws.pointer;
                  const isCompleted = idx < ws.pointer;
                  const hasError = word.status === 'error';

                  return (
                    <span
                      key={idx}
                      className={clsx(
                        'inline-block px-1 py-0.5 mx-0.5 rounded transition-all duration-300',
                        // Hidden state - blank placeholder
                        !isRevealed && 'bg-gray-200 text-transparent select-none',
                        // Revealed states
                        isRevealed && isCompleted && !hasError && 'bg-emerald-100 text-emerald-800',
                        isRevealed && isCurrent && 'bg-amber-200 text-amber-900 scale-110 font-bold',
                        isRevealed && !isCompleted && !isCurrent && !hasError && 'text-gray-600',
                        isRevealed && hasError && 'bg-red-100 text-red-800 line-through'
                      )}
                    >
                      {isRevealed ? word.word : '\u2003'.repeat(Math.max(1, word.word.length / 2))}
                    </span>
                  );
                })}
              </div>

              {/* Progress bar */}
              <div className="mt-4">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>
                    {ws.pointer} / {ws.totalWords} {t('tasmee_total_words', language)}
                  </span>
                  <span>
                    {ws.revealedUpTo} {t('reveal_mode', language).toLowerCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* Recording Controls */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              {/* Audio Level Indicator */}
              {ws.isStreaming && (
                <div className="mb-4">
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 transition-all duration-100"
                      style={{ width: `${ws.audioLevel * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Control Buttons */}
              <div className="flex items-center justify-center gap-4">
                {/* Sound Toggle */}
                <button
                  onClick={() => setSoundEnabled(!soundEnabled)}
                  className="p-3 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                  title={soundEnabled ? 'Mute alerts' : 'Enable alerts'}
                >
                  {soundEnabled ? (
                    <Volume2 className="w-6 h-6 text-gray-600" />
                  ) : (
                    <VolumeX className="w-6 h-6 text-gray-400" />
                  )}
                </button>

                {/* Main Record Button */}
                {!ws.isStreaming ? (
                  <button
                    onClick={startRecording}
                    disabled={!ws.isConnected}
                    className="p-6 rounded-full bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-lg disabled:bg-gray-400"
                  >
                    <Mic className="w-8 h-8" />
                  </button>
                ) : (
                  <>
                    {/* Stop */}
                    <button
                      onClick={stopRecording}
                      className="p-6 rounded-full bg-red-600 text-white hover:bg-red-700 transition-colors shadow-lg animate-pulse"
                    >
                      <MicOff className="w-8 h-8" />
                    </button>
                  </>
                )}

                {/* Tap Reveal Button (for tap modes) */}
                {(ws.config.revealMode === 'smart_tap' || ws.config.revealMode === 'hybrid') && (
                  <button
                    onClick={() => ws.sendRevealRequest()}
                    className="p-4 rounded-full bg-blue-500 text-white hover:bg-blue-600 transition-colors"
                    title={t('tap_to_reveal', language)}
                  >
                    <Eye className="w-6 h-6" />
                  </button>
                )}

                {/* Reset */}
                <button
                  onClick={resetSession}
                  className="p-3 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                  title={t('tasmee_reset', language)}
                >
                  <RotateCcw className="w-6 h-6 text-gray-600" />
                </button>

                {/* Complete */}
                {session.status === 'active' && ws.pointer > 0 && (
                  <button
                    onClick={handleComplete}
                    disabled={completeSessionMutation.isPending}
                    className="p-3 rounded-full bg-emerald-100 hover:bg-emerald-200 transition-colors"
                    title={t('tasmee_complete', language)}
                  >
                    <Check className="w-6 h-6 text-emerald-600" />
                  </button>
                )}
              </div>

              {/* Status Text */}
              <div className="text-center mt-4 text-sm text-gray-500">
                {!ws.isConnected ? (
                  <span className="text-amber-500">Connecting...</span>
                ) : ws.isStreaming ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    {t('tasmee_recording', language)}
                  </span>
                ) : (
                  t('tasmee_tap_to_start', language)
                )}
              </div>
            </div>

            {/* Mistakes List */}
            {ws.mistakes.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6 mt-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-orange-500" />
                  {t('tasmee_mistakes_list', language)}
                </h3>
                <div className="space-y-2">
                  {ws.mistakes.map((mistake, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <span className="font-arabic text-lg">{mistake.expectedWord}</span>
                        <span className="text-sm text-gray-500 mx-2">→</span>
                        <span className="font-arabic text-lg text-red-600">
                          {mistake.actualWord || '(skipped)'}
                        </span>
                      </div>
                      <span
                        className={clsx(
                          'text-xs px-2 py-1 rounded-full',
                          mistake.severity === 'major' && 'bg-red-100 text-red-700',
                          mistake.severity === 'moderate' && 'bg-orange-100 text-orange-700',
                          mistake.severity === 'minor' && 'bg-yellow-100 text-yellow-700'
                        )}
                      >
                        {getMistakeLabel(mistake.mistakeType)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Completion Summary */}
            {session.status === 'completed' && (
              <div className="bg-emerald-50 rounded-xl shadow-lg p-6 mt-4">
                <div className="text-center">
                  <Trophy className="w-12 h-12 text-emerald-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-emerald-800 mb-2">
                    {t('tasmee_completed', language)}
                  </h3>
                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="bg-white p-4 rounded-lg">
                      <div className="text-2xl font-bold text-emerald-600">
                        {Math.round((session.accuracy_score || 0) * 100)}%
                      </div>
                      <div className="text-sm text-gray-500">{t('tasmee_accuracy', language)}</div>
                    </div>
                    <div className="bg-white p-4 rounded-lg">
                      <div className="text-2xl font-bold text-gray-700">{session.total_words}</div>
                      <div className="text-sm text-gray-500">
                        {t('tasmee_total_words', language)}
                      </div>
                    </div>
                    <div className="bg-white p-4 rounded-lg">
                      <div className="text-2xl font-bold text-orange-500">{ws.mistakes.length}</div>
                      <div className="text-sm text-gray-500">{t('tasmee_mistakes', language)}</div>
                    </div>
                  </div>
                  <button
                    onClick={resetSession}
                    className="mt-6 px-6 py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
                  >
                    {t('tasmee_try_again', language)}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
