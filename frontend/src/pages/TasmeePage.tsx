/**
 * Tasmeeʿ (Memorization) Page - Progressive Reveal
 *
 * A memorization practice tool: the app follows the user's recitation word
 * by word with automatic speech recognition and reveals the words as they
 * are recited. It checks words only (not harakat or tajweed) and can mishear;
 * the copy says so and never claims to correct or grade recitation.
 *
 * Features:
 * - Select Surah and Ayah range
 * - Word-by-word follow-along via WebSocket
 * - Progressive word reveal (blank-first display): Auto, Smart Tap, Hybrid
 * - Possible-slip alerts (skipped / unclear / possibly different word)
 * - Practice without speech recognition (reveal words yourself) when the
 *   service is unavailable
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
  AlertCircle,
  Eye,
  EyeOff,
  Hand,
  Zap,
  Settings2,
  Info,
} from 'lucide-react';
import clsx from 'clsx';
import { api } from '../lib/api';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { SURAH_NAMES, SURAH_VERSE_COUNTS } from '../data/surahNames';
import {
  rememberTasmeeSession,
  useTasmeeWebSocket,
  type MistakeAlert,
  type RevealMode,
} from '../hooks/useTasmeeWebSocket';

// Types
interface TasmeeSession {
  id: string;
  status: string;
  sura_no: number;
  sura_name_ar?: string;
  sura_name_en?: string;
  aya_start: number;
  aya_end: number;
  total_words: number;
  words_completed: number;
  words_correct?: number;
  mistakes_count: number;
  accuracy_score?: number;
  completion_percentage: number;
  expected_text?: string;
  client_token?: string | null;
  highlighted_words?: Array<{
    word: string;
    normalized: string;
    position: number;
    status: string;
    mistake_type?: string;
  }>;
}

interface TasmeeHealth {
  stt_available: boolean;
  stt_error?: string | null;
}

// Alert sound (base64 encoded short beep)
const ALERT_SOUND =
  'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1mZ2llhIyNjI2LhoJ+enZ1eHuAhImLjY2Ni4eFgn57eHd4e3+Dh4qMjY2MioeDgHx5d3Z3en2BhYiLjI2MioiEgX15dnd3eXyAg4eJi4yMi4mGg4B8eXd2d3l8f4OGiYuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDf3x5d3Z3eXx/g4aIi4yMi4mGg398eXd2d3l8f4OGiIuMjIuJhoN/fHl3dnd5fH+DhoiLjIyLiYaDf3x5d3Z3eXx/g4aIi4yMi4mGg398eXd2d3l8f4OGiIuMjIuJhoN/fHl3dnd5fH+DhoiLjIyLiYaDf3x5d3Z3eXx/g4aIi4yMi4mGg398eXd2d3l8f4OGiIuMjIuJhoN/fHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5dnd5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fH+DhoiLjIyLiYaDgHx5d3Z3eXx/g4aIi4yMi4mGg4B8eXd3eXx/g4aIi4yMi4mGg4B8eXd2d3l8f4OGiIuMjIuJhoOAfHl3d3l8f4OGiIuMjIuJhoOAfHl3dnd5fH+DhoiLjIyLiYaDgHx5d3d5fA==';

type Lang = 'ar' | 'en';
const L = (lang: Lang, ar: string, en: string) => (lang === 'ar' ? ar : en);

/** Localised banner title/body for a hook error code. */
function describeError(code: string, lang: Lang): { title: string; body: string } {
  const [kind, detail] = code.split(':');
  switch (kind) {
    case 'PERMISSION_DENIED':
      return {
        title: L(lang, 'لم يُسمح باستخدام الميكروفون', 'Microphone permission denied'),
        body: L(lang,
          'اسمح للتطبيق باستخدام الميكروفون من إعدادات الجهاز أو المتصفح، ثم حاول مجددًا.',
          'Allow microphone access for this app in your device or browser settings, then try again.'),
      };
    case 'NO_MICROPHONE':
      return {
        title: L(lang, 'لا يوجد ميكروفون', 'No microphone found'),
        body: L(lang, 'وصّل ميكروفونًا ثم حاول مجددًا.', 'Connect a microphone and try again.'),
      };
    case 'MIC_IN_USE':
      return {
        title: L(lang, 'الميكروفون مستخدم', 'Microphone in use'),
        body: L(lang, 'يستخدم تطبيق آخر الميكروفون. أغلقه ثم حاول مجددًا.', 'Another app is using the microphone. Close it and try again.'),
      };
    case 'HTTPS_REQUIRED':
      return {
        title: L(lang, 'يلزم اتصال آمن', 'Secure connection required'),
        body: L(lang, 'يعمل الميكروفون فقط عبر اتصال آمن (https).', 'The microphone only works over a secure (https) connection.'),
      };
    case 'MIC_UNSUPPORTED':
      return {
        title: L(lang, 'الميكروفون غير مدعوم', 'Microphone not supported'),
        body: L(lang, 'هذا المتصفح لا يتيح استخدام الميكروفون. جرّب متصفحًا حديثًا.', 'This browser cannot use the microphone. Try a recent browser.'),
      };
    case 'RECORDING_INTERRUPTED':
      return {
        title: L(lang, 'توقّف التسجيل', 'Recording stopped'),
        body: detail === 'background'
          ? L(lang, 'توقّف التسجيل لأن التطبيق انتقل إلى الخلفية. اضغط «حاول مجددًا» للمتابعة.', 'Recording stopped because the app went to the background. Tap Try again to continue.')
          : L(lang, 'أوقف النظام الميكروفون (مكالمة أو تطبيق آخر). اضغط «حاول مجددًا» للمتابعة.', 'The system stopped the microphone (a call or another app). Tap Try again to continue.'),
      };
    case 'CONNECTION_LOST':
    case 'NOT_CONNECTED':
      return {
        title: L(lang, 'انقطع الاتصال بالخادم', 'Connection lost'),
        body: L(lang, 'توقّف التسجيل. حاول مجددًا عند عودة الاتصال.', 'Recording stopped. Try again when you are back online.'),
      };
    case 'SESSION_LIMIT':
      return {
        title: L(lang, 'بلغت الجلسة حدّها', 'Session limit reached'),
        body: L(lang, 'تتسع الجلسة الواحدة لعشر دقائق من التلاوة. ابدأ جلسة جديدة للمتابعة.', 'A session holds up to 10 minutes of recitation. Start a new session to continue.'),
      };
    case 'RATE_LIMITED':
      return {
        title: L(lang, 'محاولات كثيرة', 'Too many attempts'),
        body: L(lang, 'انتظر دقيقة ثم حاول مجددًا.', 'Wait a minute, then try again.'),
      };
    case 'SESSION_NOT_ACTIVE':
    case 'SESSION_NOT_FOUND':
    case 'SESSION_UNAUTHORIZED':
      return {
        title: L(lang, 'انتهت الجلسة', 'Session ended'),
        body: L(lang, 'ابدأ جلسة جديدة.', 'Start a new session.'),
      };
    default:
      return {
        title: L(lang, 'تعذّر تشغيل الميكروفون', 'Could not start the microphone'),
        body: L(lang, 'حاول مجددًا.', 'Please try again.'),
      };
  }
}

/** Possible-slip labels: honest about what word matching can tell. */
function mistakeLabel(type: string, lang: Lang): string {
  const labels: Record<string, [string, string]> = {
    substitution: ['ربما كلمة مختلفة', 'Possible different word'],
    deletion: ['كلمة متروكة', 'Skipped word'],
    insertion: ['كلمة زائدة', 'Extra word'],
    repetition: ['تكرار', 'Repetition'],
    mispronunciation: ['كلمة غير واضحة', 'Unclear word'],
  };
  const pair = labels[type];
  return pair ? L(lang, pair[0], pair[1]) : type;
}

function revealModeLabel(mode: RevealMode, lang: Lang): string {
  const labels: Record<RevealMode, [string, string]> = {
    auto: ['تلقائي', 'Auto'],
    smart_tap: ['بالنقر', 'Smart Tap'],
    hybrid: ['مختلط', 'Hybrid'],
  };
  return L(lang, labels[mode][0], labels[mode][1]);
}

export default function TasmeePage() {
  const { language } = useLanguageStore();
  const lang: Lang = language === 'ar' ? 'ar' : 'en';
  const isArabic = lang === 'ar';

  // Selection state
  const [selectedSurah, setSelectedSurah] = useState<number>(1);
  const [ayaStart, setAyaStart] = useState<number>(1);
  const [ayaEnd, setAyaEnd] = useState<number>(7);

  // Session state
  const [session, setSession] = useState<TasmeeSession | null>(null);
  const [token, setToken] = useState<string>('');
  const [showMistakeBanner, setShowMistakeBanner] = useState(false);
  const [lastMistake, setLastMistake] = useState<MistakeAlert | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [silentSeconds, setSilentSeconds] = useState(0);

  // Speech recognition availability (checked up front)
  const [health, setHealth] = useState<TasmeeHealth | null>(null);
  const [healthChecked, setHealthChecked] = useState(false);

  // Settings state
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showFullText, setShowFullText] = useState(false);
  // Developer panel: development builds only.
  const [showDebug, setShowDebug] = useState<boolean>(import.meta.env.DEV);

  // Timer ref
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const alertAudioRef = useRef<HTMLAudioElement | null>(null);

  const ws = useTasmeeWebSocket({
    sessionId: session?.id ?? '',
    token,
    onPointerUpdate: (position, progress) => {
      setSession((prev) =>
        prev ? { ...prev, words_completed: position, completion_percentage: progress * 100 } : null
      );
    },
    onMistakeAlert: (mistake) => {
      showMistakeAlertBanner(mistake);
    },
    onComplete: () => {
      handleComplete();
    },
  });

  const sttDown = ws.sttUnavailable || (healthChecked && health?.stt_available === false);

  const checkHealth = useCallback(async () => {
    try {
      const res = await api.get<TasmeeHealth>('/tasmee/health');
      setHealth(res.data);
    } catch {
      setHealth({ stt_available: false, stt_error: 'unreachable' });
    } finally {
      setHealthChecked(true);
    }
  }, []);

  useEffect(() => {
    void checkHealth();
  }, [checkHealth]);

  // Initialize alert audio
  useEffect(() => {
    alertAudioRef.current = new Audio(ALERT_SOUND);
    alertAudioRef.current.volume = 0.5;
  }, []);

  const surahVerseCount = SURAH_VERSE_COUNTS[selectedSurah - 1] ?? 1;

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post<TasmeeSession>('/tasmee/sessions', {
        sura_no: selectedSurah,
        aya_start: ayaStart,
        aya_end: ayaEnd,
      });
      return response.data;
    },
    onSuccess: (data) => {
      const sessionToken = data.client_token ?? '';
      if (sessionToken) rememberTasmeeSession(data.id, sessionToken);
      setToken(sessionToken);
      ws.clear();
      ws.loadWords((data.highlighted_words ?? []).map((w) => ({ word: w.word, position: w.position })));
      if (health?.stt_available === false) ws.markSttUnavailable(health.stt_error ?? 'unavailable');
      setSession({ ...data, client_token: null });
    },
  });

  // Complete session mutation
  const completeSessionMutation = useMutation({
    mutationFn: async () => {
      if (!session || !token) return null;
      const response = await api.post(`/tasmee/sessions/${encodeURIComponent(session.id)}/complete`, null, {
        headers: { 'X-Tasmee-Token': token },
      });
      return response.data as {
        accuracy_score: number;
        completion_percentage: number;
        words_completed: number;
        words_correct: number;
      };
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
                words_completed: data.words_completed,
                words_correct: data.words_correct,
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
      if (soundEnabled && alertAudioRef.current) {
        alertAudioRef.current.currentTime = 0;
        alertAudioRef.current.play().catch(() => {});
      }
      setTimeout(() => setShowMistakeBanner(false), 3000);
    },
    [soundEnabled]
  );

  // Connect WebSocket when a session is created (not when STT is known to be down)
  useEffect(() => {
    if (session?.id && session.status === 'active' && token && health?.stt_available !== false) {
      ws.connect();
    }
    return () => {
      ws.disconnect();
    };
  }, [session?.id, session?.status, token]);

  const startTimer = () => {
    if (timerRef.current) return;
    timerRef.current = setInterval(() => setRecordingTime((prev) => prev + 1), 1000);
  };

  // Start recording: the timer runs only once audio is really streaming.
  const startRecording = async () => {
    const started = await ws.startStreaming();
    if (started) startTimer();
  };

  // The hook can stop streaming on its own (interruption, lost connection,
  // app backgrounded): stop the timer with it.
  useEffect(() => {
    if (!ws.isStreaming && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [ws.isStreaming]);

  // "We can't hear you" hint after 3 s of silence while streaming.
  useEffect(() => {
    if (!ws.isStreaming) {
      setSilentSeconds(0);
      return;
    }
    if (ws.audioLevel >= 0.001) setSilentSeconds(0);
  }, [ws.isStreaming, ws.audioLevel]);
  useEffect(() => {
    if (!ws.isStreaming) return;
    const id = setInterval(() => setSilentSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [ws.isStreaming]);

  // Stop recording
  const stopRecording = () => {
    ws.stopStreaming();
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const handleComplete = () => {
    completeSessionMutation.mutate();
  };

  // Reset session
  const resetSession = () => {
    stopRecording();
    ws.disconnect();
    ws.clear();
    setSession(null);
    setToken('');
    setRecordingTime(0);
    setShowMistakeBanner(false);
  };

  // Retry speech recognition after it was unavailable
  const retryStt = async () => {
    await checkHealth();
    if (session?.id && token) ws.connect();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTapToReveal = () => {
    if (sttDown || ws.config.revealMode !== 'auto' || showFullText) {
      ws.sendRevealRequest();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  const progress = ws.totalWords > 0 ? (ws.pointer / ws.totalWords) * 100 : 0;
  const micError = ws.error && !ws.error.startsWith('STT_UNAVAILABLE') ? describeError(ws.error, lang) : null;
  const sttReason = ws.error?.startsWith('STT_UNAVAILABLE') ? ws.error.split(':')[1] : health?.stt_error;
  const quotaReached = sttReason === 'ai_quota_exceeded' || sttReason === 'quota';
  const wordsCorrect = session?.words_correct ?? 0;

  const sttBanner = (
    <div role="status" className="border-s-4 p-4 mb-4 rounded-e-lg bg-amber-100 border-amber-500">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="font-semibold text-amber-700">
            {quotaReached
              ? L(lang, 'تم بلوغ حدّ خدمة التعرّف على الكلام مؤقتاً', 'Speech recognition limit reached for now')
              : L(lang, 'خدمة التعرّف على الكلام غير متاحة حالياً', 'Speech recognition is unavailable right now')}
          </div>
          <p className="text-sm mt-1 text-amber-700">
            {L(lang,
              'يمكنك متابعة الحفظ بكشف الكلمات بنفسك: سمّع من حفظك ثم اضغط «اكشف الكلمة التالية» لتتحقق.',
              'You can keep practising by revealing words yourself: recite from memory, then tap "Reveal next word" to check.')}
          </p>
          <button
            onClick={() => void retryStt()}
            className="mt-2 text-sm bg-amber-600 text-white px-3 py-1 rounded hover:bg-amber-700"
          >
            {L(lang, 'حاول مجددًا', 'Try again')}
          </button>
        </div>
      </div>
    </div>
  );

  const disclaimer = (
    <div className="flex items-start gap-2 bg-sky-50 border border-sky-200 text-sky-900 rounded-lg p-3 mb-4 text-sm">
      <Info className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
      <p dir={isArabic ? 'rtl' : 'ltr'} lang={lang}>
        {L(lang,
          'التعرّف الآلي على الكلام يتحقق من الكلمات فقط، لا من الحركات ولا من أحكام التجويد، وقد يخطئ السمع. راجع شيخًا متقنًا.',
          'Automatic speech recognition checks words only, not harakat or tajweed, and can mishear. Confirm with a teacher.')}
      </p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex items-center gap-3 mb-2">
            <BookOpen className="w-8 h-8" />
            <h1 className={clsx('text-3xl font-bold', isArabic && 'font-arabic')}>{t('tasmee_title', language)}</h1>
          </div>
          <p className={clsx('text-emerald-100', isArabic && 'font-arabic')}>
            {L(lang, 'تدرّب على الحفظ: يتابع التطبيق تلاوتك كلمةً كلمة', 'Practise memorization: the app follows your recitation word by word')}
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {disclaimer}

        {/* Up-front notice when speech recognition is unavailable */}
        {!session && healthChecked && health?.stt_available === false && sttBanner}

        {/* Selection Panel (shown when no active session) */}
        {!session && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className={clsx('text-xl font-semibold text-gray-800 mb-4', isArabic && 'font-arabic')}>
              {t('tasmee_select_range', language)}
            </h2>

            <div className="mb-4">
              <label htmlFor="tasmee-surah" className="block text-sm font-medium text-gray-700 mb-2">
                {t('tasmee_surah', language)}
              </label>
              <select
                id="tasmee-surah"
                value={selectedSurah}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  setSelectedSurah(n);
                  setAyaStart(1);
                  setAyaEnd(Math.min(SURAH_VERSE_COUNTS[n - 1] ?? 1, 10));
                }}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                {SURAH_NAMES.map((s, i) => (
                  <option key={i + 1} value={i + 1}>
                    {i + 1}. {isArabic ? s.ar : s.en}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label htmlFor="tasmee-from" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('tasmee_aya_start', language)}
                </label>
                <input
                  id="tasmee-from"
                  type="number"
                  min={1}
                  max={surahVerseCount}
                  value={ayaStart}
                  onChange={(e) => setAyaStart(Math.max(1, Math.min(Number(e.target.value), ayaEnd)))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label htmlFor="tasmee-to" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('tasmee_aya_end', language)}
                </label>
                <input
                  id="tasmee-to"
                  type="number"
                  min={ayaStart}
                  max={surahVerseCount}
                  value={ayaEnd}
                  onChange={(e) => setAyaEnd(Math.min(surahVerseCount, Math.max(Number(e.target.value), ayaStart)))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>

            <button
              onClick={() => createSessionMutation.mutate()}
              disabled={createSessionMutation.isPending}
              className="w-full bg-emerald-600 text-white py-4 rounded-lg font-semibold hover:bg-emerald-700 transition-colors disabled:bg-gray-400"
            >
              {createSessionMutation.isPending
                ? t('loading', language)
                : t('tasmee_start_session', language)}
            </button>
            {createSessionMutation.isError && (
              <p role="alert" className="mt-3 text-sm text-red-700">
                {L(lang, 'تعذّر بدء الجلسة. حاول مجددًا بعد قليل.', 'Could not start the session. Please try again shortly.')}
              </p>
            )}
          </div>
        )}

        {/* Active Session */}
        {session && (
          <>
            {/* Session Info */}
            <div className="bg-white rounded-xl shadow-lg p-4 mb-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">
                    {isArabic ? session.sura_name_ar : session.sura_name_en}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {t('tasmee_verses', language)} {session.aya_start} - {session.aya_end}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-emerald-600">{Math.round(progress)}%</div>
                    <div className="text-xs text-gray-500">{t('tasmee_progress', language)}</div>
                  </div>
                  {!sttDown && (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-500">{ws.mistakes.length}</div>
                      <div className="text-xs text-gray-500">{L(lang, 'تنبيهات محتملة', 'Possible slips')}</div>
                    </div>
                  )}
                  {!sttDown && (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-700">{formatTime(recordingTime)}</div>
                      <div className="text-xs text-gray-500">{t('tasmee_time', language)}</div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Reveal Mode Controls (speech recognition only) */}
            {!sttDown && (
              <div className="bg-white rounded-xl shadow-lg p-4 mb-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">{t('reveal_mode', language)}:</span>
                    <div className="flex gap-1" role="group" aria-label={t('reveal_mode', language)}>
                      {(['auto', 'smart_tap', 'hybrid'] as RevealMode[]).map((mode) => (
                        <button
                          key={mode}
                          onClick={() => ws.updateConfig({ revealMode: mode })}
                          aria-pressed={ws.config.revealMode === mode}
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
                          {revealModeLabel(mode, lang)}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {(ws.config.revealMode === 'smart_tap' || ws.config.revealMode === 'hybrid') && (
                      <div className="flex items-center gap-2">
                        <label htmlFor="tasmee-per-tap" className="text-sm text-gray-500">{t('words_per_tap', language)}:</label>
                        <select
                          id="tasmee-per-tap"
                          value={ws.config.tapRevealCount}
                          onChange={(e) => ws.updateConfig({ tapRevealCount: Number(e.target.value) as 1 | 3 })}
                          className="text-sm border border-gray-300 rounded px-2 py-1"
                        >
                          <option value={1}>1</option>
                          <option value={3}>3</option>
                        </select>
                      </div>
                    )}

                    <button
                      onClick={() => setShowFullText(!showFullText)}
                      aria-pressed={showFullText}
                      aria-label={t('show_full_text', language)}
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
            )}

            {/* Developer panel (development builds only) */}
            {import.meta.env.DEV && showDebug && (
              <div className="bg-gray-800 text-green-400 font-mono text-xs p-4 mb-4 rounded-lg" dir="ltr" lang="en">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-white">Debug (dev only)</span>
                  <button onClick={() => setShowDebug(false)} className="text-gray-400 hover:text-white" aria-label="Hide debug">
                    ✕
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>WS: {ws.isConnected ? 'connected' : 'disconnected'}</div>
                  <div>Streaming: {ws.isStreaming ? 'yes' : 'no'}</div>
                  <div>Mode: {ws.config.revealMode}</div>
                  <div>Pointer: {ws.pointer} / {ws.totalWords}</div>
                  <div>Revealed: {ws.revealedUpTo} / {ws.totalWords}</div>
                  <div>Slips: {ws.mistakes.length}</div>
                  <div>STT down: {String(sttDown)}</div>
                  <div>Level: {(ws.audioLevel * 100).toFixed(1)}%</div>
                  {ws.error && <div className="col-span-2 text-red-400">Error: {ws.error}</div>}
                </div>
              </div>
            )}
            {import.meta.env.DEV && !showDebug && (
              <button onClick={() => setShowDebug(true)} className="text-xs text-gray-400 mb-2 hover:text-gray-600" dir="ltr">
                Show debug (dev only)
              </button>
            )}

            {/* Speech recognition unavailable: practise by revealing words yourself */}
            {sttDown && sttBanner}

            {/* Microphone / connection error */}
            {micError && (
              <div role="alert" className="border-s-4 p-4 mb-4 rounded-e-lg bg-red-100 border-red-500">
                <div className="flex items-start gap-3">
                  <MicOff className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-semibold text-red-700">{micError.title}</div>
                    <p className="text-sm mt-1 text-red-700">{micError.body}</p>
                    {ws.error !== 'HTTPS_REQUIRED' && ws.error !== 'MIC_UNSUPPORTED' && (
                      <button
                        onClick={() => {
                          if (ws.isConnected) void startRecording();
                          else ws.connect();
                        }}
                        className="mt-2 text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                      >
                        {L(lang, 'حاول مجددًا', 'Try again')}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* "We can't hear you" */}
            {ws.isStreaming && silentSeconds >= 3 && (
              <div role="status" className="bg-amber-50 border border-amber-200 text-amber-800 rounded-lg p-3 mb-4 text-sm">
                {L(lang,
                  'لا يصلنا صوت. تأكّد من السماح للتطبيق باستخدام الميكروفون واقترب منه.',
                  "We can't hear you. Check that the app may use the microphone and move closer to it.")}
              </div>
            )}

            {/* Possible-slip banner */}
            {showMistakeBanner && lastMistake && (
              <div role="status" className="bg-orange-50 border-s-4 border-orange-400 p-4 mb-4 rounded-e-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-orange-500" />
                  <div>
                    <div className="font-semibold text-orange-800">{mistakeLabel(lastMistake.mistakeType, lang)}</div>
                    <div className="text-sm text-orange-800">
                      {t('tasmee_expected', language)}:{' '}
                      <span className="font-arabic text-lg" dir="rtl" lang="ar">{lastMistake.expectedWord}</span>
                      {lastMistake.actualWord && (
                        <>
                          {' '}| {L(lang, 'تعرّف عليها كـ', 'Recognised as')}:{' '}
                          <span className="font-arabic text-lg" dir="rtl" lang="ar">{lastMistake.actualWord}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Quran Text Display - Progressive Reveal */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-4 cursor-pointer" onClick={handleTapToReveal}>
              {(sttDown || ws.config.revealMode !== 'auto') && !showFullText && (
                <div className="text-center text-sm text-gray-500 mb-4">{t('tap_to_reveal', language)}</div>
              )}

              <div className="text-3xl leading-loose text-right font-arabic" dir="rtl" lang="ar">
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
                        !isRevealed && 'bg-gray-200 text-transparent select-none',
                        isRevealed && isCompleted && !hasError && 'bg-emerald-100 text-emerald-800',
                        isRevealed && isCurrent && 'bg-amber-200 text-amber-900 font-bold',
                        isRevealed && !isCompleted && !isCurrent && !hasError && 'text-gray-600',
                        isRevealed && hasError && 'bg-orange-100 text-orange-900 underline decoration-wavy'
                      )}
                    >
                      {isRevealed ? word.word : ' '.repeat(Math.max(1, word.word.length / 2))}
                    </span>
                  );
                })}
              </div>

              <div className="mt-4">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 transition-all duration-300" style={{ width: `${progress}%` }} />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>{ws.pointer} / {ws.totalWords} {t('tasmee_total_words', language)}</span>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              {ws.isStreaming && (
                <div className="mb-4">
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 transition-all duration-100" style={{ width: `${Math.min(ws.audioLevel * 500, 100)}%` }} />
                  </div>
                </div>
              )}

              <div className="flex items-center justify-center gap-4">
                {!sttDown && (
                  <button
                    onClick={() => setSoundEnabled(!soundEnabled)}
                    className="p-3 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                    aria-pressed={!soundEnabled}
                    aria-label={soundEnabled ? L(lang, 'كتم صوت التنبيهات', 'Mute alerts') : L(lang, 'تشغيل صوت التنبيهات', 'Unmute alerts')}
                    title={soundEnabled ? L(lang, 'كتم صوت التنبيهات', 'Mute alerts') : L(lang, 'تشغيل صوت التنبيهات', 'Unmute alerts')}
                  >
                    {soundEnabled ? <Volume2 className="w-6 h-6 text-gray-600" /> : <VolumeX className="w-6 h-6 text-gray-400" />}
                  </button>
                )}

                {sttDown ? (
                  <button
                    onClick={() => ws.sendRevealRequest(1)}
                    disabled={ws.isComplete || ws.words.length === 0}
                    className="px-6 py-4 rounded-full bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition-colors shadow-lg disabled:bg-gray-400 flex items-center gap-2"
                  >
                    <Eye className="w-6 h-6" />
                    {L(lang, 'اكشف الكلمة التالية', 'Reveal next word')}
                  </button>
                ) : !ws.isStreaming ? (
                  <button
                    onClick={() => void startRecording()}
                    disabled={!ws.isConnected}
                    aria-label={L(lang, 'ابدأ التسجيل', 'Start recording')}
                    className="p-6 rounded-full bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-lg disabled:bg-gray-400"
                  >
                    <Mic className="w-8 h-8" />
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    aria-label={L(lang, 'أوقف التسجيل', 'Stop recording')}
                    className="p-6 rounded-full bg-red-600 text-white hover:bg-red-700 transition-colors shadow-lg animate-pulse"
                  >
                    <MicOff className="w-8 h-8" />
                  </button>
                )}

                {!sttDown && (ws.config.revealMode === 'smart_tap' || ws.config.revealMode === 'hybrid') && (
                  <button
                    onClick={() => ws.sendRevealRequest()}
                    className="p-4 rounded-full bg-blue-500 text-white hover:bg-blue-600 transition-colors"
                    aria-label={t('tap_to_reveal', language)}
                    title={t('tap_to_reveal', language)}
                  >
                    <Eye className="w-6 h-6" />
                  </button>
                )}

                <button
                  onClick={resetSession}
                  className="p-3 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
                  aria-label={t('tasmee_reset', language)}
                  title={t('tasmee_reset', language)}
                >
                  <RotateCcw className="w-6 h-6 text-gray-600" />
                </button>

                {!sttDown && session.status === 'active' && ws.pointer > 0 && (
                  <button
                    onClick={handleComplete}
                    disabled={completeSessionMutation.isPending}
                    className="p-3 rounded-full bg-emerald-100 hover:bg-emerald-200 transition-colors"
                    aria-label={t('tasmee_complete', language)}
                    title={t('tasmee_complete', language)}
                  >
                    <Check className="w-6 h-6 text-emerald-600" />
                  </button>
                )}
              </div>

              <div className="text-center mt-4 text-sm text-gray-500" role="status">
                {sttDown ? (
                  ws.isComplete
                    ? L(lang, 'كُشفت كل الكلمات. أحسنت المراجعة.', 'All words revealed.')
                    : L(lang, 'سمّع من حفظك ثم اكشف الكلمة لتتحقق.', 'Recite from memory, then reveal the word to check.')
                ) : !ws.isConnected ? (
                  <span className="text-amber-600">{L(lang, 'جارٍ الاتصال…', 'Connecting…')}</span>
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

            {/* Possible slips */}
            {!sttDown && ws.mistakes.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6 mt-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-1 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-orange-500" />
                  {L(lang, 'تنبيهات محتملة', 'Possible slips')}
                </h3>
                <p className="text-xs text-gray-500 mb-4">
                  {L(lang, 'قد يخطئ التعرّف الآلي؛ راجعها مع شيخك.', 'Automatic recognition can be wrong; review these with your teacher.')}
                </p>
                <div className="space-y-2">
                  {ws.mistakes.map((mistake, idx) => (
                    <div key={idx} className="flex flex-wrap items-center justify-between gap-2 p-3 bg-gray-50 rounded-lg">
                      <div>
                        <span className="font-arabic text-lg" dir="rtl" lang="ar">{mistake.expectedWord}</span>
                        {mistake.actualWord ? (
                          <span className="text-sm text-gray-600 mx-2">
                            {L(lang, 'تعرّف عليها كـ', 'Recognised as')}:{' '}
                            <span className="font-arabic text-lg" dir="rtl" lang="ar">{mistake.actualWord}</span>
                          </span>
                        ) : (
                          <span className="text-sm text-gray-600 mx-2">({L(lang, 'متروكة', 'skipped')})</span>
                        )}
                      </div>
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-700">
                        {mistakeLabel(mistake.mistakeType, lang)}
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
                  <h3 className="text-xl font-semibold text-emerald-800 mb-2">
                    {L(lang, 'انتهت الجلسة', 'Session finished')}
                  </h3>
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="bg-white p-4 rounded-lg">
                      <div className="text-2xl font-bold text-emerald-600">
                        {wordsCorrect} / {session.total_words}
                      </div>
                      <div className="text-sm text-gray-500">{L(lang, 'الكلمات المتابَعة', 'Words followed')}</div>
                    </div>
                    <div className="bg-white p-4 rounded-lg">
                      <div className="text-2xl font-bold text-orange-500">{ws.mistakes.length}</div>
                      <div className="text-sm text-gray-500">{L(lang, 'تنبيهات محتملة', 'Possible slips')}</div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-3">
                    {L(lang,
                      'هذه متابعة آلية للكلمات وليست تقييمًا للتلاوة.',
                      'This is automatic word following, not an assessment of your recitation.')}
                  </p>
                  <button
                    onClick={resetSession}
                    className="mt-6 px-6 py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
                  >
                    {L(lang, 'جلسة جديدة', 'New session')}
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
