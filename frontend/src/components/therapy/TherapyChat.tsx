import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, BookOpen, AlertCircle } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { therapyApi } from '../../lib/api';
import type { ChatResponse, GuidanceCard as GuidanceCardType } from '../../types/therapy';
import { SpiritualGuidanceCard } from './SpiritualGuidanceCard';
import clsx from 'clsx';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  response?: ChatResponse;
}

interface TherapyChatProps {
  initialEmotion?: string;
  onSessionCreated?: (sessionId: string) => void;
}

export function TherapyChat({ initialEmotion, onSessionCreated }: TherapyChatProps) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationSessionId, setConversationSessionId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    setError(null);

    const userMsg: ChatMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    const priorContext = messages.slice(-6).map(m => ({
      role: m.role,
      content: m.role === 'assistant' ? (m.response?.answer ?? m.content) : m.content,
    }));

    try {
      const data = await therapyApi.chat({
        message: text,
        language,
        emotion_override: initialEmotion,
        session_id: conversationSessionId ?? undefined,
        conversation_context: priorContext.length > 0 ? priorContext : undefined,
      });

      if (!conversationSessionId) {
        setConversationSessionId(data.session_id);
        onSessionCreated?.(data.session_id);
      }

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.answer,
        response: data,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setError(t('chat_error', language));
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex flex-col h-full min-h-[500px]">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className={clsx('text-center py-10', isRtl && 'font-arabic')}>
            <Bot className="w-10 h-10 text-indigo-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">{t('chat_intro', language)}</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === 'user' ? (
              <div className={clsx('flex gap-3', isRtl ? 'flex-row-reverse' : 'flex-row')}>
                <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-primary-600" />
                </div>
                <div className={clsx(
                  'max-w-[80%] bg-primary-50 rounded-2xl px-4 py-3 text-sm text-gray-800',
                  isRtl ? 'font-arabic text-right rounded-tr-sm' : 'rounded-tl-sm',
                )}>
                  {msg.content}
                </div>
              </div>
            ) : (
              <div className={clsx('flex gap-3', isRtl ? 'flex-row-reverse' : 'flex-row')}>
                <div className="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className={clsx(
                    'bg-white border border-gray-100 rounded-2xl px-4 py-3 text-sm text-gray-800 shadow-sm',
                    isRtl ? 'font-arabic text-right rounded-tr-sm' : 'rounded-tl-sm',
                  )}>
                    {msg.content}
                  </div>

                  {/* Citations */}
                  {msg.response?.citations && msg.response.citations.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {msg.response.citations.map((c, ci) => (
                        <div key={ci} className="flex items-start gap-1.5 text-xs text-gray-500">
                          <BookOpen className="w-3 h-3 mt-0.5 flex-shrink-0 text-amber-500" />
                          <span>
                            <span className="font-medium text-amber-700">{c.source_name}</span>
                            {' · '}
                            <span dir="ltr">{c.verse_reference}</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Fallback cards when RAG unavailable */}
                  {msg.response?.fallback_cards && msg.response.fallback_cards.length > 0 && (
                    <div className="mt-3 space-y-3">
                      {msg.response.fallback_cards.map((card: GuidanceCardType, ci: number) => (
                        <SpiritualGuidanceCard key={ci} card={card} index={ci} />
                      ))}
                    </div>
                  )}

                  {/* Follow-up suggestions */}
                  {msg.response?.follow_up_suggestions && msg.response.follow_up_suggestions.length > 0 && (
                    <div className={clsx('mt-2 flex flex-wrap gap-1.5', isRtl && 'justify-end')}>
                      {msg.response.follow_up_suggestions.map((s, si) => (
                        <button
                          key={si}
                          onClick={() => setInput(s)}
                          className={clsx(
                            'text-xs px-2.5 py-1 rounded-full border border-indigo-200 text-indigo-600 hover:bg-indigo-50 transition-colors',
                            isRtl && 'font-arabic',
                          )}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className={clsx('flex gap-3', isRtl ? 'flex-row-reverse' : 'flex-row')}>
            <div className="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
              <Loader2 className="w-4 h-4 text-emerald-600 animate-spin" />
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                {[0, 1, 2].map(d => (
                  <span
                    key={d}
                    className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce"
                    style={{ animationDelay: `${d * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 rounded-xl px-4 py-3">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className={clsx(isRtl && 'font-arabic')}>{error}</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-100 pt-3 mt-2">
        <div className="flex gap-2 items-end">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('chat_placeholder', language)}
            rows={2}
            className={clsx(
              'flex-1 resize-none rounded-xl border border-gray-200 px-3 py-2.5 text-sm',
              'focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-300',
              'placeholder:text-gray-400',
              isRtl && 'font-arabic text-right',
            )}
            dir={isRtl ? 'rtl' : 'ltr'}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className={clsx(
              'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors',
              input.trim() && !loading
                ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                : 'bg-gray-100 text-gray-300 cursor-not-allowed',
            )}
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className={clsx('text-xs text-gray-400 mt-1', isRtl ? 'text-right font-arabic' : 'text-right')}>
          {t('therapy_ctrl_enter', language)}
        </p>
      </div>
    </div>
  );
}
