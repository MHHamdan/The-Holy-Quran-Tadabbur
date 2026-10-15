/**
 * Privacy policy (required for Google Play and the App Store), public at
 * /privacy. Describes the data flows the code actually has; keep it in step
 * with backend/app/api/routes (therapy, tasmee, feedback, search) and
 * frontend/src/lib/islamicApis.ts when they change.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { ShieldCheck, Trash2 } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { eraseAllMyData } from '../lib/dataErasure';

const EFFECTIVE = '2026-10-14';
const CONTACT = (import.meta.env.VITE_PRIVACY_CONTACT || '').trim();

type Bi = { ar: string; en: string };
interface Section { title: Bi; items: Bi[] }

const SECTIONS: Section[] = [
  {
    title: { en: 'In short', ar: 'باختصار' },
    items: [
      { en: 'No accounts, no advertising, no analytics or tracking, and nothing is sold or shared for marketing.', ar: 'لا حسابات، ولا إعلانات، ولا أدوات تحليل أو تتبّع، ولا نبيع أي بيانات ولا نشاركها لأغراض تسويقية.' },
      { en: 'Most of what you create stays on your device. What reaches our server is listed below, with how long it is kept.', ar: 'معظم ما تنشئه يبقى على جهازك. وما يصل إلى خادمنا مذكور أدناه مع مدة الاحتفاظ به.' },
    ],
  },
  {
    title: { en: 'Kept only on your device', ar: 'ما يُحفظ على جهازك فقط' },
    items: [
      { en: 'Bookmarks and notes, your journal, reading progress and streaks, the reading plan, flashcard schedule, dhikr counts, reader settings, recent searches, saved offline recitations and your reminder time.', ar: 'الإشارات المرجعية والملاحظات، ويومياتك، وتقدّم القراءة والأيام المتتالية، وخطة الختمة، وجدول بطاقات الحفظ، وعدّاد الأذكار، وإعدادات القراءة، وعمليات البحث الأخيرة، والتلاوات المحفوظة دون اتصال، ووقت التذكير.' },
      { en: 'Deleting the app, clearing its data, or the button at the end of this page removes them.', ar: 'تُحذف بحذف التطبيق أو مسح بياناته، أو بالزر في آخر هذه الصفحة.' },
      { en: 'This data never reaches our server. If you have turned on your phone\'s own backup (for example iCloud or Google backup), that backup may include it, under your account.', ar: 'لا تصل هذه البيانات إلى خادمنا. وإذا فعّلت النسخ الاحتياطي في هاتفك (مثل iCloud أو نسخ Google الاحتياطي) فقد يتضمّنها ذلك النسخ ضمن حسابك.' },
    ],
  },
  {
    title: { en: 'Sent to our server', ar: 'ما يُرسل إلى خادمنا' },
    items: [
      { en: 'Questions you ask the AI assistant, to answer them with cited sources. The conversation is kept for up to 24 hours so follow-up questions work, then deleted.', ar: 'الأسئلة التي توجّهها إلى المساعد الذكي، للإجابة عنها مع ذكر المصادر. تُحفظ المحادثة مدة أقصاها ٢٤ ساعة لتعمل الأسئلة المتابِعة، ثم تُحذف.' },
      { en: 'Spiritual guidance: your message is used to answer and is not stored. We keep the detected feeling, the theme and the verse references shown, without anything that identifies you, for up to 180 days. A reflection you choose to save is kept with it until you delete it or 180 days pass.', ar: 'الإرشاد الروحي: تُستخدم رسالتك للإجابة ولا تُحفظ. نحتفظ بالشعور المكتشَف والموضوع ومراجع الآيات المعروضة، دون أي معرّف لك، مدة أقصاها ١٨٠ يومًا. والتأمّل الذي تختار حفظه يبقى معها حتى تحذفه أو تمضي ١٨٠ يومًا.' },
      { en: 'Recitation practice (Tasmeeʿ): microphone audio is streamed while you recite, turned into text to compare with the verse, and never saved. The recognised words and possible mistakes of each session are kept without your identity for up to 90 days, then deleted; "Delete my data" removes this device\'s sessions sooner.', ar: 'التسميع: يُرسل صوت الميكروفون أثناء التلاوة ويُحوَّل إلى نص لمقارنته بالآية، ولا يُحفظ الصوت أبدًا. وتُحفظ الكلمات المتعرَّف عليها والأخطاء المحتملة لكل جلسة دون هويتك مدة أقصاها ٩٠ يومًا ثم تُحذف، ويحذف زر «حذف بياناتي» جلسات هذا الجهاز قبل ذلك.' },
      { en: 'Feedback you send: your message and the page it is about. No name or contact details are requested.', ar: 'الملاحظات التي ترسلها: نص ملاحظتك والصفحة التي تخصها. لا نطلب اسمًا ولا وسيلة تواصل.' },
      { en: 'Searches: the query, to return results. Recent searches may also be held in server memory for your session and are lost on restart.', ar: 'البحث: نص البحث لإرجاع النتائج. وقد تُحفظ عمليات البحث الأخيرة مؤقتًا في ذاكرة الخادم لجلستك وتزول عند إعادة تشغيله.' },
      { en: 'Your IP address is held in memory for about a minute to limit abuse, and is not written to our logs.', ar: 'يُحفظ عنوان IP في الذاكرة نحو دقيقة للحدّ من الإساءة، ولا يُكتب في سجلاتنا.' },
    ],
  },
  {
    title: { en: 'Services that process data for us', ar: 'خدمات تعالج البيانات لصالحنا' },
    items: [
      { en: 'Hugging Face (Inference Providers) runs the AI models: questions, guidance messages, meaning-based searches and recitation audio are processed there to produce an answer, search results or a transcription.', ar: 'تشغّل Hugging Face (مزوّدو الاستدلال) نماذج الذكاء الاصطناعي: تُعالَج هناك الأسئلة ورسائل الإرشاد وعمليات البحث بالمعنى وصوت التلاوة لإنتاج الإجابة أو نتائج البحث أو النص.' },
    ],
  },
  {
    title: { en: 'Services your device contacts directly', ar: 'خدمات يتصل بها جهازك مباشرة' },
    items: [
      { en: 'Prayer times and the Hijri date: AlAdhan (api.aladhan.com) receives your approximate location (rounded to about 1 km) or the city you enter. Place names and the mosque finder: OpenStreetMap (Nominatim, Overpass) receives the same approximate location. The exact position stays on your device (it is used there for the Qibla direction) and your location is never sent to our server.', ar: 'مواقيت الصلاة والتاريخ الهجري: تستقبل AlAdhan ‏(api.aladhan.com) موقعك التقريبي (مقرَّبًا إلى نحو كيلومتر) أو المدينة التي تدخلها. أسماء الأماكن والبحث عن المساجد: تستقبل OpenStreetMap ‏(Nominatim وOverpass) الموقع التقريبي نفسه. ويبقى الموقع الدقيق على جهازك (يُستخدم فيه لحساب اتجاه القبلة)، ولا يُرسل موقعك إلى خادمنا أبدًا.' },
      { en: 'Recitations stream from everyayah.com, cdn.islamic.network, quranicaudio.com and verses.quran.com. The external resource pages load from archive.org (books) and YouTube (video thumbnails). Fonts are part of the app and are not downloaded from anyone. These services see your IP address, as any website does.', ar: 'تُبثّ التلاوات من everyayah.com وcdn.islamic.network وquranicaudio.com وverses.quran.com. وتُحمَّل صفحات الروابط الخارجية من archive.org (الكتب) وYouTube (صور المقاطع). أما الخطوط فجزء من التطبيق ولا تُنزَّل من أي جهة. ترى هذه الخدمات عنوان IP الخاص بك كأي موقع.' },
    ],
  },
  {
    title: { en: 'Permissions', ar: 'الأذونات' },
    items: [
      { en: 'Microphone: only when you start recitation practice. Location: only when you ask for prayer times, the Qibla or nearby mosques. Notifications: only if you turn on the daily reading reminder (it is scheduled on your device; there is no push service). Every feature still works without them, except the one that needs it.', ar: 'الميكروفون: عند بدء التسميع فقط. الموقع: عند طلب مواقيت الصلاة أو القبلة أو المساجد القريبة فقط. الإشعارات: إذا فعّلت تذكير القراءة اليومي فقط (يُجدول على جهازك، دون خدمة إشعارات خارجية). وتعمل بقية الميزات دونها.' },
    ],
  },
  {
    title: { en: 'Children', ar: 'الأطفال' },
    items: [
      { en: 'The app is for a general audience and collects no personal information knowingly from anyone, including children.', ar: 'التطبيق موجّه للجميع، ولا يجمع عن قصد معلومات شخصية من أي أحد، بمن فيهم الأطفال.' },
    ],
  },
  {
    title: { en: 'Changes', ar: 'التغييرات' },
    items: [
      { en: 'If this policy changes, the new version and its date appear on this page.', ar: 'إذا تغيّرت هذه السياسة فستظهر نسختها الجديدة وتاريخها في هذه الصفحة.' },
    ],
  },
];

export function PrivacyPage() {
  const { language } = useLanguageStore();
  const ar = language === 'ar';
  const [state, setState] = useState<'idle' | 'working' | 'done' | 'partial'>('idle');
  const pick = (b: Bi) => (ar ? b.ar : b.en);

  async function erase() {
    if (!confirm(ar
      ? 'سيُحذف كل ما حفظه التطبيق لك على هذا الجهاز وعلى خادمنا. لا يمكن التراجع. متابعة؟'
      : 'This deletes everything the app keeps for you on this device and on our server. It cannot be undone. Continue?')) return;
    setState('working');
    const result = await eraseAllMyData();
    setState(result.serverError ? 'partial' : 'done');
  }

  return (
    <div className={clsx('max-w-3xl mx-auto px-4 sm:px-6 py-8', ar && 'font-arabic')} dir={ar ? 'rtl' : 'ltr'}>
      <div className="flex items-center gap-3 mb-2">
        <ShieldCheck className="w-7 h-7 text-emerald-600" />
        <h1 className="text-2xl font-bold text-gray-900">{ar ? 'سياسة الخصوصية' : 'Privacy policy'}</h1>
      </div>
      <p className="text-sm text-gray-600 mb-8">
        {ar ? 'سارية من ' : 'Effective '}
        <bdi dir="ltr">{EFFECTIVE}</bdi>
      </p>

      {SECTIONS.map((section) => (
        <section key={section.title.en} className="mb-7">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">{pick(section.title)}</h2>
          <ul className="space-y-2 list-disc ps-5 text-gray-700 leading-relaxed">
            {section.items.map((item) => <li key={item.en}>{pick(item)}</li>)}
          </ul>
        </section>
      ))}

      <section className="mb-7">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">{ar ? 'التواصل' : 'Contact'}</h2>
        <p className="text-gray-700">
          {CONTACT
            ? <>{ar ? 'لأي سؤال عن الخصوصية: ' : 'Privacy questions: '}<a className="text-primary-600 underline" href={`mailto:${CONTACT}`} dir="ltr">{CONTACT}</a></>
            : (ar ? 'استخدم زر الملاحظات في أي صفحة.' : 'Use the feedback button on any page.')}
        </p>
      </section>

      <section className="rounded-2xl border border-red-200 bg-red-50 p-5">
        <h2 className="text-lg font-semibold text-red-900 mb-1">{ar ? 'حذف بياناتي' : 'Delete my data'}</h2>
        <p className="text-sm text-red-800 mb-3">
          {ar
            ? 'يحذف من خادمنا جلسات الإرشاد والتأمّلات وجلسات التسميع التي أنشأها هذا الجهاز، ويحذف من جهازك كل بيانات التطبيق والتلاوات المحفوظة والتذكير.'
            : 'Deletes the guidance sessions, reflections and Tasmeeʿ sessions this device created from our server, and all app data, saved recitations and the reminder from this device.'}
        </p>
        <button
          type="button"
          onClick={erase}
          disabled={state === 'working' || state === 'done'}
          className="inline-flex min-h-11 items-center gap-2 px-4 py-2 rounded-lg bg-red-700 text-white text-sm font-medium hover:bg-red-800 disabled:opacity-50"
        >
          <Trash2 className="w-4 h-4" />
          {state === 'working' ? (ar ? 'جارٍ الحذف…' : 'Deleting…') : (ar ? 'احذف بياناتي' : 'Delete my data')}
        </button>
        {state !== 'idle' && state !== 'working' && (
          <p role="status" className="mt-3 text-sm text-red-900">
            {state === 'done'
              ? (ar ? 'حُذفت بياناتك.' : 'Your data has been deleted.')
              : (ar ? 'حُذفت بيانات الجهاز، لكن تعذّر الوصول إلى الخادم. حاول مجددًا لاحقًا.' : 'Device data was deleted, but the server could not be reached. Try again later.')}
          </p>
        )}
      </section>

      <p className="mt-8 flex flex-wrap gap-x-4 text-sm text-gray-600">
        <Link to="/sources" className="inline-block py-2 underline">{ar ? 'مصادر المحتوى وتراخيصها' : 'Content sources and licences'}</Link>
        <Link to="/licenses" className="inline-block py-2 underline">{ar ? 'تراخيص البرمجيات والخطوط' : 'Software and font licences'}</Link>
      </p>
    </div>
  );
}
