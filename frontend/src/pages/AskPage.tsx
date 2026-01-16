import { useState, useEffect, useRef, useCallback, memo, KeyboardEvent } from 'react';
import { Send, Settings2, ChevronDown, ChevronUp, Search, Sparkles, MessageCircle, Trash2, Users, Heart, Star, Lightbulb, BookOpen } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { ragApi, RAGResponse, TafseerSource } from '../lib/api';
import { ChatMessage, ChatMessageData } from '../components/ask';
import clsx from 'clsx';

// Session storage key
const SESSION_STORAGE_KEY = 'tadabbur_ask_session';

// Simple debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

interface Suggestion {
  text: string;
  type: string;
  concept_type?: string;
}

export function AskPage() {
  const { language } = useLanguageStore();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Tafseer source selection
  const [sources, setSources] = useState<TafseerSource[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [showSourceSelector, setShowSourceSelector] = useState(false);
  const [loadingSources, setLoadingSources] = useState(true);

  // Auto-suggestions
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const debouncedQuestion = useDebounce(question, 300);

  // Keyboard navigation for suggestions
  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        if (selectedSuggestionIndex >= 0) {
          e.preventDefault();
          handleSelectSuggestion(suggestions[selectedSuggestionIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  }, [showSuggestions, suggestions, selectedSuggestionIndex]);

  // Reset selection when suggestions change
  useEffect(() => {
    setSelectedSuggestionIndex(-1);
  }, [suggestions]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load session from localStorage on mount
  useEffect(() => {
    const savedSession = localStorage.getItem(SESSION_STORAGE_KEY);
    if (savedSession) {
      try {
        const { sessionId: savedSessionId } = JSON.parse(savedSession);
        setSessionId(savedSessionId);
      } catch {
        localStorage.removeItem(SESSION_STORAGE_KEY);
      }
    }
  }, []);

  // Save session to localStorage when it changes
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({ sessionId }));
    }
  }, [sessionId]);

  // Fetch suggestions when debounced question changes
  useEffect(() => {
    async function fetchSuggestions() {
      if (debouncedQuestion.length < 2) {
        setSuggestions([]);
        return;
      }

      setLoadingSuggestions(true);
      try {
        const result = await ragApi.getSuggestions(debouncedQuestion, language, 6);
        if (result.data.ok) {
          setSuggestions(result.data.suggestions);
        }
      } catch (err) {
        console.error('Failed to fetch suggestions:', err);
        setSuggestions([]);
      } finally {
        setLoadingSuggestions(false);
      }
    }
    fetchSuggestions();
  }, [debouncedQuestion, language]);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Select a suggestion
  const handleSelectSuggestion = useCallback((suggestion: Suggestion) => {
    setQuestion(suggestion.text);
    setShowSuggestions(false);
    inputRef.current?.focus();
  }, []);

  // Load available sources on mount
  useEffect(() => {
    async function loadSources() {
      try {
        const result = await ragApi.getSources();
        setSources(result.data.sources);
        setSelectedSources(result.data.sources.map(s => s.id));
      } catch (err) {
        console.error('Failed to load sources:', err);
      } finally {
        setLoadingSources(false);
      }
    }
    loadSources();
  }, []);

  function toggleSource(sourceId: string) {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    );
  }

  function selectAllSources() {
    setSelectedSources(sources.map(s => s.id));
  }

  function clearAllSources() {
    setSelectedSources([]);
  }

  // Clear conversation
  function clearConversation() {
    setMessages([]);
    setSessionId(null);
    localStorage.removeItem(SESSION_STORAGE_KEY);
  }

  // Handle form submission
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userQuestion = question.trim();
    setQuestion('');
    setShowSuggestions(false);

    await submitQuestion(userQuestion);
  }

  // Submit a question (initial or follow-up)
  async function submitQuestion(userQuestion: string) {
    // Add user message
    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    const userMessage: ChatMessageData = {
      id: userMessageId,
      role: 'user',
      content: userQuestion,
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessageData = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setLoading(true);

    try {
      let result;

      if (sessionId && messages.length > 0) {
        // Follow-up question
        result = await ragApi.askFollowup(sessionId, userQuestion, language);
      } else {
        // Initial question
        result = await ragApi.ask(userQuestion, language, selectedSources);
      }

      // Check for structured error response
      if (result.data && 'ok' in result.data && result.data.ok === false) {
        const errorData = result.data as unknown as {
          ok: boolean;
          error_id: string;
          message_ar: string;
          message_en: string;
        };
        const errorMessage = language === 'ar' ? errorData.message_ar : errorData.message_en;

        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, isLoading: false, error: `${errorMessage} (${errorData.error_id})` }
            : msg
        ));
        return;
      }

      const response = result.data as RAGResponse;

      // Update session ID if provided
      if (response.session_id) {
        setSessionId(response.session_id);
      }

      // Update assistant message with response
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, isLoading: false, response, content: response.answer }
          : msg
      ));

    } catch (err: unknown) {
      console.error('RAG error:', err);

      let errorMessage = language === 'ar'
        ? 'حدث خطأ أثناء معالجة السؤال. حاول مرة أخرى.'
        : 'An error occurred while processing your question. Please try again.';

      // Try to extract structured error
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { message_ar?: string; message_en?: string; error_id?: string } } };
        if (axiosError.response?.data) {
          const errorData = axiosError.response.data;
          if (errorData.message_ar || errorData.message_en) {
            errorMessage = language === 'ar'
              ? (errorData.message_ar || errorData.message_en || errorMessage)
              : (errorData.message_en || errorData.message_ar || errorMessage);
          }
        }
      }

      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, isLoading: false, error: errorMessage }
          : msg
      ));
    } finally {
      setLoading(false);
    }
  }

  // Handle follow-up suggestion click
  const handleFollowUp = useCallback((followUpQuestion: string) => {
    submitQuestion(followUpQuestion);
  }, [sessionId, messages.length, language, selectedSources]);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex-shrink-0 px-3 sm:px-6 py-3 sm:py-4 border-b border-gray-100">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <div className="p-1.5 sm:p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg sm:rounded-xl shadow-lg shadow-primary-500/25 flex-shrink-0">
              <MessageCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate">{t('ask_title', language)}</h1>
              <p className="text-xs sm:text-sm text-gray-500 truncate hidden xs:block">{t('ask_subtitle', language)}</p>
            </div>
          </div>

          {messages.length > 0 && (
            <button
              onClick={clearConversation}
              className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-2 min-h-[44px] text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
              aria-label={language === 'ar' ? 'مسح المحادثة' : 'Clear chat'}
            >
              <Trash2 className="w-4 h-4" />
              <span className="hidden sm:inline">{language === 'ar' ? 'مسح المحادثة' : 'Clear chat'}</span>
            </button>
          )}
        </div>

        {/* Tafseer Source Selector */}
        <div className="mt-3 sm:mt-4">
          <button
            onClick={() => setShowSourceSelector(!showSourceSelector)}
            className="w-full flex items-center justify-between text-left p-2.5 sm:p-3 min-h-[44px] bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <div className="flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-primary-600" />
              <span className="text-sm font-medium">
                {language === 'ar' ? 'مصادر التفسير' : 'Tafseer Sources'}
              </span>
              <span className="text-xs text-gray-500">
                ({selectedSources.length}/{sources.length})
              </span>
            </div>
            {showSourceSelector ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {showSourceSelector && (
            <div className="mt-2 p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="flex gap-2 mb-3">
                <button
                  onClick={selectAllSources}
                  className="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded hover:bg-primary-200 transition-colors"
                >
                  {language === 'ar' ? 'اختر الكل' : 'Select All'}
                </button>
                <button
                  onClick={clearAllSources}
                  className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                >
                  {language === 'ar' ? 'إلغاء الكل' : 'Clear All'}
                </button>
              </div>

              {loadingSources ? (
                <div className="flex justify-center py-4">
                  <div className="animate-spin w-5 h-5 border-2 border-primary-600 border-t-transparent rounded-full" />
                </div>
              ) : (
                <div className="grid gap-2 sm:grid-cols-2 max-h-48 overflow-y-auto">
                  {sources.map((source) => (
                    <label
                      key={source.id}
                      className={clsx(
                        'flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors text-sm',
                        selectedSources.includes(source.id)
                          ? 'border-primary-300 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={selectedSources.includes(source.id)}
                        onChange={() => toggleSource(source.id)}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="truncate">
                        {language === 'ar' ? source.name_ar : source.name_en}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-3 sm:py-4 space-y-4 sm:space-y-6 chat-scroll custom-scrollbar">
        {messages.length === 0 ? (
          <EmptyState
            language={language}
            onQuestionSelect={(q) => {
              setQuestion(q);
              inputRef.current?.focus();
            }}
          />
        ) : (
          messages.map((message, idx) => (
            <ChatMessage
              key={message.id}
              message={message}
              language={language}
              onFollowUp={handleFollowUp}
              isLatest={idx === messages.length - 1 && message.role === 'assistant'}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 px-3 sm:px-6 py-3 sm:py-4 border-t border-gray-100 bg-white safe-area-bottom">
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative flex gap-2 sm:gap-3">
            <div className="relative flex-1">
              <div className={clsx(
                'absolute top-1/2 -translate-y-1/2 pointer-events-none',
                language === 'ar' ? 'right-3' : 'left-3'
              )}>
                <Search className={clsx(
                  'w-4 h-4 sm:w-5 sm:h-5 transition-colors',
                  question ? 'text-primary-500' : 'text-gray-400'
                )} />
              </div>
              <input
                ref={inputRef}
                type="text"
                value={question}
                onChange={(e) => {
                  setQuestion(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                onKeyDown={handleKeyDown}
                placeholder={
                  messages.length > 0
                    ? (language === 'ar' ? 'اطرح سؤال متابعة...' : 'Ask a follow-up question...')
                    : t('ask_placeholder', language)
                }
                className={clsx(
                  'w-full py-3 sm:py-3.5 text-base border-2 border-gray-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 rounded-xl shadow-sm transition-all',
                  language === 'ar' ? 'pr-10 sm:pr-11 pl-3 sm:pl-4' : 'pl-10 sm:pl-11 pr-3 sm:pr-4'
                )}
                dir={language === 'ar' ? 'rtl' : 'ltr'}
                disabled={loading}
                autoComplete="off"
                aria-autocomplete="list"
                aria-controls="suggestions-list"
                aria-expanded={showSuggestions && suggestions.length > 0}
              />

              {/* Suggestions Dropdown */}
              {showSuggestions && suggestions.length > 0 && (
                <div
                  ref={suggestionsRef}
                  id="suggestions-list"
                  role="listbox"
                  className="absolute z-50 w-full mt-1 bg-white rounded-xl shadow-lg border border-gray-200 max-h-72 overflow-y-auto"
                  dir={language === 'ar' ? 'rtl' : 'ltr'}
                >
                  {loadingSuggestions && (
                    <div className="p-3 text-center text-gray-500 text-sm">
                      <div className="inline-block animate-spin w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full mr-2" />
                      {language === 'ar' ? 'جاري البحث...' : 'Searching...'}
                    </div>
                  )}
                  <div className="py-1">
                    {suggestions.map((suggestion, idx) => (
                      <button
                        key={idx}
                        type="button"
                        role="option"
                        aria-selected={idx === selectedSuggestionIndex}
                        onClick={() => handleSelectSuggestion(suggestion)}
                        onMouseEnter={() => setSelectedSuggestionIndex(idx)}
                        className={clsx(
                          'w-full text-left px-4 py-3 transition-colors flex items-center gap-3',
                          idx === selectedSuggestionIndex
                            ? 'bg-primary-50 border-l-2 border-primary-500'
                            : 'hover:bg-gray-50 border-l-2 border-transparent'
                        )}
                      >
                        <Search className={clsx(
                          'w-4 h-4 flex-shrink-0',
                          idx === selectedSuggestionIndex ? 'text-primary-600' : 'text-gray-400'
                        )} />
                        <div className="flex-1 min-w-0">
                          <div className={clsx(
                            'text-sm truncate',
                            idx === selectedSuggestionIndex ? 'text-primary-900 font-medium' : 'text-gray-900'
                          )}>
                            {suggestion.text}
                          </div>
                          <div className="text-xs text-gray-500 capitalize">
                            {suggestion.type === 'concept' && suggestion.concept_type
                              ? (language === 'ar'
                                  ? (suggestion.concept_type === 'person' ? 'شخصية' : suggestion.concept_type === 'theme' ? 'موضوع' : suggestion.concept_type)
                                  : suggestion.concept_type)
                              : suggestion.type}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                  {/* Keyboard hint - hidden on mobile (touch doesn't use keyboard nav) */}
                  <div className="hidden sm:flex px-3 py-2 bg-gray-50 border-t border-gray-100 items-center gap-4 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-600">↑↓</kbd>
                      {language === 'ar' ? 'للتنقل' : 'navigate'}
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-600">↵</kbd>
                      {language === 'ar' ? 'للاختيار' : 'select'}
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-600">Esc</kbd>
                      {language === 'ar' ? 'للإغلاق' : 'close'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !question.trim() || selectedSources.length === 0}
              className={clsx(
                'flex items-center justify-center gap-2 px-3 sm:px-5 py-3 min-w-[48px] min-h-[48px]',
                'bg-gradient-to-r from-primary-500 to-primary-600',
                'hover:from-primary-600 hover:to-primary-700',
                'active:scale-95',
                'text-white font-medium rounded-xl',
                'shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30',
                'transition-all duration-300',
                (loading || !question.trim() || selectedSources.length === 0) && 'opacity-50 cursor-not-allowed shadow-none'
              )}
              aria-label={t('ask_button', language)}
            >
              {loading ? (
                <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
              ) : (
                <Send className="w-5 h-5" />
              )}
              <span className="hidden sm:inline">{t('ask_button', language)}</span>
            </button>
          </div>

          {selectedSources.length === 0 && (
            <p className="text-sm text-red-500 mt-2 flex items-center gap-2">
              {language === 'ar' ? 'يرجى اختيار مصدر تفسير واحد على الأقل' : 'Please select at least one tafseer source'}
            </p>
          )}
        </form>
      </div>
    </div>
  );
}

// Question categories with icons
const QUESTION_CATEGORIES = {
  ar: [
    {
      id: 'famous_verses',
      label: 'آيات مشهورة',
      icon: Star,
      color: 'amber',
      questions: [
        'ما معنى آية الكرسي؟',
        'ما فضل سورة الفاتحة؟',
        'ما تفسير آية النور؟',
        'ما معنى خواتيم سورة البقرة؟',
      ],
    },
    {
      id: 'stories',
      label: 'قصص الأنبياء',
      icon: Users,
      color: 'blue',
      questions: [
        'أخبرني عن قصة يوسف عليه السلام',
        'ما قصة موسى وفرعون؟',
        'قصة إبراهيم والنار',
        'ما قصة أصحاب الكهف؟',
      ],
    },
    {
      id: 'themes',
      label: 'مواضيع قرآنية',
      icon: Heart,
      color: 'rose',
      questions: [
        'ماذا يقول القرآن عن الصبر؟',
        'ما هي التقوى في القرآن؟',
        'آيات عن الرحمة',
        'ما هو التوكل على الله؟',
      ],
    },
    {
      id: 'guidance',
      label: 'هداية ونصائح',
      icon: Lightbulb,
      color: 'emerald',
      questions: [
        'كيف أتدبر القرآن؟',
        'آيات للتخلص من الهم',
        'دعاء الاستخارة في القرآن',
        'آيات عن بر الوالدين',
      ],
    },
  ],
  en: [
    {
      id: 'famous_verses',
      label: 'Famous Verses',
      icon: Star,
      color: 'amber',
      questions: [
        'What is the meaning of Ayat al-Kursi?',
        'What are the virtues of Al-Fatiha?',
        'Explain the Light verse (Ayat an-Nur)',
        'What do the last verses of Al-Baqarah mean?',
      ],
    },
    {
      id: 'stories',
      label: 'Prophet Stories',
      icon: Users,
      color: 'blue',
      questions: [
        'Tell me about the story of Prophet Yusuf',
        'What is the story of Musa and Pharaoh?',
        'Story of Ibrahim and the fire',
        'Tell me about the People of the Cave',
      ],
    },
    {
      id: 'themes',
      label: 'Quranic Themes',
      icon: Heart,
      color: 'rose',
      questions: [
        'What does the Quran say about patience?',
        'What is Taqwa in the Quran?',
        'Verses about mercy',
        'What is Tawakkul (trust in Allah)?',
      ],
    },
    {
      id: 'guidance',
      label: 'Guidance & Wisdom',
      icon: Lightbulb,
      color: 'emerald',
      questions: [
        'How to reflect on the Quran?',
        'Verses for relieving anxiety',
        'What does the Quran say about parents?',
        'Verses about gratitude',
      ],
    },
  ],
};

const COLOR_CLASSES: Record<string, { bg: string; hover: string; text: string; border: string; iconBg: string }> = {
  amber: { bg: 'bg-amber-50', hover: 'hover:bg-amber-100', text: 'text-amber-700', border: 'border-amber-200 hover:border-amber-300', iconBg: 'bg-amber-100' },
  blue: { bg: 'bg-blue-50', hover: 'hover:bg-blue-100', text: 'text-blue-700', border: 'border-blue-200 hover:border-blue-300', iconBg: 'bg-blue-100' },
  rose: { bg: 'bg-rose-50', hover: 'hover:bg-rose-100', text: 'text-rose-700', border: 'border-rose-200 hover:border-rose-300', iconBg: 'bg-rose-100' },
  emerald: { bg: 'bg-emerald-50', hover: 'hover:bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-200 hover:border-emerald-300', iconBg: 'bg-emerald-100' },
};

/** Enhanced empty state with categories and trending topics */
const EmptyState = memo(function EmptyState({
  language,
  onQuestionSelect
}: {
  language: 'ar' | 'en';
  onQuestionSelect: (question: string) => void;
}) {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const categories = QUESTION_CATEGORIES[language];

  return (
    <div className="flex flex-col items-center justify-center min-h-full py-4 sm:py-8 px-2 sm:px-4">
      {/* Hero Section */}
      <div className="text-center mb-6 sm:mb-8 animate-fade-in">
        <div className="relative w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 sm:mb-5">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl sm:rounded-2xl rotate-6 opacity-20" />
          <div className="absolute inset-0 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/30">
            <BookOpen className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
          </div>
          <Sparkles className="absolute -top-1.5 -right-1.5 sm:-top-2 sm:-right-2 w-5 h-5 sm:w-6 sm:h-6 text-amber-500 animate-pulse" />
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2 sm:mb-3">
          {language === 'ar' ? 'اسأل عن القرآن الكريم' : 'Ask About the Quran'}
        </h2>
        <p className="text-sm sm:text-base text-gray-500 max-w-lg mx-auto leading-relaxed px-2">
          {language === 'ar'
            ? 'اكتشف معاني الآيات وقصص الأنبياء والحكمة القرآنية من خلال مصادر التفسير الموثوقة'
            : 'Discover verse meanings, prophet stories, and Quranic wisdom from trusted tafsir sources'}
        </p>
      </div>

      {/* Category Tabs */}
      <div className="w-full max-w-3xl mb-4 sm:mb-6">
        <div className="flex flex-wrap justify-center gap-1.5 sm:gap-2 mb-4 sm:mb-6 px-1">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const colors = COLOR_CLASSES[cat.color];
            const isActive = activeCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(isActive ? null : cat.id)}
                className={clsx(
                  'flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-2 sm:py-2.5 min-h-[40px] rounded-full border-2 transition-all duration-300 text-xs sm:text-sm font-medium',
                  isActive
                    ? `${colors.bg} ${colors.text} ${colors.border} shadow-sm`
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50 active:scale-95'
                )}
              >
                <Icon className={clsx('w-3.5 h-3.5 sm:w-4 sm:h-4', isActive && colors.text)} />
                <span className="truncate">{cat.label}</span>
              </button>
            );
          })}
        </div>

        {/* Questions Grid */}
        <div className="grid gap-2 sm:gap-3 grid-cols-1 sm:grid-cols-2 px-1">
          {(activeCategory
            ? categories.filter((c) => c.id === activeCategory)
            : categories
          ).map((cat) =>
            cat.questions.slice(0, activeCategory ? 4 : 1).map((q, i) => {
              const Icon = cat.icon;
              const colors = COLOR_CLASSES[cat.color];
              return (
                <button
                  key={`${cat.id}-${i}`}
                  onClick={() => onQuestionSelect(q)}
                  className={clsx(
                    'group text-left p-3 sm:p-4 rounded-xl border-2 transition-all duration-300 min-h-[60px]',
                    colors.border,
                    colors.hover,
                    'bg-white hover:shadow-md active:scale-[0.98]'
                  )}
                  dir={language === 'ar' ? 'rtl' : 'ltr'}
                >
                  <div className="flex items-start gap-2 sm:gap-3">
                    <div className={clsx('p-1.5 sm:p-2 rounded-lg transition-colors shrink-0', colors.iconBg)}>
                      <Icon className={clsx('w-3.5 h-3.5 sm:w-4 sm:h-4', colors.text)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-sm sm:text-base text-gray-800 group-hover:text-gray-900 transition-colors line-clamp-2">
                        {q}
                      </span>
                      {!activeCategory && (
                        <span className={clsx('text-xs mt-1 block', colors.text)}>
                          {cat.label}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Quick Tips */}
      <div className="w-full max-w-2xl mt-4 sm:mt-6 mx-2 sm:mx-0 p-3 sm:p-4 bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl border border-primary-100">
        <div className="flex items-start gap-2 sm:gap-3">
          <div className="p-1.5 sm:p-2 bg-white rounded-lg shadow-sm flex-shrink-0">
            <Lightbulb className="w-4 h-4 sm:w-5 sm:h-5 text-primary-600" />
          </div>
          <div className="min-w-0">
            <h4 className="font-semibold text-gray-900 mb-0.5 sm:mb-1 text-sm sm:text-base">
              {language === 'ar' ? 'نصيحة سريعة' : 'Quick Tip'}
            </h4>
            <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
              {language === 'ar'
                ? 'جرب أسئلة مثل "ما معنى آية الكرسي؟" للحصول على إجابات سريعة ودقيقة من التفاسير المعتمدة'
                : 'Try questions like "What is Ayat al-Kursi?" for fast, accurate answers from trusted tafsir sources'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
});
