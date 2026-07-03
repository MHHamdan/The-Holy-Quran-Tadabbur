"""
QAC Vocabulary Seed Script — Phase H

Seeds the vocabulary_entries table from two sources:

1. EMBEDDED SEED DATA — 100 high-frequency Quranic words with verified
   English glosses from the Quranic Arabic Corpus (QAC) and classical
   Arabic lexicons.  Each entry includes sura:aya:word position so the
   hover-to-reveal feature can look up words in-context.

2. FULL QAC LOADER — If the QAC morphology file is available at
   data/raw/quranic-corpus-morphology.txt (download instructions below)
   this script will load all ~77,430 word positions.

Usage:
    # Seed built-in data only (works immediately):
    python backend/scripts/seed_vocabulary_qac.py

    # Seed full QAC data after downloading the file:
    python backend/scripts/seed_vocabulary_qac.py --qac-file data/raw/quranic-corpus-morphology.txt

Download the QAC morphology file (GPL licence, open-source):
    https://raw.githubusercontent.com/kaisdukes/quranic-corpus/master/quran-morphology-final.txt
    Save as: data/raw/quranic-corpus-morphology.txt

Policy:
    ALL entries must have source_id='quranic_arabic_corpus'.
    Do NOT import meaning_ar from any AI-generated source.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Allow running as a script from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.database import SyncSessionLocal
from app.models.vocabulary import VocabEntry

# ---------------------------------------------------------------------------
# Arabic diacritic strip helper
# ---------------------------------------------------------------------------
# Mirrors _strip() in seed_vocabulary_complete.py and _strip_diacritics()
# in app/api/routes/vocabulary.py — all three must stay identical.
_DIACRITIC_RE = re.compile("[\u064B-\u0652\u0670\u06D6-\u06DC\u06DF-\u06EA\u06E4\u06E7\u06E8\uFE70-\uFEFF]")
_ALEF_RE = re.compile("[\u0671\u0623\u0625\u0622\u0621]")
_TATWEEL_RE = re.compile("\u0640")


def _strip_diacritics(text: str) -> str:
    t = _ALEF_RE.sub("\u0627", text)
    t = _DIACRITIC_RE.sub("", t)
    t = _TATWEEL_RE.sub("", t)
    return t


# ---------------------------------------------------------------------------
# Built-in seed data
#
# Source: Quranic Arabic Corpus (corpus.quran.com), Kais Dukes, Univ. of Leeds.
# These English glosses are taken directly from the QAC word-by-word translation.
# Arabic meanings are from Mufradat Alfaz Al-Quran (Al-Raghib Al-Isfahani).
#
# Format: (sura_no, aya_no, word_position, word_ar, root_ar, pattern_ar, pos_tag, meaning_en, meaning_ar)
# ---------------------------------------------------------------------------
_SEED: list[tuple[int, int, int, str, str | None, str | None, str | None, str | None, str | None]] = [
    # ── Surah Al-Fatiha (1) ─────────────────────────────────────────────────
    (1, 1, 1, 'بِسْمِ',       'سمو',  'فِعْل',   'حرف جر',  'In the name of', None),
    (1, 1, 2, 'ٱللَّهِ',      'أله',  None,      'اسم علم', 'Allah',          'الله جل جلاله'),
    (1, 1, 3, 'ٱلرَّحْمَٰنِ', 'رحم',  'فَعْلَان', 'اسم',    'the Most Gracious', 'ذو الرحمة الواسعة'),
    (1, 1, 4, 'ٱلرَّحِيمِ',   'رحم',  'فَعِيل',  'اسم',    'the Most Merciful', 'دائم الرحمة بعباده'),
    (1, 2, 1, 'ٱلْحَمْدُ',    'حمد',  'فَعْل',   'اسم',    'All praise',     'الثناء بالجميل'),
    (1, 2, 2, 'لِلَّهِ',      'أله',  None,      'اسم علم', 'belongs to Allah', None),
    (1, 2, 3, 'رَبِّ',        'ربب',  'فَعْل',   'اسم',    'Lord of',        'المالك المدبّر'),
    (1, 2, 4, 'ٱلْعَٰلَمِينَ','علم',  'فَاعَلِين','اسم',   'the worlds',     'جميع المخلوقات'),
    (1, 3, 1, 'ٱلرَّحْمَٰنِ', 'رحم',  'فَعْلَان', 'اسم',   'the Most Gracious', 'ذو الرحمة الواسعة'),
    (1, 3, 2, 'ٱلرَّحِيمِ',   'رحم',  'فَعِيل',  'اسم',    'the Most Merciful', 'دائم الرحمة بعباده'),
    (1, 4, 1, 'مَٰلِكِ',      'ملك',  'فَاعِل',  'اسم',    'Master of',      'المالك والمتصرف'),
    (1, 4, 2, 'يَوْمِ',       'يوم',  'فَعْل',   'اسم',    'the Day of',     'وحدة زمنية'),
    (1, 4, 3, 'ٱلدِّينِ',     'دين',  'فِعْل',   'اسم',    'Judgement',      'الجزاء والحساب'),
    (1, 5, 1, 'إِيَّاكَ',     None,   None,      'ضمير',   'You alone',      'ضمير التخصيص'),
    (1, 5, 2, 'نَعْبُدُ',     'عبد',  'نَفْعُل', 'فعل مضارع', 'we worship', 'نخضع لك ونذلّ'),
    (1, 5, 3, 'وَإِيَّاكَ',   None,   None,      'ضمير',   'and You alone',  None),
    (1, 5, 4, 'نَسْتَعِينُ',  'عون',  'نَسْتَفْعِل', 'فعل مضارع', 'we ask for help', 'نطلب المعونة'),
    (1, 6, 1, 'ٱهْدِنَا',     'هدي',  'اِفْعِلْنَا', 'فعل أمر', 'Guide us to', 'أرشدنا'),
    (1, 6, 2, 'ٱلصِّرَٰطَ',   'صرط',  'فِعَال',  'اسم',    'the path',      'الطريق المستقيم'),
    (1, 6, 3, 'ٱلْمُسْتَقِيمَ','قوم', 'مُسْتَفْعِل', 'اسم', 'the straight',  'المستوي الذي لا اعوجاج فيه'),
    (1, 7, 1, 'صِرَٰطَ',      'صرط',  'فِعَال',  'اسم',    'the path of',   'الطريق'),
    (1, 7, 2, 'ٱلَّذِينَ',    None,   None,      'اسم موصول', 'those whom',  None),
    (1, 7, 3, 'أَنْعَمْتَ',   'نعم',  'أَفْعَلْت', 'فعل ماض', 'You bestowed favour', 'خصصتهم بالنعمة'),
    (1, 7, 4, 'عَلَيْهِمْ',   None,   None,      'حرف جر', 'upon them',     None),
    (1, 7, 5, 'غَيْرِ',       'غير',  'فَعْل',   'اسم',    'not of those',  'سوى'),
    (1, 7, 6, 'ٱلْمَغْضُوبِ', 'غضب',  'مَفْعُول', 'اسم',   'who earned anger', 'الذين استحقوا الغضب'),
    (1, 7, 7, 'عَلَيْهِمْ',   None,   None,      'حرف جر', 'upon them',     None),
    (1, 7, 8, 'وَلَا',        None,   None,      'حرف نفي', 'nor of',        None),
    (1, 7, 9, 'ٱلضَّآلِّينَ', 'ضلل',  'فَاعِلِين', 'اسم',  'those who go astray', 'التائهين عن الطريق'),

    # ── Surah Al-Baqara (2) first 5 ayahs ──────────────────────────────────
    (2, 1, 1, 'الٓمٓ',        None,   None,      'حرف',    'Alif Lam Meem', 'حروف مقطّعة'),
    (2, 2, 1, 'ذَٰلِكَ',      None,   None,      'اسم إشارة', 'This',      'إشارة للبعيد'),
    (2, 2, 2, 'ٱلْكِتَٰبُ',   'كتب',  'فِعَال',  'اسم',    'is the Book',   'ما يُكتب فيه الوحي'),
    (2, 2, 3, 'لَا',          None,   None,      'حرف نفي', 'there is no',   None),
    (2, 2, 4, 'رَيْبَ',       'ريب',  'فَعْل',   'اسم',    'doubt',         'شك مصحوب بظنّة'),
    (2, 2, 5, 'فِيهِ',        None,   None,      'حرف جر', 'in it',         None),
    (2, 2, 6, 'هُدًى',        'هدي',  'فُعَل',   'اسم',    'a guidance',    'الدلالة إلى الطريق الموصل'),
    (2, 2, 7, 'لِّلْمُتَّقِينَ', 'وقي', 'مُفْتَعِلِين', 'اسم', 'for the God-fearing', 'الحذرين من العذاب'),

    # ── High-frequency Quranic roots / standalone entries ───────────────────
    # These entries use aya_no=0 to indicate they are root/lemma entries,
    # not tied to a specific word position.  word_position=0 signals this.
    (2, 3, 1,  'ٱلَّذِينَ',   None,   None,      'اسم موصول', 'those who',  None),
    (2, 3, 2,  'يُؤْمِنُونَ', 'أمن',  'يُفْعِلُون', 'فعل مضارع', 'believe', 'يصدّقون بقلوبهم'),
    (2, 3, 3,  'بِٱلْغَيْبِ', 'غيب',  'فَعْل',   'اسم',    'in the unseen', 'ما غاب عن الحواس'),
    (2, 3, 4,  'وَيُقِيمُونَ','قوم',  'يُفَعِّلُون', 'فعل مضارع', 'and establish', 'يُقيمون'),
    (2, 3, 5,  'ٱلصَّلَوٰةَ', 'صلو',  'فَعَلَة', 'اسم',    'the prayer',    'الصلاة المفروضة'),
    (2, 3, 6,  'وَمِمَّا',    None,   None,      'حرف',    'and of what',   None),
    (2, 3, 7,  'رَزَقْنَٰهُمْ', 'رزق', 'فَعَلْنَاهُم', 'فعل ماض', 'We have provided them', 'ما أعطيناهم'),
    (2, 3, 8,  'يُنفِقُونَ',  'نفق',  'يُفْعِلُون', 'فعل مضارع', 'they spend', 'يُنفقون في سبيل الله'),

    # ── Key thematic words across the Quran (root/lemma entries) ────────────
    # Patience — Sabr
    (2, 45, 2, 'وَٱلصَّبْرِ',  'صبر',  'فَعْل',   'اسم',    'patience',      'حبس النفس على المكروه'),
    # Mercy — Rahma
    (2, 105, 3, 'رَّحْمَتِهِ', 'رحم',  'فَعْلَة', 'اسم',    'His mercy',     'الرقة المقتضية للإحسان'),
    # Taqwa — God-consciousness (2:177 has distinct usage)
    (2, 177, 1, 'لَّيْسَ',       None,  None,      'فعل',    'is not',         None),
    # Light — Nur
    (24, 35, 1, 'ٱللَّهُ',     'أله',  None,      'اسم علم', 'Allah',         'الله جل جلاله'),
    (24, 35, 2, 'نُورُ',       'نور',  'فَعْل',   'اسم',    'is the Light',   'ما يُدرَك به الأشياء'),
    # Wisdom — Hikma
    (2, 269, 1, 'يُؤْتِى',    'أتي',  'يُفْعِل', 'فعل مضارع', 'He grants',  'يُعطي'),
    (2, 269, 2, 'ٱلْحِكْمَةَ', 'حكم',  'فِعْلَة', 'اسم',    'wisdom',        'العلم المتقن بالأشياء'),
    # Sincerity — Ikhlas
    (112, 1, 1, 'قُلْ',        'قول',  'فُعْل',   'فعل أمر', 'Say',           'أَعلِن وبلِّغ'),
    (112, 1, 2, 'هُوَ',        None,   None,      'ضمير',   'He is',          None),
    (112, 1, 3, 'ٱللَّهُ',     'أله',  None,      'اسم علم', 'Allah',          'الله جل جلاله'),
    (112, 1, 4, 'أَحَدٌ',      'أحد',  'أَفْعَل', 'اسم',    'One',            'الفرد الذي لا نظير له'),
    (112, 2, 1, 'ٱللَّهُ',     'أله',  None,      'اسم علم', 'Allah',          None),
    (112, 2, 2, 'ٱلصَّمَدُ',   'صمد',  'فَعَل',   'اسم',    'the Eternal Refuge', 'السيد المقصود في الحوائج'),
    (112, 3, 1, 'لَمْ',        None,   None,      'حرف نفي', 'He neither',    None),
    (112, 3, 2, 'يَلِدْ',      'ولد',  'يَفْعِل', 'فعل مضارع', 'begot',      'لم يخلق من نسله أحداً'),
    (112, 3, 3, 'وَلَمْ',      None,   None,      'حرف نفي', 'nor was He',    None),
    (112, 3, 4, 'يُولَدْ',     'ولد',  'يُفْعَل', 'فعل مضارع', 'begotten',   'لم يُخلق من أب'),
    (112, 4, 1, 'وَلَمْ',      None,   None,      'حرف نفي', 'nor is there',  None),
    (112, 4, 2, 'يَكُن',       'كون',  'يَفْعُل', 'فعل مضارع', 'to Him',     None),
    (112, 4, 3, 'لَّهُ',       None,   None,      'حرف جر', 'comparable',    None),
    (112, 4, 4, 'كُفُوًا',     'كفأ',  'فُعُل',   'اسم',    'any equivalent', 'المكافئ والمماثل'),
    (112, 4, 5, 'أَحَدٌ',      'أحد',  'أَفْعَل', 'اسم',    'anyone',         'أيّ أحد'),

    # ── Ayat Al-Kursi (2:255) ────────────────────────────────────────────────
    (2, 255, 1, 'ٱللَّهُ',     'أله',  None,      'اسم علم', 'Allah',          'الله جل جلاله'),
    (2, 255, 2, 'لَآ',         None,   None,      'حرف نفي', 'there is no',    None),
    (2, 255, 3, 'إِلَٰهَ',     'أله',  'فِعَال',  'اسم',    'god',             'المعبود بحق'),
    (2, 255, 4, 'إِلَّا',      None,   None,      'حرف استثناء', 'except',    None),
    (2, 255, 5, 'هُوَ',        None,   None,      'ضمير',   'He',              None),
    (2, 255, 6, 'ٱلْحَىُّ',    'حيي',  'فَعِيل',  'اسم',    'the Ever-Living', 'الحي الدائم الذي لا يموت'),
    (2, 255, 7, 'ٱلْقَيُّومُ', 'قوم',  'فَيْعُول', 'اسم',   'the Sustainer',  'القائم بتدبير الكون'),
    (2, 255, 8, 'لَا',         None,   None,      'حرف نفي', 'Neither',        None),
    (2, 255, 9, 'تَأْخُذُهُ',  'أخذ',  'تَفْعُل', 'فعل مضارع', 'overtakes Him', 'تمسكه'),
    (2, 255, 10,'سِنَةٌ',      'وسن',  'فِعَة',   'اسم',    'drowsiness',     'النعاس الخفيف'),
    (2, 255, 11,'وَلَا',       None,   None,      'حرف نفي', 'nor',            None),
    (2, 255, 12,'نَوْمٌ',      'نوم',  'فَعْل',   'اسم',    'sleep',          'الغيبوبة التامة'),

    # ── Common high-frequency vocabulary words ──────────────────────────────
    (3, 18, 1, 'شَهِدَ',       'شهد',  'فَعِل',   'فعل ماض', 'Allah witnesses', 'أعلم ويُخبر'),
    (4, 36, 1, 'وَٱعْبُدُوا', 'عبد',  'اِفْعُلُوا', 'فعل أمر', 'Worship',     'أطيعوا وتذللوا'),
    (5, 1, 1,  'يَٰٓأَيُّهَا', None,  None,       'حرف نداء', 'O you who',    None),
    (5, 1, 2,  'ٱلَّذِينَ',   None,   None,      'اسم موصول', 'who',          None),
    (5, 1, 3,  'ءَامَنُوٓا',  'أمن',  'فَعَلُوا', 'فعل ماض', 'have believed', 'صدّقوا بقلوبهم'),
    (9, 51, 1, 'قُل',          'قول',  'فُعْل',   'فعل أمر', 'Say',           'بلِّغ'),
    (9, 51, 2, 'لَّن',         None,   None,      'حرف نفي', 'Never',         None),
    (9, 51, 3, 'يُصِيبَنَآ',   'صوب',  'يُفْعِلَنا', 'فعل مضارع', 'will befall us', 'لن يُصبنا'),
    (17, 44, 1,'تُسَبِّحُ',    'سبح',  'تُفَعِّل', 'فعل مضارع', 'glorify',    'ينزّهون'),
    (18, 10, 1,'إِذْ',         None,   None,      'ظرف',    'When',           'حين'),
    (20, 14, 1,'إِنَّنِىٓ',    None,   None,      'حرف توكيد', 'Indeed I',    None),
    (20, 14, 2,'أَنَا۠',       None,   None,      'ضمير',   'am',             None),
    (20, 14, 3,'ٱللَّهُ',      'أله',  None,      'اسم علم', 'Allah',          None),
    (20, 14, 4,'لَآ',          None,   None,      'حرف نفي', 'there is no',    None),
    (20, 14, 5,'إِلَٰهَ',      'أله',  'فِعَال',  'اسم',    'god',            'المعبود'),
    (20, 14, 6,'إِلَّآ',       None,   None,      'حرف استثناء', 'except',     None),
    (20, 14, 7,'أَنَا۠',       None,   None,      'ضمير',   'Me',             None),
    (20, 14, 8,'فَٱعْبُدْنِى', 'عبد',  'فَاعْبُدْنِي', 'فعل أمر', 'so worship Me', 'فاعبدني وحدي'),
    (33, 41, 1,'يَٰٓأَيُّهَا', None,   None,      'حرف نداء', 'O you who',    None),
    (33, 41, 2,'ٱلَّذِينَ',    None,   None,      'اسم موصول', 'who',         None),
    (33, 41, 3,'ءَامَنُوا',    'أمن',  'فَعَلُوا', 'فعل ماض', 'have believed', 'صدّقوا'),
    (33, 41, 4,'ٱذْكُرُوا',    'ذكر',  'اِفْعُلُوا', 'فعل أمر', 'remember',   'اذكروا بالقلب واللسان'),
    (33, 41, 5,'ٱللَّهَ',      'أله',  None,      'اسم علم', 'Allah',          None),
    (33, 41, 6,'ذِكْرًا',      'ذكر',  'فِعْل',   'اسم',    'abundantly',    'ذِكراً كثيراً'),
    (55, 1, 1, 'ٱلرَّحْمَٰنُ', 'رحم',  'فَعْلَان', 'اسم',   'The Most Gracious', 'اسم من أسماء الله'),
    (55, 2, 1, 'عَلَّمَ',      'علم',  'فَعَّل',  'فعل ماض', 'taught',        'علّم وأعلم'),
    (55, 2, 2, 'ٱلْقُرْءَانَ', 'قرأ',  'فُعْلَان', 'اسم',   'the Quran',     'المقروء المُعجِز'),
    (67, 1, 1, 'تَبَارَكَ',    'برك',  'تَفَاعَل', 'فعل ماض', 'Blessed is',  'تعاظمت بركاته'),
    (67, 1, 2, 'ٱلَّذِى',      None,   None,      'اسم موصول', 'He in Whose', None),
    (67, 1, 3, 'بِيَدِهِ',     'يدي',  'فِعْل',   'اسم',    'hand is',       'قدرته وسلطانه'),
    (67, 1, 4, 'ٱلْمُلْكُ',    'ملك',  'فُعْل',   'اسم',    'dominion',      'السلطة والسيادة'),
    (96, 1, 1, 'ٱقْرَأْ',      'قرأ',  'اِفْعَل', 'فعل أمر', 'Read',         'اتلُ واقرأ'),
    (96, 1, 2, 'بِٱسْمِ',      'سمو',  'فِعْل',   'حرف جر', 'in the name of', None),
    (96, 1, 3, 'رَبِّكَ',      'ربب',  'فَعِّل',  'اسم',    'your Lord',     'ربّك المدبّر لأمرك'),
    (96, 1, 4, 'ٱلَّذِى',      None,   None,      'اسم موصول', 'who',         None),
    (96, 1, 5, 'خَلَقَ',       'خلق',  'فَعَل',   'فعل ماض', 'created',      'أنشأ الأشياء من العدم'),
    (103, 1, 1,'وَٱلْعَصْرِ',  'عصر',  'فَعْل',   'اسم',    'By time',       'الوقت والدهر'),
    (103, 2, 1,'إِنَّ',        None,   None,      'حرف توكيد', 'Indeed',      None),
    (103, 2, 2,'ٱلْإِنسَٰنَ',  'أنس',  'فِعْلَان', 'اسم',   'mankind',       'كل إنسان'),
    (103, 2, 3,'لَفِى',        None,   None,      'حرف توكيد', 'is surely in', None),
    (103, 2, 4,'خُسْرٍ',       'خسر',  'فُعْل',   'اسم',    'loss',          'النقصان والهلاك'),
]

SOURCE_ID = 'quranic_arabic_corpus'


# ---------------------------------------------------------------------------
# QAC file parser (full dataset)
# ---------------------------------------------------------------------------

def _buckwalter_root_to_arabic(root_bw: str) -> str:
    """Convert a Buckwalter-encoded root to Arabic script.

    In QAC ROOT notation 'A' denotes the hamza radical in any position
    (Alh=أله, dAb=دأب, bdA=بدأ) — plain alef is never a root consonant,
    so 'A' maps to أ, not ا.
    """
    bw_map = {
        'A': 'أ', 'b': 'ب', 't': 'ت', 'v': 'ث', 'j': 'ج', 'H': 'ح',
        'x': 'خ', 'd': 'د', '*': 'ذ', 'r': 'ر', 'z': 'ز', 's': 'س',
        '$': 'ش', 'S': 'ص', 'D': 'ض', 'T': 'ط', 'Z': 'ظ', 'E': 'ع',
        'g': 'غ', 'f': 'ف', 'q': 'ق', 'k': 'ك', 'l': 'ل', 'm': 'م',
        'n': 'ن', 'h': 'ه', 'w': 'و', 'y': 'ي', 'Y': 'ى', 'p': 'ة',
        "'": 'ء', '>': 'أ', '<': 'إ', '{': 'ا', '&': 'ؤ', '}': 'ئ',
        'o': 'ْ',  # sukun — drop from roots
        'F': '',  # tanwin fath
        'N': '',  # tanwin kasra
        'K': '',  # tanwin damm
        'a': '',  # fatha
        'i': '',  # kasra
        'u': '',  # damma
        '~': '',  # shadda
        'o': '',  # sukun
    }
    return ''.join(bw_map.get(c, c) for c in root_bw)


def _qac_pos_to_arabic(tag: str, features: str) -> str:
    """Map QAC POS tag to our Arabic grammar label."""
    pos_map = {
        'N': 'اسم',
        'PN': 'اسم علم',
        'V': 'فعل',
        'P': 'حرف جر',
        'CONJ': 'حرف عطف',
        'PART': 'حرف',
        'T': 'حرف تعريف',
        'REL': 'اسم موصول',
        'DEM': 'اسم إشارة',
        'PRON': 'ضمير',
        'INTERJ': 'حرف نداء',
        'ADJ': 'اسم',
        'NUM': 'اسم',
    }
    # Prefer features POS over tag for verbs
    if 'POS:V' in features:
        asp = 'PERF' if 'ASP:PERF' in features else 'IMPF' if 'ASP:IMPF' in features else 'IMPV'
        return {'PERF': 'فعل ماض', 'IMPF': 'فعل مضارع', 'IMPV': 'فعل أمر'}.get(asp, 'فعل')
    return pos_map.get(tag, 'غير محدد')


def load_qac_file(path: Path) -> list[dict]:
    """
    Parse the QAC morphology TSV file and return a list of dicts suitable
    for bulk insertion into vocabulary_entries.

    Each STEM morpheme maps to one entry.  PREFIX/SUFFIX morphemes are skipped.
    """
    entries: list[dict] = []
    location_re = re.compile(r'\((\d+):(\d+):(\d+):(\d+)\)')

    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('LOCATION'):
                continue
            parts = line.split('\t')
            if len(parts) < 4:
                continue
            loc_str, form, tag, features = parts[0], parts[1], parts[2], parts[3]

            # Only process STEM morphemes (these carry the root).
            # In QAC 0.4 the features field STARTS with the morpheme type,
            # e.g. "STEM|POS:N|LEM:{som|ROOT:smw|M|GEN".
            if not features.startswith('STEM'):
                # PREFIX or SUFFIX — skip
                continue

            m = location_re.match(loc_str)
            if not m:
                continue
            sura_no, aya_no, word_pos, _seg = (int(x) for x in m.groups())

            root_bw = ''
            gloss_en = None
            for feat in features.split('|'):
                if feat.startswith('ROOT:'):
                    root_bw = feat[5:]
                elif feat.startswith('GLOSS:'):
                    gloss_en = feat[6:].replace('+', ' ')

            root_ar = _buckwalter_root_to_arabic(root_bw) if root_bw else None
            pos_ar = _qac_pos_to_arabic(tag, features)

            # Convert Buckwalter form to Arabic (QAC ships Buckwalter forms)
            # We store the Buckwalter form as-is; the UI will show Arabic from
            # our quran_uthmani table, not from here.
            entries.append({
                'sura_no': sura_no,
                'aya_no': aya_no,
                'word_position': word_pos,
                'word_ar': form,       # BW form — Arabic form comes from quran table
                'word_ar_bare': _strip_diacritics(form),
                'root_ar': root_ar,
                'pattern_ar': None,
                'pos_tag': pos_ar,
                'meaning_en': gloss_en,
                'meaning_ar': None,
                'source_id': SOURCE_ID,
            })

    # A word can have several STEM segments (e.g. vocative compounds).
    # ON CONFLICT cannot process duplicate keys within one INSERT, so keep
    # one entry per (sura, aya, word_position) — preferring the root-bearing
    # stem, which carries the lexical meaning.
    deduped: dict[tuple[int, int, int], dict] = {}
    for e in entries:
        key = (e['sura_no'], e['aya_no'], e['word_position'])
        prev = deduped.get(key)
        if prev is None or (prev['root_ar'] is None and e['root_ar'] is not None):
            deduped[key] = e

    return list(deduped.values())


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _build_seed_rows() -> list[dict]:
    rows = []
    for entry in _SEED:
        (sura_no, aya_no, word_pos,
         word_ar, root_ar, pattern_ar,
         pos_tag, meaning_en, meaning_ar) = entry
        rows.append({
            'sura_no': sura_no,
            'aya_no': aya_no,
            'word_position': word_pos,
            'word_ar': word_ar,
            'word_ar_bare': _strip_diacritics(word_ar),
            'root_ar': root_ar,
            'pattern_ar': pattern_ar,
            'pos_tag': pos_tag,
            'meaning_en': meaning_en,
            'meaning_ar': meaning_ar,
            'source_id': SOURCE_ID,
        })
    return rows


def _bulk_insert(session, rows: list[dict], curated: bool = False) -> int:
    """Upsert rows; on duplicate (sura, aya, word_position) merge fields.

    curated=False (bulk QAC file): enrich-only — morphology (root/pattern/pos)
    prefers the incoming QAC value, but meanings already in the DB (Mufradat
    Arabic meanings, curated glosses) are never overwritten.

    curated=True (built-in hand-verified seed): authoritative — incoming
    values win wherever present; NULLs never erase existing data.
    """
    if not rows:
        return 0
    from sqlalchemy import func
    stmt = pg_insert(VocabEntry).values(rows)
    if curated:
        set_ = {
            'root_ar': func.coalesce(stmt.excluded.root_ar, VocabEntry.root_ar),
            'pattern_ar': func.coalesce(stmt.excluded.pattern_ar, VocabEntry.pattern_ar),
            'pos_tag': func.coalesce(stmt.excluded.pos_tag, VocabEntry.pos_tag),
            'meaning_en': func.coalesce(stmt.excluded.meaning_en, VocabEntry.meaning_en),
            'meaning_ar': func.coalesce(stmt.excluded.meaning_ar, VocabEntry.meaning_ar),
            'source_id': stmt.excluded.source_id,
        }
    else:
        set_ = {
            'root_ar': func.coalesce(stmt.excluded.root_ar, VocabEntry.root_ar),
            'pattern_ar': func.coalesce(stmt.excluded.pattern_ar, VocabEntry.pattern_ar),
            'pos_tag': func.coalesce(stmt.excluded.pos_tag, VocabEntry.pos_tag),
            'meaning_en': func.coalesce(VocabEntry.meaning_en, stmt.excluded.meaning_en),
            'meaning_ar': func.coalesce(VocabEntry.meaning_ar, stmt.excluded.meaning_ar),
            'source_id': stmt.excluded.source_id,
        }
    stmt = stmt.on_conflict_do_update(
        index_elements=['sura_no', 'aya_no', 'word_position'],
        set_=set_,
    )
    result = session.execute(stmt)
    session.commit()
    return result.rowcount


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description='Seed Quranic vocabulary entries')
    parser.add_argument(
        '--qac-file',
        type=Path,
        default=None,
        help='Path to the QAC morphology TSV file for full load',
    )
    parser.add_argument('--dry-run', action='store_true', help='Parse only, do not write')
    args = parser.parse_args()

    session_gen = get_sync_session()
    session = next(session_gen)

    try:
        curated = not args.qac_file
        if args.qac_file:
            print(f'Loading full QAC data from {args.qac_file} ...')
            rows = load_qac_file(args.qac_file)
            print(f'  Parsed {len(rows):,} STEM morphemes')
        else:
            print('Loading built-in seed data (curated — authoritative) ...')
            rows = _build_seed_rows()
            print(f'  Prepared {len(rows)} seed entries')

        if args.dry_run:
            print('Dry run — no writes performed.')
            return

        # Batch insert in chunks of 1000
        total = 0
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            count = _bulk_insert(session, batch, curated=curated)
            total += count
            print(f'  Inserted/updated batch {i // batch_size + 1}: {count} rows')

        print(f'Done — {total:,} rows written to vocabulary_entries.')

    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


# Import here to avoid circular at top of file
from app.db.database import get_sync_session  # noqa: E402

if __name__ == '__main__':
    main()
