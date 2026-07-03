import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Pause, SkipBack, SkipForward, Loader2 } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import type { AsmaNameSummary } from '../../lib/api';

/**
 * AsmaAudioPlayer — plays the canonical Quranic verse for each of the 99
 * Names of Allah, using the Quran.com per-ayah CDN (Mishary Rashid Alafasy).
 *
 * URL pattern: https://verses.quran.com/Alafasy/mp3/{SSS}{AAA}.mp3
 * Reciter attribution is rendered in the player chrome (required by license).
 *
 * No Quran text is rendered here — only the surah/ayah reference label
 * underneath the currently-playing Name.
 */

const CDN_BASE = 'https://verses.quran.com/Alafasy/mp3';
const RECITER_NAME_EN = 'Mishary Rashid Alafasy';
const RECITER_NAME_AR = 'مشاري راشد العفاسي';

function pad(n: number, width: number): string {
  return n.toString().padStart(width, '0');
}

export function asmaAudioUrl(surah: number, ayah: number): string {
  return `${CDN_BASE}/${pad(surah, 3)}${pad(ayah, 3)}.mp3`;
}

interface PlaylistEntry {
  nameId: string;
  arabicName: string;
  transliteration: string;
  englishName?: string;
  surahNumber: number;
  ayahNumber: number;
  url: string;
}

function buildPlaylist(names: AsmaNameSummary[]): PlaylistEntry[] {
  const out: PlaylistEntry[] = [];
  for (const n of names) {
    const ref = n.primaryQuranicReferences?.[0];
    if (!ref) continue;
    out.push({
      nameId: n.nameId,
      arabicName: n.arabicName,
      transliteration: n.transliteration,
      englishName: n.englishName,
      surahNumber: ref.surahNumber,
      ayahNumber: ref.ayahStart,
      url: asmaAudioUrl(ref.surahNumber, ref.ayahStart),
    });
  }
  return out;
}

interface AsmaAudioPlayerProps {
  names: AsmaNameSummary[];
}

export function AsmaAudioPlayer({ names }: AsmaAudioPlayerProps) {
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playlist = useMemo(() => buildPlaylist(names), [names]);

  const [index, setIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const current = playlist[index];

  useEffect(() => {
    setIndex(0);
  }, [playlist.length]);

  const playAt = useCallback(
    (i: number) => {
      if (i < 0 || i >= playlist.length) return;
      setIndex(i);
      setError(null);
      const a = audioRef.current;
      if (!a) return;
      a.src = playlist[i].url;
      a.play().catch((e) => setError(e?.message || 'Audio playback failed'));
    },
    [playlist]
  );

  const onTogglePlay = useCallback(() => {
    const a = audioRef.current;
    if (!a) return;
    if (!a.src && current) a.src = current.url;
    if (a.paused) {
      a.play().catch((e) => setError(e?.message || 'Audio playback failed'));
    } else {
      a.pause();
    }
  }, [current]);

  const onPrev = useCallback(() => playAt(Math.max(0, index - 1)), [playAt, index]);
  const onNext = useCallback(
    () => playAt(Math.min(playlist.length - 1, index + 1)),
    [playAt, index, playlist.length]
  );

  // Keep <audio> listeners in sync with React state.
  useEffect(() => {
    const a = audioRef.current;
    if (!a) return;
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onWaiting = () => setLoading(true);
    const onPlaying = () => setLoading(false);
    const onCanPlay = () => setLoading(false);
    const onEnded = () => {
      if (index < playlist.length - 1) playAt(index + 1);
      else setIsPlaying(false);
    };
    const onErrorEvt = () => {
      setLoading(false);
      setError('Could not load audio for this verse.');
    };
    a.addEventListener('play', onPlay);
    a.addEventListener('pause', onPause);
    a.addEventListener('waiting', onWaiting);
    a.addEventListener('playing', onPlaying);
    a.addEventListener('canplay', onCanPlay);
    a.addEventListener('ended', onEnded);
    a.addEventListener('error', onErrorEvt);
    return () => {
      a.removeEventListener('play', onPlay);
      a.removeEventListener('pause', onPause);
      a.removeEventListener('waiting', onWaiting);
      a.removeEventListener('playing', onPlaying);
      a.removeEventListener('canplay', onCanPlay);
      a.removeEventListener('ended', onEnded);
      a.removeEventListener('error', onErrorEvt);
    };
  }, [index, playlist.length, playAt]);

  if (playlist.length === 0) return null;

  return (
    <section
      aria-label={language === 'ar' ? 'استماع لأسماء الله الحسنى' : 'Listen to the 99 Names of Allah'}
      className="mb-6 p-4 sm:p-5 bg-white border border-emerald-200 rounded-lg shadow-sm"
      dir={dir}
    >
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2
              className={`text-base font-semibold text-emerald-800 ${
                language === 'ar' ? 'font-arabic' : ''
              }`}
            >
              {language === 'ar'
                ? 'استماع للآيات الجامعة لأسماء الله الحسنى'
                : 'Listen — verses of the 99 Names'}
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {language === 'ar'
                ? `القارئ: ${RECITER_NAME_AR} · بثّ من Quran.com`
                : `Reciter: ${RECITER_NAME_EN} · streamed from Quran.com`}
            </p>
          </div>
          <span className="text-xs text-gray-500 tabular-nums" dir="ltr">
            {index + 1} / {playlist.length}
          </span>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={onPrev}
            disabled={index === 0}
            className="p-2 rounded-full text-gray-700 hover:bg-emerald-50 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label={language === 'ar' ? 'الاسم السابق' : 'Previous Name'}
          >
            <SkipBack className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={onTogglePlay}
            className="p-3 rounded-full bg-emerald-600 text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            aria-label={isPlaying ? (language === 'ar' ? 'إيقاف' : 'Pause') : language === 'ar' ? 'تشغيل' : 'Play'}
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5" />
            )}
          </button>
          <button
            type="button"
            onClick={onNext}
            disabled={index >= playlist.length - 1}
            className="p-2 rounded-full text-gray-700 hover:bg-emerald-50 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label={language === 'ar' ? 'الاسم التالي' : 'Next Name'}
          >
            <SkipForward className="w-5 h-5" />
          </button>

          {current && (
            <div className="flex-1 min-w-0">
              <p className="font-arabic text-xl text-gray-900 truncate" dir="rtl" lang="ar">
                {current.arabicName}
              </p>
              <p className="text-xs text-gray-600 truncate" dir="ltr" lang="en">
                {current.transliteration}
                {current.englishName ? ` · ${current.englishName}` : ''}
                {' · '}
                <span className="tabular-nums">
                  {current.surahNumber}:{current.ayahNumber}
                </span>
              </p>
            </div>
          )}
        </div>

        {current && (
          <Link
            to={`/quran/${current.surahNumber}?aya=${current.ayahNumber}`}
            className="inline-flex items-center gap-1 text-xs text-emerald-700 hover:text-emerald-900 hover:underline"
          >
            {language === 'ar'
              ? `اقرأ الآية في المصحف · ${current.surahNumber}:${current.ayahNumber}`
              : `Read the verse in the mushaf · ${current.surahNumber}:${current.ayahNumber}`}
          </Link>
        )}

        {error && (
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
            {language === 'ar'
              ? 'تعذّر تحميل الصوت لهذه الآية. يرجى المحاولة لاحقاً.'
              : error}
          </p>
        )}

        <audio ref={audioRef} preload="none" />
      </div>
    </section>
  );
}
