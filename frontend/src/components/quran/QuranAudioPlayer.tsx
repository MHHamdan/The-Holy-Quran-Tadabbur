/**
 * Quran Audio Player Component
 *
 * A comprehensive audio player for Quran recitation with:
 * - Multiple reciter selection
 * - Verse-by-verse or continuous playback
 * - Progress tracking
 * - Speed control
 * - Download option
 *
 * Arabic: مشغل صوت القرآن الكريم
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Download, Repeat, Settings } from 'lucide-react';
import { audioApi, ReciterInfo, VerseAudioInfo } from '../../lib/api';
import { Language } from '../../i18n/translations';
import clsx from 'clsx';

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
  const [selectedReciter, setSelectedReciter] = useState('mishary_afasy');
  const [playbackState, setPlaybackState] = useState<PlaybackState>('idle');
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isRepeat, setIsRepeat] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // For verse-by-verse mode
  const [verseAudios, setVerseAudios] = useState<VerseAudioInfo[]>([]);
  const [currentVerseIndex, setCurrentVerseIndex] = useState(0);

  // Fallback URL tracking - supports multiple fallback URLs for high availability
  const [fallbackUrls, setFallbackUrls] = useState<string[]>([]);
  const [currentFallbackIndex, setCurrentFallbackIndex] = useState(0);

  // Track if we should auto-play after loading (used with startFromAya)
  const [pendingAutoPlay, setPendingAutoPlay] = useState(false);

  // Audio element ref
  const audioRef = useRef<HTMLAudioElement | null>(null);

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

  // Helper to collect all fallback URLs for a verse
  const collectFallbackUrls = (verseInfo: VerseAudioInfo): string[] => {
    const urls: string[] = [];
    if (verseInfo.fallback_url) urls.push(verseInfo.fallback_url);
    if (verseInfo.fallback_urls) urls.push(...verseInfo.fallback_urls.filter(u => u));
    return urls;
  };

  // Load audio based on mode
  const loadAudio = useCallback(async () => {
    setPlaybackState('loading');
    setError(null);
    setFallbackUrls([]);
    setCurrentFallbackIndex(0);

    try {
      let audioUrl = '';
      let fallbacks: string[] = [];

      if (mode === 'surah' && suraNo) {
        // For surah mode with startFromAya, use range mode instead to get verse-by-verse control
        if (startFromAya) {
          // Get total verses in sura first (estimate max as 286 for Baqara)
          // We'll use range mode to get verse-by-verse playback
          const response = await audioApi.getRangeAudio(suraNo, startFromAya, 286, selectedReciter);
          const verses = response.data.verse_audios;
          setVerseAudios(verses);

          const targetVerse = verses[0]; // First verse is the startFromAya
          audioUrl = targetVerse?.url || '';
          if (targetVerse) fallbacks = collectFallbackUrls(targetVerse);
          setFallbackUrls(fallbacks);
          setCurrentVerseIndex(0);

          // Notify about the starting verse
          if (targetVerse && onVerseChange) {
            onVerseChange(targetVerse.sura_no, targetVerse.aya_no);
          }

          // Set auto-play flag if requested
          if (autoPlay) {
            setPendingAutoPlay(true);
          }
        } else {
          const response = await audioApi.getSurahAudio(suraNo, selectedReciter);
          audioUrl = response.data.audio_url;
          setVerseAudios([]);
        }
      } else if (mode === 'verse' && suraNo && ayaNo) {
        const response = await audioApi.getVerseAudio(suraNo, ayaNo, selectedReciter);
        audioUrl = response.data.audio_url;
        // Collect all fallback URLs
        if (response.data.fallback_url) fallbacks.push(response.data.fallback_url);
        setFallbackUrls(fallbacks);
        setVerseAudios([{
          sura_no: suraNo,
          aya_no: ayaNo,
          reference: `${suraNo}:${ayaNo}`,
          url: audioUrl,
          fallback_url: response.data.fallback_url
        }]);
      } else if (mode === 'range' && suraNo && ayaStart && ayaEnd) {
        const response = await audioApi.getRangeAudio(suraNo, ayaStart, ayaEnd, selectedReciter);
        const verses = response.data.verse_audios;
        setVerseAudios(verses);

        // Find the starting verse index if startFromAya is specified
        let startIndex = 0;
        if (startFromAya && verses.length > 0) {
          const targetSura = startFromSura || suraNo;
          const foundIndex = verses.findIndex(v =>
            v.aya_no === startFromAya && v.sura_no === targetSura
          );
          if (foundIndex >= 0) {
            startIndex = foundIndex;
          }
        }

        const targetVerse = verses[startIndex];
        audioUrl = targetVerse?.url || '';
        if (targetVerse) fallbacks = collectFallbackUrls(targetVerse);
        setFallbackUrls(fallbacks);
        setCurrentVerseIndex(startIndex);

        // Notify about the starting verse
        if (startIndex > 0 && targetVerse && onVerseChange) {
          onVerseChange(targetVerse.sura_no, targetVerse.aya_no);
        }

        // Set auto-play flag if requested
        if (autoPlay && startFromAya) {
          setPendingAutoPlay(true);
        }
      } else if (mode === 'page' && pageNo) {
        const response = await audioApi.getPageAudio(pageNo, selectedReciter);
        const verses = response.data.verse_audios;
        setVerseAudios(verses);

        // Find the starting verse index if startFromAya is specified
        let startIndex = 0;
        if (startFromAya && verses.length > 0) {
          const foundIndex = verses.findIndex(v => {
            // Match by aya number, and optionally sura number for cross-sura pages
            const ayaMatch = v.aya_no === startFromAya;
            const suraMatch = startFromSura ? v.sura_no === startFromSura : true;
            return ayaMatch && suraMatch;
          });
          if (foundIndex >= 0) {
            startIndex = foundIndex;
          }
        }

        const targetVerse = verses[startIndex];
        audioUrl = targetVerse?.url || '';
        if (targetVerse) fallbacks = collectFallbackUrls(targetVerse);
        setFallbackUrls(fallbacks);
        setCurrentVerseIndex(startIndex);

        // Notify about the starting verse
        if (startIndex > 0 && targetVerse && onVerseChange) {
          onVerseChange(targetVerse.sura_no, targetVerse.aya_no);
        }

        // Set auto-play flag if requested
        if (autoPlay && startFromAya) {
          setPendingAutoPlay(true);
        }
      }

      if (audioUrl && audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.load();
        setPlaybackState('paused');
      } else {
        setPlaybackState('idle');
      }
    } catch (err) {
      console.error('Failed to load audio:', err);
      setError(language === 'ar' ? 'فشل تحميل الصوت' : 'Failed to load audio');
      setPlaybackState('idle');
    }
  }, [mode, suraNo, ayaNo, ayaStart, ayaEnd, pageNo, selectedReciter, language, startFromAya, startFromSura, autoPlay, onVerseChange]);

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
      if (verseAudios.length > 1 && currentVerseIndex < verseAudios.length - 1) {
        // Play next verse
        const nextIndex = currentVerseIndex + 1;
        setCurrentVerseIndex(nextIndex);
        audio.src = verseAudios[nextIndex].url;
        audio.play();
        onVerseChange?.(verseAudios[nextIndex].sura_no, verseAudios[nextIndex].aya_no);
      } else if (isRepeat) {
        // Repeat from beginning
        if (verseAudios.length > 1) {
          setCurrentVerseIndex(0);
          audio.src = verseAudios[0].url;
          onVerseChange?.(verseAudios[0].sura_no, verseAudios[0].aya_no);
        }
        audio.currentTime = 0;
        audio.play();
      } else {
        setPlaybackState('paused');
      }
    };
    const handlePlay = () => setPlaybackState('playing');
    const handlePause = () => setPlaybackState('paused');
    const handleError = () => {
      // Try next fallback URL if available
      if (fallbackUrls.length > 0 && currentFallbackIndex < fallbackUrls.length && audio) {
        const nextFallback = fallbackUrls[currentFallbackIndex];
        console.log(`Audio failed, trying fallback ${currentFallbackIndex + 1}/${fallbackUrls.length}:`, nextFallback);
        setCurrentFallbackIndex(prev => prev + 1);
        audio.src = nextFallback;
        audio.load();
        audio.play().catch(() => {
          // If this fallback also fails, the error handler will be called again
          console.warn('Fallback also failed:', nextFallback);
        });
        return;
      }
      // All fallbacks exhausted
      console.error('All audio sources failed');
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
  }, [verseAudios, currentVerseIndex, isRepeat, language, onVerseChange, fallbackUrls, currentFallbackIndex]);

  // Update volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  // Update playback rate
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  // Control functions
  const togglePlay = () => {
    if (!audioRef.current) return;
    if (playbackState === 'playing') {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
  };

  const skipPrevious = () => {
    if (!audioRef.current) return;
    if (verseAudios.length > 1 && currentVerseIndex > 0) {
      const prevIndex = currentVerseIndex - 1;
      setCurrentVerseIndex(prevIndex);
      audioRef.current.src = verseAudios[prevIndex].url;
      audioRef.current.play();
      onVerseChange?.(verseAudios[prevIndex].sura_no, verseAudios[prevIndex].aya_no);
    } else {
      audioRef.current.currentTime = 0;
    }
  };

  const skipNext = () => {
    if (!audioRef.current) return;
    if (verseAudios.length > 1 && currentVerseIndex < verseAudios.length - 1) {
      const nextIndex = currentVerseIndex + 1;
      setCurrentVerseIndex(nextIndex);
      audioRef.current.src = verseAudios[nextIndex].url;
      audioRef.current.play();
      onVerseChange?.(verseAudios[nextIndex].sura_no, verseAudios[nextIndex].aya_no);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return;
    const newTime = parseFloat(e.target.value);
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleDownload = () => {
    if (audioRef.current?.src) {
      window.open(audioRef.current.src, '_blank');
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
            className="control-btn"
            disabled={playbackState === 'loading'}
          >
            <SkipBack className="w-5 h-5" />
          </button>

          <button
            onClick={togglePlay}
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

          {/* Download */}
          <button
            onClick={handleDownload}
            className="control-btn"
            disabled={!audioRef.current?.src}
          >
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel">
          <div className="setting-row">
            <label>{language === 'ar' ? 'سرعة التشغيل' : 'Playback Speed'}</label>
            <select
              value={playbackRate}
              onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
            >
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1">1x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
            </select>
          </div>

          {compact && (
            <div className="setting-row">
              <label>{language === 'ar' ? 'القارئ' : 'Reciter'}</label>
              <select
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
