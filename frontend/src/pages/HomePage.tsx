import { Link } from 'react-router-dom';
import { Book, MessageCircle, Network, ArrowRight } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';

export function HomePage() {
  const { language } = useLanguageStore();

  const features = [
    {
      icon: Book,
      title: language === 'ar' ? 'قصص القرآن' : 'Quran Stories',
      description:
        language === 'ar'
          ? 'استكشف القصص القرآنية وترابطها عبر السور المختلفة'
          : 'Explore Quranic stories and their connections across different surahs',
      link: '/stories',
      color: 'bg-blue-500',
    },
    {
      icon: MessageCircle,
      title: language === 'ar' ? 'اسأل بالاستناد للمصادر' : 'Ask with Citations',
      description:
        language === 'ar'
          ? 'احصل على إجابات مستندة إلى التفاسير الموثقة'
          : 'Get answers grounded in authenticated tafseer sources',
      link: '/ask',
      color: 'bg-green-500',
    },
    {
      icon: Network,
      title: language === 'ar' ? 'الروابط البيانية' : 'Story Connections',
      description:
        language === 'ar'
          ? 'تصور الروابط بين أجزاء القصص عبر الرسم البياني'
          : 'Visualize connections between story segments through interactive graphs',
      link: '/stories',
      color: 'bg-purple-500',
    },
  ];

  return (
    <div className="min-h-[calc(100vh-4rem)]">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 to-primary-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            {t('app_title', language)}
          </h1>
          <p className="text-xl md:text-2xl text-primary-100 mb-8 max-w-3xl mx-auto">
            {t('app_subtitle', language)}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/stories"
              className="btn-primary bg-white text-primary-700 hover:bg-primary-50 px-8 py-3 text-lg"
            >
              {t('nav_stories', language)}
              <ArrowRight className="w-5 h-5 inline ml-2" />
            </Link>
            <Link
              to="/ask"
              className="btn-secondary border-2 border-white text-white hover:bg-white/10 px-8 py-3 text-lg"
            >
              {t('nav_ask', language)}
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Link
                  key={feature.link + feature.title}
                  to={feature.link}
                  className="card hover:shadow-lg transition-shadow group"
                >
                  <div
                    className={`w-12 h-12 ${feature.color} rounded-lg flex items-center justify-center mb-4`}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2 group-hover:text-primary-600 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">{feature.description}</p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Safety Notice */}
      <section className="py-12 bg-gold-50 border-t border-gold-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-lg font-semibold text-gold-800 mb-2">
            {language === 'ar' ? 'ملاحظة مهمة' : 'Important Notice'}
          </h2>
          <p className="text-gold-700">
            {language === 'ar'
              ? 'جميع الإجابات في هذا التطبيق مستندة إلى مصادر تفسيرية موثقة. لا يقوم النظام بتوليد تفسيرات من تلقاء نفسه.'
              : 'All answers in this application are grounded in authenticated tafseer sources. The system does not generate interpretations on its own.'}
          </p>
        </div>
      </section>
    </div>
  );
}
