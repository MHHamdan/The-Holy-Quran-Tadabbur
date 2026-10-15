/**
 * Quran Audio Player Component
 *
 * A comprehensive audio player for Quran recitation with:
 * - Multiple reciter selection (remembered)
 * - Verse-by-verse playback in every mode, so the reader can follow along
 * - Per-verse repeat count for memorisation, and whole-range repeat
 * - Speed control (remembered)
 * - Lock-screen / media-key controls through the Media Session API
 * - Save a surah for offline listening (device storage / Cache Storage)
 *
 * Arabic: مشغل صوت القرآن الكريم
 */
import { useState, useEffect, useRef, useCallback, useId } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Download, Repeat, Settings, CheckCircle2, Trash2 } from 'lucide-react';
import { audioApi, ReciterInfo, VerseAudioInfo } from '../../lib/api';
import { Language } from '../../i18n/translations';
import {
  useReaderSettingsStore,
  PLAYBACK_RATES,
  VERSE_REPEATS,
} from '../../stores/readerSettingsStore';
import {
  hasPlaylist,
  isSavedVerse,
  offlineAudioSupported,
  playableUrl,
  recordSurahVerses,
  removeSurah,
  saveSurah,
  savedSurah,
} from '../../lib/offlineAudio';
import clsx from 'clsx';
import { AudioSourceAttribution, audioHost } from './AudioSourceAttribution';

// =============================================================================
// TYPES
// =============================================================================

interface QuranAudioPlayerProps {
  mode: 'surah' | 'verse' | 'page' | 'range';
  suraNo?: number;
  ayaNo?: number;
  ayaStart?: number;
  ayaEnd?: number;
  pageNo?: number;
  language: Language;
  onVerseChange?: (suraNo: number, ayaNo: number) => void;
  compact?: boolean;
  // New props for starting from a specific verse (e.g., from concepts page)
  startFromAya?: number;      // Verse number to start from
  startFromSura?: number;     // Sura number (for cross-sura page navigation)
  autoPlay?: boolean;         // Auto-play when loaded and startFromAya is set
}

type PlaybackState = 'idle' | 'loading' | 'playing' | 'paused';

/**
 * Audio Session API (WKWebView on iOS 16.4+): ask for "playback" so recitation
 * keeps playing with the ring/silent switch on. No-op elsewhere.
 */
function requestPlaybackAudioSession() {
  const nav = navigator as Navigator & { audioSession?: { type: string } };
  try {
    if (nav.audioSession && nav.audioSession.type !== 'playback') nav.audioSession.type = 'playback';
  } catch { /* not supported */ }
}

/** Every alternative source the API gave for one verse (same verse, same reciter). */
function collectFallbackUrls(verseInfo: VerseAudioInfo | undefined): string[] {
  if (!verseInfo) return [];
  const urls: string[] = [];
  if (verseInfo.fallback_url) urls.push(verseInfo.fallback_url);
  if (verseInfo.fallback_urls) urls.push(...verseInfo.fallback_urls.filter((u): u is string => !!u));
  return [...new Set(urls)].filter((u) => u !== verseInfo.url);
}

// =============================================================================
// DEFAULT RECITERS
// =============================================================================

const DEFAULT_RECITERS: ReciterInfo[] = [
  { id: 'mishary_afasy', name_ar: 'مشاري العفاسي', name_en: 'Mishary Al-Afasy', style: 'murattal' },
  { id: 'saud_shuraim', name_ar: 'سعود الشريم', name_en: 'Saud Al-Shuraim', style: 'murattal' },
  { id: 'maher_muaiqly', name_ar: 'ماهر المعيقلي', name_en: 'Maher Al-Muaiqly', style: 'murattal' },
  { id: 'abdul_basit', name_ar: 'عبد الباسط عبد الصمد', name_en: 'Abdul Basit Abdul Samad', style: 'mujawwad' },
  { id: 'husary', name_ar: 'محمود خليل الحصري', name_en: 'Mahmoud Khalil Al-Husary', style: 'murattal' },
];

// =============================================================================
// COMPONENT
// =============================================================================

export function QuranAudioPlayer({
  mode,
  suraNo,
  ayaNo,
  ayaStart,
  ayaEnd,
  pageNo,
  language,
  onVerseChange,
  compact = false,
  startFromAya,
  startFromSura,
  autoPlay = false,
}: QuranAudioPlayerProps) {
  // State
  const [reciters, setReciters] = useState<ReciterInfo[]>(DEFAULT_RECITERS);
  const {
    reciterId: selectedReciter, setReciterId: setSelectedReciter,
    playbackRate, setPlaybackRate, verseRepeat, setVerseRepeat,
  } = useReaderSettingsStore();
  const [playbackState, setPlaybackState] = useState<PlaybackState>('idle');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isRepeat, setIsRepeat] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // For verse-by-verse mode
  const [verseAudios, setVerseAudios] = useState<VerseAudioInfo[]>([]);
  const [currentVerseIndex, setCurrentVerseIndex] = useState(0);

  // Track if we should auto-play after loading (used with startFromAya)
  const [pendingAutoPlay, setPendingAutoPlay] = useState(false);

  // Audio element ref
  const audioRef = useRef<HTMLAudioElement | null>(null);
  // Plays of the current verse so far (for the per-verse repeat count)
  const playsOfVerseRef = useRef(1);
  // blob: URL of the saved copy now loaded (web), revoked when replaced
  const blobUrlRef = useRef<string | null>(null);
  // Fallback sources already tried for the verse now loaded. Reset by
  // setSource on every verse change, so a fallback is always the SAME verse
  // (and, from the API, the same reciter): never verse 1 while 1:3 is shown.
  const fallbackAttemptRef = useRef(0);
  // Whether playback was requested, so a fallback resumes only if it should.
  const wantPlayRef = useRef(false);
  // Host of the recitation file now loaded (for the attribution line). An
  // offline copy keeps the host it was downloaded from.
  const [sourceHost, setSourceHost] = useState<string | null>(null);
  const idBase = useId();

  /** Point the player at a verse, preferring its offline copy, and optionally play. */
  const setSource = useCallback(async (audio: HTMLAudioElement, url: string, sura: number, play: boolean) => {
    fallbackAttemptRef.current = 0;
    wantPlayRef.current = play;
    const src = await playableUrl(selectedReciter, sura, url);
    setSourceHost(audioHost(url));
    if (blobUrlRef.current && blobUrlRef.current !== src) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
    if (src.startsWith('blob:')) blobUrlRef.current = src;
    audio.src = src;
    if (play) {
      requestPlaybackAudioSession();
      await audio.play().catch(() => undefined);
    }
  }, [selectedReciter]);
  useEffect(() => () => {
    if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
  }, []);

  const isRTL = language === 'ar';

  // Load reciters on mount
  useEffect(() => {
    async function loadReciters() {
      try {
        const response = await audioApi.getReciters();
        if (response.data.ok) {
          setReciters(response.data.reciters);
        }
      } catch (err) {
        console.error('Failed to load reciters:', err);
      }
    }
    loadReciters();
  }, []);

  // Load audio based on mode
  const loadAudio = useCallback(async () => {
    setPlaybackState('loading');
    setError(null);

    try {
      let startSura = suraNo ?? 0;
      let verses: VerseAudioInfo[] = [];
      let startIndex = 0;

      if (mode === 'surah' && suraNo) {
        // Verse by verse, so the reader can highlight and follow each verse.
        const offline = savedSurah(selectedReciter, suraNo);
        if (offline && hasPlaylist(offline)) {
          // Saved for offline: the playlist comes from the device, no API call.
          const from = startFromAya ?? 1;
          verses = offline.ayahs
            .map((aya, i) => ({ sura_no: suraNo, aya_no: aya, reference: `${suraNo}:${aya}`, url: offline.urls[i] }))
            .filter((v) => v.aya_no >= from);
        } else {
          // 286 (the longest surah) means "to the end"; the API clamps it.
          const response = await audioApi.getRangeAudio(suraNo, startFromAya ?? 1, 286, selectedReciter);
          verses = response.data.verse_audios;
          // A surah saved before playlists were recorded: fill its playlist now.
          if (offline && (startFromAya ?? 1) === 1) {
            recordSurahVerses(selectedReciter, suraNo, verses.map((v) => ({ aya_no: v.aya_no, url: v.url })));
          }
        }
        if (startFromAya && verses[0] && onVerseChange) {
          onVerseChange(verses[0].sura_no, verses[0].aya_no);
        }
        if (autoPlay && startFromAya) setPendingAutoPlay(true);
      } else if (mode === 'verse' && suraNo && ayaNo) {
        const response = await audioApi.getVerseAudio(suraNo, ayaNo, selectedReciter);
        const data = response.data as typeof response.data & { fallback_urls?: string[] };
        verses = [{
          sura_no: suraNo,
          aya_no: ayaNo,
          reference: `${suraNo}:${ayaNo}`,
          url: data.audio_url,
          fallback_url: data.fallback_url,
          fallback_urls: data.fallback_urls,
        }];
      } else if (mode === 'range' && suraNo && ayaStart && ayaEnd) {
        const response = await audioApi.getRangeAudio(suraNo, ayaStart, ayaEnd, selectedReciter);
        verses = response.data.verse_audios;
        if (startFromAya && verses.length > 0) {
          const targetSura = startFromSura || suraNo;
          const foundIndex = verses.findIndex(v => v.aya_no === startFromAya && v.sura_no === targetSura);
          if (foundIndex >= 0) startIndex = foundIndex;
        }
        if (startIndex > 0 && verses[startIndex] && onVerseChange) {
          onVerseChange(verses[startIndex].sura_no, verses[startIndex].aya_no);
        }
        if (autoPlay && startFromAya) setPendingAutoPlay(true);
      } else if (mode === 'page' && pageNo) {
        const response = await audioApi.getPageAudio(pageNo, selectedReciter);
        verses = response.data.verse_audios;
        if (startFromAya && verses.length > 0) {
          const foundIndex = verses.findIndex(v =>
            // Match by aya number, and optionally sura number for cross-sura pages
            v.aya_no === startFromAya && (startFromSura ? v.sura_no === startFromSura : true));
          if (foundIndex >= 0) startIndex = foundIndex;
        }
        startSura = verses[startIndex]?.sura_no ?? 0;
        if (startIndex > 0 && verses[startIndex] && onVerseChange) {
          onVerseChange(verses[startIndex].sura_no, verses[startIndex].aya_no);
        }
        if (autoPlay && startFromAya) setPendingAutoPlay(true);
      }

      setVerseAudios(verses);
      setCurrentVerseIndex(startIndex);
      const audioUrl = verses[startIndex]?.url ?? '';

      playsOfVerseRef.current = 1;
      if (audioUrl && audioRef.current) {
        await setSource(audioRef.current, audioUrl, startSura, false);
        audioRef.current.load();
        setPlaybackState('paused');
      } else {
        setPlaybackState('idle');
      }
    } catch (err) {
      console.error('Failed to load audio:', err);
      const offlineNow = typeof navigator !== 'undefined' && navigator.onLine === false;
      setError(offlineNow
        ? (language === 'ar'
          ? 'لا يوجد اتصال. احفظ السورة للاستماع دون اتصال حين تكون متصلاً.'
          : 'You are offline. Save the surah for offline listening while connected.')
        : (language === 'ar' ? 'فشل تحميل الصوت' : 'Failed to load audio'));
      setPlaybackState('idle');
    }
  }, [mode, suraNo, ayaNo, ayaStart, ayaEnd, pageNo, selectedReciter, language, startFromAya, startFromSura, autoPlay, onVerseChange, setSource]);

  // Load audio when mode/params change
  useEffect(() => {
    loadAudio();
  }, [loadAudio]);

  // Handle auto-play when audio is loaded with startFromAya
  useEffect(() => {
    if (pendingAutoPlay && playbackState === 'paused' && audioRef.current) {
      setPendingAutoPlay(false);
      audioRef.current.play().catch(err => {
        console.warn('Auto-play failed (may require user interaction):', err);
      });
    }
  }, [pendingAutoPlay, playbackState]);

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);
    const handleEnded = () => {
      if (playsOfVerseRef.current < verseRepeat) {
        // Same verse again (memorisation repeat)
        playsOfVerseRef.current += 1;
        audio.currentTime = 0;
        audio.play();
        return;
      }
      playsOfVerseRef.current = 1;
      if (verseAudios.length > 1 && currentVerseIndex < verseAudios.length - 1) {
        // Play next verse
        const nextIndex = currentVerseIndex + 1;
        const next = verseAudios[nextIndex];
        setCurrentVerseIndex(nextIndex);
        void setSource(audio, next.url, next.sura_no, true);
        onVerseChange?.(next.sura_no, next.aya_no);
      } else if (isRepeat) {
        // Repeat from beginning
        if (verseAudios.length > 1) {
          const first = verseAudios[0];
          setCurrentVerseIndex(0);
          void setSource(audio, first.url, first.sura_no, true);
          onVerseChange?.(first.sura_no, first.aya_no);
        } else {
          audio.currentTime = 0;
          audio.play();
        }
      } else {
        setPlaybackState('paused');
      }
    };
    const handlePlay = () => {
      setPlaybackState('playing');
      // Highlight the verse as soon as playback starts, not only on advance.
      const verse = verseAudios[currentVerseIndex];
      if (verse) onVerseChange?.(verse.sura_no, verse.aya_no);
    };
    const handlePause = () => setPlaybackState('paused');
    const handleError = () => {
      // An empty src (cleared on unmount/reload) is not a playback failure.
      if (!audio.getAttribute('src')) return;
      // Alternatives for THIS verse only (same reciter, from the API).
      const fallbacks = collectFallbackUrls(verseAudios[currentVerseIndex]);
      const attempt = fallbackAttemptRef.current;
      if (attempt < fallbacks.length) {
        fallbackAttemptRef.current = attempt + 1;
        audio.src = fallbacks[attempt];
        setSourceHost(audioHost(fallbacks[attempt]));
        audio.load();
        if (wantPlayRef.current) {
          // If this fallback also fails, the error handler runs again.
          audio.play().catch(() => undefined);
        }
        return;
      }
      // All sources for this verse failed: say so, never play another verse.
      setError(language === 'ar' ? 'خطأ في تشغيل الصوت - يرجى المحاولة مرة أخرى' : 'Audio playback error - please try again');
      setPlaybackState('idle');
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('error', handleError);
    };
  }, [verseAudios, currentVerseIndex, isRepeat, verseRepeat, language, onVerseChange, setSource]);

  // Update volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  // Update playback rate. defaultPlaybackRate survives the src change on each
  // new verse; playbackRate alone would reset to 1x at every verse.
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.defaultPlaybackRate = playbackRate;
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  // Warm the browser cache with the next verse so verse changes have no gap.
  useEffect(() => {
    const next = verseAudios[currentVerseIndex + 1];
    if (!next) return;
    // A saved verse plays from the device; preloading would hit the network.
    if (isSavedVerse(selectedReciter, next.sura_no, next.url)) return;
    const preload = new Audio();
    preload.preload = 'auto';
    preload.src = next.url;
    return () => {
      preload.src = '';
    };
  }, [verseAudios, currentVerseIndex, selectedReciter]);

  // Control functions
  const togglePlay = () => {
    if (!audioRef.current) return;
    if (playbackState === 'playing') {
      wantPlayRef.current = false;
      audioRef.current.pause();
    } else {
      wantPlayRef.current = true;
      requestPlaybackAudioSession();
      audioRef.current.play().catch(() => undefined);
    }
  };

  const skipPrevious = () => {
    if (!audioRef.current) return;
    if (verseAudios.length > 1 && currentVerseIndex > 0) {
      const prevIndex = currentVerseIndex - 1;
      const prev = verseAudios[prevIndex];
      setCurrentVerseIndex(prevIndex);
      void setSource(audioRef.current, prev.url, prev.sura_no, true);
      onVerseChange?.(prev.sura_no, prev.aya_no);
    } else {
      audioRef.current.currentTime = 0;
    }
  };

  const skipNext = () => {
    if (!audioRef.current) return;
    if (verseAudios.length > 1 && currentVerseIndex < verseAudios.length - 1) {
      const nextIndex = currentVerseIndex + 1;
      const next = verseAudios[nextIndex];
      setCurrentVerseIndex(nextIndex);
      void setSource(audioRef.current, next.url, next.sura_no, true);
      onVerseChange?.(next.sura_no, next.aya_no);
    }
  };

  // Lock-screen and media-key controls (Android Chrome/WebView, iOS 15+, desktop).
  const currentReciter = reciters.find((r) => r.id === selectedReciter);
  const playingVerse = verseAudios[currentVerseIndex];
  useEffect(() => {
    if (!('mediaSession' in navigator) || !playingVerse) return;
    navigator.mediaSession.metadata = new MediaMetadata({
      title: `${language === 'ar' ? 'القرآن الكريم' : 'Quran'} ${playingVerse.reference}`,
      artist: currentReciter ? (language === 'ar' ? currentReciter.name_ar : currentReciter.name_en) : '',
      album: language === 'ar' ? 'تدبر' : 'Tadabbur',
    });
  }, [playingVerse, currentReciter, language]);

  const controlsRef = useRef({ togglePlay, skipNext, skipPrevious });
  controlsRef.current = { togglePlay, skipNext, skipPrevious };
  useEffect(() => {
    if (!('mediaSession' in navigator)) return;
    const session = navigator.mediaSession;
    const handlers: [MediaSessionAction, MediaSessionActionHandler][] = [
      ['play', () => audioRef.current?.play()],
      ['pause', () => audioRef.current?.pause()],
      ['nexttrack', () => controlsRef.current.skipNext()],
      ['previoustrack', () => controlsRef.current.skipPrevious()],
    ];
    for (const [action, handler] of handlers) {
      try { session.setActionHandler(action, handler); } catch { /* action unsupported on this platform */ }
    }
    return () => {
      for (const [action] of handlers) {
        try { session.setActionHandler(action, null); } catch { /* action unsupported on this platform */ }
      }
    };
  }, []);

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return;
    const newTime = parseFloat(e.target.value);
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  // ── Offline: save the whole surah for this reciter ──
  const canSaveOffline = offlineAudioSupported && mode === 'surah' && !!suraNo;
  const [saved, setSaved] = useState(() => (suraNo ? savedSurah(selectedReciter, suraNo) : null));
  const [saveProgress, setSaveProgress] = useState<{ done: number; total: number } | null>(null);
  const [saveError, setSaveError] = useState(false);
  const saveAbort = useRef<AbortController | null>(null);
  useEffect(() => {
    setSaved(suraNo ? savedSurah(selectedReciter, suraNo) : null);
    setSaveError(false);
    return () => saveAbort.current?.abort();
  }, [selectedReciter, suraNo]);

  const handleSaveOffline = async () => {
    if (!suraNo || saveProgress) return;
    const controller = new AbortController();
    saveAbort.current = controller;
    setSaveError(false);
    try {
      const verses = (await audioApi.getRangeAudio(suraNo, 1, 286, selectedReciter)).data.verse_audios
        .map((v) => ({ aya_no: v.aya_no, url: v.url }));
      setSaveProgress({ done: 0, total: verses.length });
      const entry = await saveSurah(selectedReciter, suraNo, verses,
        (done, total) => setSaveProgress({ done, total }), controller.signal);
      setSaved(entry);
    } catch {
      if (!controller.signal.aborted) setSaveError(true);
    } finally {
      setSaveProgress(null);
    }
  };

  // Uses only the local index: works offline and leaves nothing behind.
  const handleRemoveOffline = async () => {
    if (!suraNo) return;
    try {
      await removeSurah(selectedReciter, suraNo);
    } finally {
      setSaved(null);
    }
  };

  // Format time
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get current verse info
  const currentVerse = verseAudios[currentVerseIndex];

  return (
    <div
      className={clsx(
        'quran-audio-player',
        compact && 'compact',
        isRTL && 'rtl'
      )}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      {/* Hidden audio element */}
      <audio ref={audioRef} preload="metadata" />

      {/* Main Controls */}
      <div className="player-controls">
        {/* Reciter Selector */}
        {!compact && (
          <div className="reciter-selector">
            <select
              value={selectedReciter}
              onChange={(e) => setSelectedReciter(e.target.value)}
              className="reciter-select"
              aria-label={language === 'ar' ? 'القارئ' : 'Reciter'}
            >
              {reciters.map((r) => (
                <option key={r.id} value={r.id}>
                  {language === 'ar' ? r.name_ar : r.name_en}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Playback Controls */}
        <div className="playback-controls">
          <button
            onClick={skipPrevious}
            aria-label={language === 'ar' ? 'الآية السابقة' : 'Previous verse'}
            className="control-btn"
            disabled={playbackState === 'loading'}
          >
            <SkipBack className="w-5 h-5" />
          </button>

          <button
            onClick={togglePlay}
            aria-label={playbackState === 'playing'
              ? (language === 'ar' ? 'إيقاف مؤقت' : 'Pause')
              : (language === 'ar' ? 'تشغيل' : 'Play')}
            className="control-btn play-btn"
            disabled={playbackState === 'loading' || playbackState === 'idle'}
          >
            {playbackState === 'loading' ? (
              <div className="loading-spinner" />
            ) : playbackState === 'playing' ? (
              <Pause className="w-6 h-6" />
            ) : (
              <Play className="w-6 h-6" />
            )}
          </button>

          <button
            onClick={skipNext}
            aria-label={language === 'ar' ? 'الآية التالية' : 'Next verse'}
            className="control-btn"
            disabled={playbackState === 'loading' || (verseAudios.length > 0 && currentVerseIndex >= verseAudios.length - 1)}
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="progress-section">
          <span className="time-label">{formatTime(currentTime)}</span>
          <input
            aria-label={language === 'ar' ? 'موضع التشغيل' : 'Playback position'}
            type="range"
            min="0"
            max={duration || 0}
            value={currentTime}
            onChange={handleSeek}
            className="progress-bar"
          />
          <span className="time-label">{formatTime(duration)}</span>
        </div>

        {/* Secondary Controls */}
        <div className="secondary-controls">
          {/* Volume */}
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="control-btn"
          >
            {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
          </button>

          {!compact && (
            <input
              aria-label={language === 'ar' ? 'مستوى الصوت' : 'Volume'}
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={isMuted ? 0 : volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="volume-slider"
            />
          )}

          {/* Repeat */}
          <button
            onClick={() => setIsRepeat(!isRepeat)}
            aria-pressed={isRepeat}
            aria-label={language === 'ar' ? 'تكرار المقطع' : 'Repeat all'}
            className={clsx('control-btn', isRepeat && 'active')}
          >
            <Repeat className="w-5 h-5" />
          </button>

          {/* Settings */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="control-btn"
          >
            <Settings className="w-5 h-5" />
          </button>

          {/* Save for offline (surah mode) */}
          {canSaveOffline && (
            <button
              onClick={saved ? handleRemoveOffline : handleSaveOffline}
              className={clsx('control-btn', saved && 'active')}
              disabled={!!saveProgress}
              aria-label={saved
                ? (language === 'ar' ? 'حذف النسخة المحفوظة' : 'Remove offline copy')
                : (language === 'ar' ? 'حفظ السورة للاستماع دون اتصال' : 'Save surah for offline listening')}
              title={saved
                ? (language === 'ar' ? 'محفوظة للاستماع دون اتصال — اضغط للحذف' : 'Saved for offline — tap to remove')
                : (language === 'ar' ? 'حفظ السورة للاستماع دون اتصال' : 'Save surah for offline listening')}
            >
              {saved ? <CheckCircle2 className="w-5 h-5" /> : <Download className="w-5 h-5" />}
            </button>
          )}
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel">
          <div className="setting-row">
            <label htmlFor={`${idBase}-rate`}>{language === 'ar' ? 'سرعة التشغيل' : 'Playback Speed'}</label>
            <select
              id={`${idBase}-rate`}
              value={playbackRate}
              onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
            >
              {PLAYBACK_RATES.map((rate) => (
                <option key={rate} value={rate}>{rate}x</option>
              ))}
            </select>
          </div>

          <div className="setting-row">
            <label htmlFor={`${idBase}-repeat`}>{language === 'ar' ? 'تكرار كل آية' : 'Repeat each verse'}</label>
            <select
              id={`${idBase}-repeat`}
              value={verseRepeat}
              onChange={(e) => setVerseRepeat(parseInt(e.target.value, 10))}
            >
              {VERSE_REPEATS.map((n) => (
                <option key={n} value={n}>
                  {n === 1 ? (language === 'ar' ? 'مرة واحدة' : 'Once') : `×${n}`}
                </option>
              ))}
            </select>
          </div>

          {compact && (
            <div className="setting-row">
              <label htmlFor={`${idBase}-reciter`}>{language === 'ar' ? 'القارئ' : 'Reciter'}</label>
              <select
                id={`${idBase}-reciter`}
                value={selectedReciter}
                onChange={(e) => setSelectedReciter(e.target.value)}
              >
                {reciters.map((r) => (
                  <option key={r.id} value={r.id}>
                    {language === 'ar' ? r.name_ar : r.name_en}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Current Verse Info */}
      {currentVerse && verseAudios.length > 1 && (
        <div className="verse-info">
          <span className="verse-counter">
            {language === 'ar'
              ? `الآية ${currentVerseIndex + 1} من ${verseAudios.length}`
              : `Verse ${currentVerseIndex + 1} of ${verseAudios.length}`}
          </span>
          <span className="verse-reference">{currentVerse.reference}</span>
        </div>
      )}

      {/* Offline save status */}
      {canSaveOffline && (saveProgress || saveError || saved) && (
        <div className="offline-status" role="status">
          {saveProgress ? (
            <>
              <span>
                {language === 'ar'
                  ? `جارٍ الحفظ للاستماع دون اتصال: ${saveProgress.done} من ${saveProgress.total}`
                  : `Saving for offline: ${saveProgress.done} of ${saveProgress.total}`}
              </span>
              <progress value={saveProgress.done} max={saveProgress.total} />
              <button onClick={() => saveAbort.current?.abort()}>
                {language === 'ar' ? 'إلغاء' : 'Cancel'}
              </button>
            </>
          ) : saveError ? (
            <span className="offline-error">
              {language === 'ar' ? 'تعذّر حفظ السورة. تحقق من الاتصال وحاول مجددًا.' : 'Could not save the surah. Check your connection and try again.'}
            </span>
          ) : saved ? (
            <span>
              <CheckCircle2 className="w-4 h-4 inline-block align-text-bottom" />{' '}
              {language === 'ar'
                ? `محفوظة للاستماع دون اتصال (${saved.verses} آية${saved.bytes ? `، ${(saved.bytes / 1048576).toFixed(1)} م.ب` : ''})`
                : `Saved for offline (${saved.verses} verses${saved.bytes ? `, ${(saved.bytes / 1048576).toFixed(1)} MB` : ''})`}
              <button onClick={handleRemoveOffline} aria-label={language === 'ar' ? 'حذف' : 'Remove'}>
                <Trash2 className="w-4 h-4" />
              </button>
            </span>
          ) : null}
        </div>
      )}

      {/* Starting from highlighted verse indicator */}
      {startFromAya && verseAudios.length > 0 && currentVerseIndex === 0 && playbackState !== 'playing' && (
        <div className="start-from-indicator">
          {language === 'ar'
            ? `سيبدأ التشغيل من الآية ${startFromAya}`
            : `Starting from verse ${startFromAya}`}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-message">
          {error}
          <button onClick={loadAudio}>
            {language === 'ar' ? 'إعادة المحاولة' : 'Retry'}
          </button>
        </div>
      )}

      {/* Recitation audio source (attribution) */}
      <AudioSourceAttribution host={sourceHost} language={language} className="mt-2" />

      {/* Styles */}
      <style>{`
        .quran-audio-player {
          background: #f8fafc;
          border-radius: 12px;
          padding: 1rem;
          border: 1px solid #e2e8f0;
        }

        .quran-audio-player.compact {
          padding: 0.5rem;
        }

        .player-controls {
          display: flex;
          align-items: center;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .reciter-selector {
          min-width: 150px;
        }

        .reciter-select {
          width: 100%;
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          font-size: 0.875rem;
          background: white;
        }

        .playback-controls {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .control-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          border: none;
          background: white;
          border-radius: 50%;
          cursor: pointer;
          transition: all 0.2s;
          color: #374151;
        }

        .control-btn:hover:not(:disabled) {
          background: #e2e8f0;
        }

        .control-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .control-btn.active {
          background: #3b82f6;
          color: white;
        }

        .play-btn {
          width: 48px;
          height: 48px;
          background: #3b82f6;
          color: white;
        }

        .play-btn:hover:not(:disabled) {
          background: #2563eb;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid white;
          border-top-color: transparent;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .progress-section {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          min-width: 200px;
        }

        .time-label {
          font-size: 0.75rem;
          color: #6b7280;
          font-variant-numeric: tabular-nums;
          min-width: 40px;
        }

        .progress-bar {
          flex: 1;
          height: 4px;
          -webkit-appearance: none;
          background: #e2e8f0;
          border-radius: 2px;
          cursor: pointer;
        }

        .progress-bar::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 12px;
          height: 12px;
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
        }

        .secondary-controls {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .volume-slider {
          width: 80px;
          height: 4px;
          -webkit-appearance: none;
          background: #e2e8f0;
          border-radius: 2px;
          cursor: pointer;
        }

        .volume-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 10px;
          height: 10px;
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
        }

        .settings-panel {
          margin-top: 1rem;
          padding: 1rem;
          background: white;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
        }

        .setting-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.5rem 0;
        }

        .setting-row label {
          font-size: 0.875rem;
          color: #374151;
        }

        .setting-row select {
          padding: 0.375rem 0.75rem;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          font-size: 0.875rem;
        }

        .verse-info {
          margin-top: 0.75rem;
          display: flex;
          justify-content: center;
          gap: 1rem;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .verse-reference {
          font-weight: 600;
          color: #3b82f6;
        }

        .error-message {
          margin-top: 0.75rem;
          padding: 0.5rem 1rem;
          background: #fef2f2;
          color: #991b1b;
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 0.875rem;
        }

        .error-message button {
          padding: 0.25rem 0.75rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 4px;
          cursor: pointer;
        }

        .offline-status {
          margin-top: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex-wrap: wrap;
          font-size: 0.8125rem;
          color: #047857;
        }
        .offline-status progress { flex: 1; min-width: 120px; height: 6px; accent-color: #059669; }
        .offline-status button {
          padding: 0.125rem 0.5rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 4px;
          cursor: pointer;
          color: #374151;
        }
        .offline-status .offline-error { color: #991b1b; }

        .start-from-indicator {
          margin-top: 0.75rem;
          padding: 0.5rem 1rem;
          background: #ecfdf5;
          color: #047857;
          border-radius: 6px;
          font-size: 0.875rem;
          text-align: center;
          border: 1px solid #a7f3d0;
        }

        /* RTL adjustments */
        .rtl .progress-section {
          flex-direction: row-reverse;
        }

        /* Compact mode */
        .compact .player-controls {
          gap: 0.5rem;
        }

        .compact .progress-section {
          min-width: 120px;
        }

        .compact .control-btn {
          width: 32px;
          height: 32px;
        }

        .compact .play-btn {
          width: 40px;
          height: 40px;
        }
      `}</style>
    </div>
  );
}

export default QuranAudioPlayer;
