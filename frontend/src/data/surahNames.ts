// Compact surah name lookup — used throughout the UI to display human-readable
// surah names alongside bare ayah numbers (e.g. "24:44" → "An-Noor 24:44").
// Sourced from SURAH_ATLAS_DATA (same transliterations, simpler Arabic names).

export interface SurahNameEntry {
  ar: string;   // short Arabic name (no سُورَةُ prefix)
  en: string;   // English transliteration
}

// Index 0 = Surah 1 (Al-Faatiha), index 113 = Surah 114 (An-Naas)
export const SURAH_NAMES: readonly SurahNameEntry[] = [
  { ar: 'الفاتحة', en: 'Al-Faatiha' },
  { ar: 'البقرة', en: 'Al-Baqara' },
  { ar: 'آل عمران', en: 'Aal-i-Imraan' },
  { ar: 'النساء', en: 'An-Nisaa' },
  { ar: 'المائدة', en: 'Al-Maaida' },
  { ar: 'الأنعام', en: "Al-An'aam" },
  { ar: 'الأعراف', en: "Al-A'raaf" },
  { ar: 'الأنفال', en: 'Al-Anfaal' },
  { ar: 'التوبة', en: 'At-Tawba' },
  { ar: 'يونس', en: 'Yunus' },
  { ar: 'هود', en: 'Hud' },
  { ar: 'يوسف', en: 'Yusuf' },
  { ar: 'الرعد', en: "Ar-Ra'd" },
  { ar: 'إبراهيم', en: 'Ibrahim' },
  { ar: 'الحجر', en: 'Al-Hijr' },
  { ar: 'النحل', en: 'An-Nahl' },
  { ar: 'الإسراء', en: 'Al-Israa' },
  { ar: 'الكهف', en: 'Al-Kahf' },
  { ar: 'مريم', en: 'Maryam' },
  { ar: 'طه', en: 'Taa-Haa' },
  { ar: 'الأنبياء', en: 'Al-Anbiyaa' },
  { ar: 'الحج', en: 'Al-Hajj' },
  { ar: 'المؤمنون', en: 'Al-Muminoon' },
  { ar: 'النور', en: 'An-Noor' },
  { ar: 'الفرقان', en: 'Al-Furqaan' },
  { ar: 'الشعراء', en: "Ash-Shu'araa" },
  { ar: 'النمل', en: 'An-Naml' },
  { ar: 'القصص', en: 'Al-Qasas' },
  { ar: 'العنكبوت', en: 'Al-Ankaboot' },
  { ar: 'الروم', en: 'Ar-Room' },
  { ar: 'لقمان', en: 'Luqman' },
  { ar: 'السجدة', en: 'As-Sajda' },
  { ar: 'الأحزاب', en: 'Al-Ahzaab' },
  { ar: 'سبأ', en: 'Saba' },
  { ar: 'فاطر', en: 'Faatir' },
  { ar: 'يس', en: 'Yaseen' },
  { ar: 'الصافات', en: 'As-Saaffaat' },
  { ar: 'ص', en: 'Saad' },
  { ar: 'الزمر', en: 'Az-Zumar' },
  { ar: 'غافر', en: 'Ghafir' },
  { ar: 'فصلت', en: 'Fussilat' },
  { ar: 'الشورى', en: 'Ash-Shura' },
  { ar: 'الزخرف', en: 'Az-Zukhruf' },
  { ar: 'الدخان', en: 'Ad-Dukhaan' },
  { ar: 'الجاثية', en: 'Al-Jaathiya' },
  { ar: 'الأحقاف', en: 'Al-Ahqaf' },
  { ar: 'محمد', en: 'Muhammad' },
  { ar: 'الفتح', en: 'Al-Fath' },
  { ar: 'الحجرات', en: 'Al-Hujuraat' },
  { ar: 'ق', en: 'Qaaf' },
  { ar: 'الذاريات', en: 'Adh-Dhaariyat' },
  { ar: 'الطور', en: 'At-Tur' },
  { ar: 'النجم', en: 'An-Najm' },
  { ar: 'القمر', en: 'Al-Qamar' },
  { ar: 'الرحمن', en: 'Ar-Rahmaan' },
  { ar: 'الواقعة', en: 'Al-Waaqia' },
  { ar: 'الحديد', en: 'Al-Hadid' },
  { ar: 'المجادلة', en: 'Al-Mujaadila' },
  { ar: 'الحشر', en: 'Al-Hashr' },
  { ar: 'الممتحنة', en: 'Al-Mumtahana' },
  { ar: 'الصف', en: 'As-Saff' },
  { ar: 'الجمعة', en: "Al-Jumu'a" },
  { ar: 'المنافقون', en: 'Al-Munaafiqoon' },
  { ar: 'التغابن', en: 'At-Taghaabun' },
  { ar: 'الطلاق', en: 'At-Talaaq' },
  { ar: 'التحريم', en: 'At-Tahrim' },
  { ar: 'الملك', en: 'Al-Mulk' },
  { ar: 'القلم', en: 'Al-Qalam' },
  { ar: 'الحاقة', en: 'Al-Haaqqa' },
  { ar: 'المعارج', en: "Al-Ma'aarij" },
  { ar: 'نوح', en: 'Nooh' },
  { ar: 'الجن', en: 'Al-Jinn' },
  { ar: 'المزمل', en: 'Al-Muzzammil' },
  { ar: 'المدثر', en: 'Al-Muddaththir' },
  { ar: 'القيامة', en: 'Al-Qiyaama' },
  { ar: 'الإنسان', en: 'Al-Insaan' },
  { ar: 'المرسلات', en: 'Al-Mursalaat' },
  { ar: 'النبأ', en: 'An-Naba' },
  { ar: 'النازعات', en: "An-Naazi'aat" },
  { ar: 'عبس', en: 'Abasa' },
  { ar: 'التكوير', en: 'At-Takwir' },
  { ar: 'الانفطار', en: 'Al-Infitaar' },
  { ar: 'المطففين', en: 'Al-Mutaffifin' },
  { ar: 'الانشقاق', en: 'Al-Inshiqaaq' },
  { ar: 'البروج', en: 'Al-Burooj' },
  { ar: 'الطارق', en: 'At-Taariq' },
  { ar: 'الأعلى', en: "Al-A'laa" },
  { ar: 'الغاشية', en: 'Al-Ghaashiya' },
  { ar: 'الفجر', en: 'Al-Fajr' },
  { ar: 'البلد', en: 'Al-Balad' },
  { ar: 'الشمس', en: 'Ash-Shams' },
  { ar: 'الليل', en: 'Al-Lail' },
  { ar: 'الضحى', en: 'Ad-Dhuhaa' },
  { ar: 'الشرح', en: 'Ash-Sharh' },
  { ar: 'التين', en: 'At-Tin' },
  { ar: 'العلق', en: 'Al-Alaq' },
  { ar: 'القدر', en: 'Al-Qadr' },
  { ar: 'البينة', en: 'Al-Bayyina' },
  { ar: 'الزلزلة', en: 'Az-Zalzala' },
  { ar: 'العاديات', en: 'Al-Aadiyaat' },
  { ar: 'القارعة', en: "Al-Qaari'a" },
  { ar: 'التكاثر', en: 'At-Takaathur' },
  { ar: 'العصر', en: 'Al-Asr' },
  { ar: 'الهمزة', en: 'Al-Humaza' },
  { ar: 'الفيل', en: 'Al-Fil' },
  { ar: 'قريش', en: 'Quraish' },
  { ar: 'الماعون', en: "Al-Maa'un" },
  { ar: 'الكوثر', en: 'Al-Kawthar' },
  { ar: 'الكافرون', en: 'Al-Kaafiroon' },
  { ar: 'النصر', en: 'An-Nasr' },
  { ar: 'المسد', en: 'Al-Masad' },
  { ar: 'الإخلاص', en: 'Al-Ikhlaas' },
  { ar: 'الفلق', en: 'Al-Falaq' },
  { ar: 'الناس', en: 'An-Naas' },
] as const;

export function getSurahName(surahNo: number): SurahNameEntry {
  return SURAH_NAMES[surahNo - 1] ?? { ar: `سورة ${surahNo}`, en: `Surah ${surahNo}` };
}

/** Returns e.g. "An-Noor 24:44" (en) or "النور ٢٤:٤٤" (ar) */
export function formatVerseRef(surahNo: number, ayahNo: number, language: 'ar' | 'en'): string {
  const name = getSurahName(surahNo);
  if (language === 'ar') {
    return `${name.ar} ${surahNo}:${ayahNo}`;
  }
  return `${name.en} ${surahNo}:${ayahNo}`;
}

/** Compact badge label: "(Surah An-Noor)" for English, "(سورة النور)" for Arabic */
export function surahBadge(surahNo: number, language: 'ar' | 'en'): string {
  const name = getSurahName(surahNo);
  if (language === 'ar') {
    return `سورة ${name.ar}`;
  }
  return `Surah ${name.en}`;
}
