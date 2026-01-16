import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Video, Search, Play, Clock, User, Filter, Loader2 } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

interface VideoResult {
  id: string;
  title: string;
  description: string;
  thumbnail: string;
  channelTitle: string;
  publishedAt: string;
  duration?: string;
  viewCount?: string;
}

interface Channel {
  id: string;
  name_en: string;
  name_ar: string;
  category: string;
}

// Curated list of trusted Islamic channels
const TRUSTED_CHANNELS: Channel[] = [
  { id: 'UCIUVe6LlNxUJnLCaHd3zFPw', name_en: 'Yaqeen Institute', name_ar: 'معهد يقين', category: 'education' },
  { id: 'UC5A-P_i7LlOK2q7lp7kI8kg', name_en: 'Bayyinah Institute', name_ar: 'معهد بينة', category: 'quran' },
  { id: 'UCLkW4ZqBfuGlpq5FcYmBGwg', name_en: 'Mufti Menk', name_ar: 'مفتي منك', category: 'lecture' },
  { id: 'UCgTGPzJbiR6KqYR9KVbVqkA', name_en: 'Omar Suleiman', name_ar: 'عمر سليمان', category: 'lecture' },
  { id: 'UCfkZ1wQbJQhOYUqV7l_f99g', name_en: 'Nouman Ali Khan', name_ar: 'نعمان علي خان', category: 'quran' },
  { id: 'UCrvLt6zQN1wL2cWvR3I-6Ng', name_en: 'Islamic Guidance', name_ar: 'الهداية الإسلامية', category: 'education' },
  { id: 'UCmo8MsiqGcD6z3phTTfU0Ow', name_en: 'FreeQuranEducation', name_ar: 'تعليم القرآن المجاني', category: 'quran' },
  { id: 'UCnD0_lWkiGPpn4rKPxpIFAA', name_en: 'One Path Network', name_ar: 'شبكة طريق واحد', category: 'education' },
];

const CATEGORIES = [
  { id: 'all', name_en: 'All', name_ar: 'الكل' },
  { id: 'quran', name_en: 'Quran & Tafsir', name_ar: 'القرآن والتفسير' },
  { id: 'hadith', name_en: 'Hadith', name_ar: 'الحديث' },
  { id: 'fiqh', name_en: 'Fiqh', name_ar: 'الفقه' },
  { id: 'seerah', name_en: 'Seerah', name_ar: 'السيرة' },
  { id: 'lecture', name_en: 'Lectures', name_ar: 'محاضرات' },
  { id: 'education', name_en: 'Education', name_ar: 'تعليمي' },
];

const DURATION_FILTERS = [
  { id: 'any', name_en: 'Any Duration', name_ar: 'أي مدة' },
  { id: 'short', name_en: 'Under 10 min', name_ar: 'أقل من 10 دقائق' },
  { id: 'medium', name_en: '10-30 min', name_ar: '10-30 دقيقة' },
  { id: 'long', name_en: 'Over 30 min', name_ar: 'أكثر من 30 دقيقة' },
];

// Sample videos for demonstration (in production, use YouTube API)
const SAMPLE_VIDEOS: VideoResult[] = [
  {
    id: 'sample1',
    title: 'Understanding Surah Al-Fatiha - Deep Analysis',
    description: 'A comprehensive analysis of the opening chapter of the Quran',
    thumbnail: 'https://i.ytimg.com/vi/sample1/hqdefault.jpg',
    channelTitle: 'Bayyinah Institute',
    publishedAt: '2024-01-15',
    duration: '45:32',
    viewCount: '1.2M',
  },
  {
    id: 'sample2',
    title: 'The Story of Prophet Yusuf - Full Series',
    description: 'Learn about the beautiful story of Prophet Yusuf from the Quran',
    thumbnail: 'https://i.ytimg.com/vi/sample2/hqdefault.jpg',
    channelTitle: 'Yaqeen Institute',
    publishedAt: '2024-01-10',
    duration: '1:23:45',
    viewCount: '850K',
  },
  {
    id: 'sample3',
    title: 'How to Have Khushoo in Salah',
    description: 'Practical tips to increase focus and concentration in prayer',
    thumbnail: 'https://i.ytimg.com/vi/sample3/hqdefault.jpg',
    channelTitle: 'Mufti Menk',
    publishedAt: '2024-01-05',
    duration: '18:20',
    viewCount: '2.1M',
  },
];

export function IslamicVideosPage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [searchQuery, setSearchQuery] = useState('');
  const [videos, setVideos] = useState<VideoResult[]>(SAMPLE_VIDEOS);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDuration, setSelectedDuration] = useState('any');
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null);

  // In production, this would call YouTube API
  const searchVideos = useCallback(async () => {
    if (!searchQuery.trim()) {
      setVideos(SAMPLE_VIDEOS);
      return;
    }

    setLoading(true);
    try {
      // Simulated API call - in production use YouTube Data API v3
      await new Promise(resolve => setTimeout(resolve, 500));

      // Filter sample videos based on search
      const filtered = SAMPLE_VIDEOS.filter(v =>
        v.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        v.description.toLowerCase().includes(searchQuery.toLowerCase())
      );

      setVideos(filtered.length > 0 ? filtered : SAMPLE_VIDEOS);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  // Search on Enter key
  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      searchVideos();
    }
  }

  function openVideo(videoId: string) {
    window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString(isArabic ? 'ar-SA' : 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-red-100 rounded-lg">
            <Video className="w-8 h-8 text-red-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isArabic ? 'الفيديوهات الإسلامية' : 'Islamic Videos'}
            </h1>
            <p className="text-gray-600">
              {isArabic
                ? 'محاضرات وفيديوهات تعليمية من علماء موثقين'
                : 'Lectures and educational videos from trusted scholars'}
            </p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className={clsx(
            'absolute top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400',
            isArabic ? 'right-3' : 'left-3'
          )} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isArabic ? 'ابحث عن محاضرات إسلامية...' : 'Search for Islamic lectures...'}
            className={clsx(
              'w-full py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500',
              isArabic ? 'pr-10 pl-4' : 'pl-10 pr-4'
            )}
          />
          <button
            onClick={searchVideos}
            disabled={loading}
            className={clsx(
              'absolute top-1/2 transform -translate-y-1/2 px-4 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50',
              isArabic ? 'left-2' : 'right-2'
            )}
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : (isArabic ? 'بحث' : 'Search')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-4">
        {/* Category Filters */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                selectedCategory === cat.id
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {isArabic ? cat.name_ar : cat.name_en}
            </button>
          ))}
        </div>

        {/* Duration Filter */}
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={selectedDuration}
            onChange={(e) => setSelectedDuration(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-red-500"
          >
            {DURATION_FILTERS.map((dur) => (
              <option key={dur.id} value={dur.id}>
                {isArabic ? dur.name_ar : dur.name_en}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Trusted Channels */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          {isArabic ? 'قنوات موثقة' : 'Trusted Channels'}
        </h3>
        <div className="flex flex-wrap gap-2">
          {TRUSTED_CHANNELS.map((channel) => (
            <button
              key={channel.id}
              onClick={() => setSelectedChannel(selectedChannel === channel.id ? null : channel.id)}
              className={clsx(
                'px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2',
                selectedChannel === channel.id
                  ? 'bg-red-100 text-red-700 border border-red-200'
                  : 'bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100'
              )}
            >
              <User className="w-4 h-4" />
              {isArabic ? channel.name_ar : channel.name_en}
            </button>
          ))}
        </div>
      </div>

      {/* Video Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-red-600" />
          </div>
        ) : videos.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            {isArabic ? 'لا توجد نتائج' : 'No results found'}
          </div>
        ) : (
          videos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              language={language}
              onPlay={() => openVideo(video.id)}
              formatDate={formatDate}
            />
          ))
        )}
      </div>

      {/* API Notice */}
      <div className="mt-8 p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
        <p>
          {isArabic
            ? 'ملاحظة: هذه نسخة تجريبية. في الإصدار الكامل، سيتم عرض محتوى مباشر من يوتيوب من القنوات الإسلامية الموثقة.'
            : 'Note: This is a demo version. In the full release, live content from trusted Islamic YouTube channels will be displayed.'}
        </p>
      </div>
    </div>
  );
}

// Video Card Component
interface VideoCardProps {
  video: VideoResult;
  language: 'ar' | 'en';
  onPlay: () => void;
  formatDate: (dateStr: string) => string;
}

function VideoCard({ video, language, onPlay, formatDate }: VideoCardProps) {
  const isArabic = language === 'ar';

  return (
    <div
      className="card border border-gray-200 hover:border-red-300 transition-colors cursor-pointer group overflow-hidden"
      onClick={onPlay}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-200 -mx-6 -mt-6 mb-4">
        <div className="absolute inset-0 bg-gray-300 flex items-center justify-center">
          <Video className="w-12 h-12 text-gray-400" />
        </div>
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center">
            <Play className="w-8 h-8 text-white ml-1" />
          </div>
        </div>
        {video.duration && (
          <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-0.5 rounded">
            {video.duration}
          </div>
        )}
      </div>

      {/* Content */}
      <div>
        <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2 group-hover:text-red-600 transition-colors">
          {video.title}
        </h3>
        <p className="text-sm text-gray-500 line-clamp-2 mb-3">
          {video.description}
        </p>
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <User className="w-3 h-3" />
            {video.channelTitle}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDate(video.publishedAt)}
          </span>
        </div>
        {video.viewCount && (
          <p className="text-xs text-gray-400 mt-1">
            {video.viewCount} {isArabic ? 'مشاهدة' : 'views'}
          </p>
        )}
      </div>
    </div>
  );
}
