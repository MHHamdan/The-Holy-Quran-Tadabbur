"""
The 99 Names of Allah (أسماء الله الحسنى)

This module contains a comprehensive list of the 99 Beautiful Names of Allah,
sourced from authentic hadith and scholarly works including:
- Al-Maqsad al-Asna by Imam Al-Ghazali
- Tafsir Ibn Kathir
- Fath al-Bari by Ibn Hajar

Categories:
- dhat (الذات): Names relating to Allah's Essence
- jamal (الجمال): Names relating to Beauty, Mercy, and Grace
- jalal (الجلال): Names relating to Majesty, Power, and Authority
- kamal (الكمال): Names relating to Perfection
- af'al (الأفعال): Names relating to Allah's Actions
"""

from typing import List, TypedDict


class AllahName(TypedDict):
    """Type definition for an Allah name entry."""
    number: int
    name_ar: str  # With tashkeel
    name_simple: str  # Without diacritics for search
    transliteration: str
    meaning_en: str
    meaning_ar: str
    description_ar: str
    description_en: str
    category: str  # dhat, jamal, jalal, kamal, af'al


ALLAH_NAMES_99: List[AllahName] = [
    {
        "number": 1,
        "name_ar": "الرَّحْمَنُ",
        "name_simple": "الرحمن",
        "transliteration": "Ar-Rahman",
        "meaning_en": "The Most Gracious",
        "meaning_ar": "ذو الرحمة الواسعة التي وسعت كل شيء",
        "description_ar": "الرحمن: اسم خاص بالله تعالى لا يُسمى به غيره، يدل على سعة رحمته التي وسعت كل شيء. وهي رحمة عامة تشمل جميع الخلق في الدنيا، المؤمن والكافر، الإنسان والحيوان.",
        "description_en": "Ar-Rahman: A name exclusive to Allah, indicating His vast mercy that encompasses all things. This is a general mercy that includes all creation in this world - believers and disbelievers, humans and animals alike.",
        "category": "jamal"
    },
    {
        "number": 2,
        "name_ar": "الرَّحِيمُ",
        "name_simple": "الرحيم",
        "transliteration": "Ar-Raheem",
        "meaning_en": "The Most Merciful",
        "meaning_ar": "ذو الرحمة الخاصة بالمؤمنين",
        "description_ar": "الرحيم: يدل على رحمة خاصة بالمؤمنين يوم القيامة، فهو رحيم بهم في الآخرة بإدخالهم الجنة والنجاة من النار. قال تعالى: {وَكَانَ بِالْمُؤْمِنِينَ رَحِيمًا}.",
        "description_en": "Ar-Raheem: Indicates a special mercy for the believers on the Day of Judgment. He is merciful to them in the Hereafter by admitting them to Paradise and saving them from the Fire. Allah says: 'And He is ever Merciful to the believers.'",
        "category": "jamal"
    },
    {
        "number": 3,
        "name_ar": "المَلِكُ",
        "name_simple": "الملك",
        "transliteration": "Al-Malik",
        "meaning_en": "The King",
        "meaning_ar": "المالك لكل شيء المتصرف فيه",
        "description_ar": "الملك: هو المالك الحقيقي لكل شيء، المتصرف في ملكه كيف يشاء، لا معقب لحكمه ولا راد لقضائه. ملكه كامل لا نقص فيه، باقٍ لا يزول.",
        "description_en": "Al-Malik: The true King and Owner of all things, who disposes of His kingdom as He wills. None can overturn His judgment or repel His decree. His sovereignty is complete without deficiency, everlasting without decline.",
        "category": "jalal"
    },
    {
        "number": 4,
        "name_ar": "القُدُّوسُ",
        "name_simple": "القدوس",
        "transliteration": "Al-Quddus",
        "meaning_en": "The Most Holy",
        "meaning_ar": "المنزه عن كل نقص وعيب",
        "description_ar": "القدوس: المنزه عن كل عيب ونقص، المطهر عن كل ما لا يليق بجلاله. تُسبح له الملائكة وتقدسه. قال تعالى: {وَنَحْنُ نُسَبِّحُ بِحَمْدِكَ وَنُقَدِّسُ لَكَ}.",
        "description_en": "Al-Quddus: The One purified from all imperfection and deficiency, free from anything unbefitting His majesty. The angels glorify and sanctify Him. Allah quotes them: 'While we glorify You with Your praise and sanctify You.'",
        "category": "dhat"
    },
    {
        "number": 5,
        "name_ar": "السَّلَامُ",
        "name_simple": "السلام",
        "transliteration": "As-Salam",
        "meaning_en": "The Source of Peace",
        "meaning_ar": "السالم من كل نقص، ومنه السلامة",
        "description_ar": "السلام: السالم من كل عيب ونقص، وهو مصدر السلام والأمان لخلقه. يُسلم على عباده في الجنة، وتحيتهم فيها سلام.",
        "description_en": "As-Salam: The One free from all defects and imperfections, and the source of peace and security for His creation. He will greet His servants in Paradise, and their greeting therein will be peace.",
        "category": "dhat"
    },
    {
        "number": 6,
        "name_ar": "المُؤْمِنُ",
        "name_simple": "المؤمن",
        "transliteration": "Al-Mu'min",
        "meaning_en": "The Granter of Security",
        "meaning_ar": "الذي يؤمّن خلقه من الظلم",
        "description_ar": "المؤمن: الذي يؤمّن خلقه من ظلمه، ويؤمّن عباده المؤمنين من عذابه، والمصدق لرسله بالمعجزات.",
        "description_en": "Al-Mu'min: The One who grants security to His creation from His oppression, secures His believing servants from His punishment, and confirms His messengers with miracles.",
        "category": "jamal"
    },
    {
        "number": 7,
        "name_ar": "المُهَيْمِنُ",
        "name_simple": "المهيمن",
        "transliteration": "Al-Muhaymin",
        "meaning_en": "The Guardian",
        "meaning_ar": "الرقيب الحافظ على كل شيء",
        "description_ar": "المهيمن: الرقيب الحافظ لكل شيء، الشاهد على خلقه بأعمالهم، المطلع على كل أمورهم.",
        "description_en": "Al-Muhaymin: The Guardian and Protector of all things, the Witness over His creation regarding their deeds, fully aware of all their affairs.",
        "category": "jalal"
    },
    {
        "number": 8,
        "name_ar": "العَزِيزُ",
        "name_simple": "العزيز",
        "transliteration": "Al-Aziz",
        "meaning_en": "The Almighty",
        "meaning_ar": "الغالب الذي لا يُغلب",
        "description_ar": "العزيز: الغالب الذي لا يُغلب، القوي الذي لا يُقهر، المنيع الجانب الذي لا يُنال. عزته كاملة مطلقة، من عز به عز، ومن اعتز بغيره ذل.",
        "description_en": "Al-Aziz: The Almighty who cannot be overcome, the Strong who cannot be subdued, the Invincible whose side cannot be reached. His might is complete and absolute; whoever seeks honor through Him will be honored.",
        "category": "jalal"
    },
    {
        "number": 9,
        "name_ar": "الجَبَّارُ",
        "name_simple": "الجبار",
        "transliteration": "Al-Jabbar",
        "meaning_en": "The Compeller",
        "meaning_ar": "القاهر لخلقه، جابر القلوب",
        "description_ar": "الجبار: له ثلاثة معانٍ: جبار القوة والسلطان الذي يقهر الجبابرة، وجابر القلوب المكسورة، والعلي فوق خلقه لا يناله شيء.",
        "description_en": "Al-Jabbar: Has three meanings: The Compeller of might and authority who subdues tyrants, the Mender of broken hearts, and the Exalted above His creation whom nothing can reach.",
        "category": "jalal"
    },
    {
        "number": 10,
        "name_ar": "المُتَكَبِّرُ",
        "name_simple": "المتكبر",
        "transliteration": "Al-Mutakabbir",
        "meaning_en": "The Supreme",
        "meaning_ar": "المتعالي عن صفات الخلق",
        "description_ar": "المتكبر: المتعالي عن صفات الخلق، العظيم الذي له الكبرياء في السماوات والأرض. الكبرياء صفة له وحده لا تليق بغيره.",
        "description_en": "Al-Mutakabbir: The Supreme, exalted above the attributes of creation. The Great One to whom belongs all grandeur in the heavens and earth. Grandeur is an attribute befitting Him alone.",
        "category": "jalal"
    },
    {
        "number": 11,
        "name_ar": "الخَالِقُ",
        "name_simple": "الخالق",
        "transliteration": "Al-Khaliq",
        "meaning_en": "The Creator",
        "meaning_ar": "الذي خلق كل شيء من العدم",
        "description_ar": "الخالق: الذي أوجد جميع المخلوقات من العدم، وقدّر خلقها قبل إيجادها. خلق كل شيء فأحسن خلقه وأتقنه.",
        "description_en": "Al-Khaliq: The One who brought all creatures into existence from nothing, having predetermined their creation. He created everything and perfected its creation.",
        "category": "af'al"
    },
    {
        "number": 12,
        "name_ar": "البَارِئُ",
        "name_simple": "البارئ",
        "transliteration": "Al-Bari'",
        "meaning_en": "The Originator",
        "meaning_ar": "المُبدع للخلق على غير مثال سابق",
        "description_ar": "البارئ: الذي برأ الخلق وأوجدهم على صور مختلفة، بريئين من التفاوت والنقص، على غير مثال سابق.",
        "description_en": "Al-Bari': The One who originates creation in different forms, free from disparity and deficiency, without any prior model.",
        "category": "af'al"
    },
    {
        "number": 13,
        "name_ar": "المُصَوِّرُ",
        "name_simple": "المصور",
        "transliteration": "Al-Musawwir",
        "meaning_en": "The Fashioner",
        "meaning_ar": "الذي صور المخلوقات كيف شاء",
        "description_ar": "المصور: الذي صور جميع الموجودات ورتبها، وأعطى كل شيء صورته الخاصة وهيئته المميزة التي ينفرد بها.",
        "description_en": "Al-Musawwir: The One who fashioned all beings and arranged them, giving each thing its unique form and distinctive appearance.",
        "category": "af'al"
    },
    {
        "number": 14,
        "name_ar": "الغَفَّارُ",
        "name_simple": "الغفار",
        "transliteration": "Al-Ghaffar",
        "meaning_en": "The Oft-Forgiving",
        "meaning_ar": "كثير المغفرة والستر للذنوب",
        "description_ar": "الغفار: كثير المغفرة والستر للذنوب، يغفر الذنوب مرة بعد مرة، ويستر العيوب ولا يفضح صاحبها. صيغة مبالغة تدل على كثرة المغفرة.",
        "description_en": "Al-Ghaffar: The One who forgives abundantly and conceals sins, forgiving sins time after time, covering faults without exposing their doers. An intensive form indicating abundant forgiveness.",
        "category": "jamal"
    },
    {
        "number": 15,
        "name_ar": "القَهَّارُ",
        "name_simple": "القهار",
        "transliteration": "Al-Qahhar",
        "meaning_en": "The Subduer",
        "meaning_ar": "الذي قهر كل شيء وخضع له",
        "description_ar": "القهار: الذي قهر جميع الكائنات وأذعن له كل مخلوق، القاهر فوق عباده. قهر الجبارين بجبروته، والعتاة بقوته.",
        "description_en": "Al-Qahhar: The One who has subdued all beings and to whom every creature submits. The Dominant over His servants. He subdues tyrants with His might and rebels with His power.",
        "category": "jalal"
    },
    {
        "number": 16,
        "name_ar": "الوَهَّابُ",
        "name_simple": "الوهاب",
        "transliteration": "Al-Wahhab",
        "meaning_en": "The Bestower",
        "meaning_ar": "كثير العطاء والهبات",
        "description_ar": "الوهاب: كثير الهبات والعطاء، يعطي بلا عوض ولا سبب، عطاؤه لا ينقطع ولا ينفد. يهب لمن يشاء ما يشاء.",
        "description_en": "Al-Wahhab: The One who gives abundantly without compensation or cause. His giving never ceases or depletes. He bestows upon whom He wills whatever He wills.",
        "category": "jamal"
    },
    {
        "number": 17,
        "name_ar": "الرَّزَّاقُ",
        "name_simple": "الرزاق",
        "transliteration": "Ar-Razzaq",
        "meaning_en": "The Provider",
        "meaning_ar": "الذي يرزق جميع الخلق",
        "description_ar": "الرزاق: الذي تكفل بأرزاق جميع المخلوقات وأوصلها إليهم، ظاهرها وباطنها. ما من دابة في الأرض إلا على الله رزقها.",
        "description_en": "Ar-Razzaq: The One who guarantees the sustenance of all creatures and delivers it to them, both apparent and hidden. There is no creature on earth except that Allah provides for it.",
        "category": "jamal"
    },
    {
        "number": 18,
        "name_ar": "الفَتَّاحُ",
        "name_simple": "الفتاح",
        "transliteration": "Al-Fattah",
        "meaning_en": "The Opener",
        "meaning_ar": "الذي يفتح أبواب الرحمة والرزق",
        "description_ar": "الفتاح: الذي يفتح خزائن رحمته، ويفتح المغلق من أمور عباده، ويحكم بينهم بالحق. يفتح أبواب الرزق والفهم والعلم.",
        "description_en": "Al-Fattah: The One who opens the treasures of His mercy, opens the closed matters of His servants, and judges between them with truth. He opens doors of provision, understanding, and knowledge.",
        "category": "af'al"
    },
    {
        "number": 19,
        "name_ar": "العَلِيمُ",
        "name_simple": "العليم",
        "transliteration": "Al-Alim",
        "meaning_en": "The All-Knowing",
        "meaning_ar": "المحيط علمه بكل شيء",
        "description_ar": "العليم: الذي أحاط علمه بكل شيء ظاهراً وباطناً، دقيقاً وجليلاً، أولاً وآخراً. لا يعزب عن علمه مثقال ذرة في السماوات ولا في الأرض.",
        "description_en": "Al-Alim: The One whose knowledge encompasses all things, apparent and hidden, minute and great, first and last. Not even the weight of an atom escapes His knowledge in the heavens or earth.",
        "category": "dhat"
    },
    {
        "number": 20,
        "name_ar": "القَابِضُ",
        "name_simple": "القابض",
        "transliteration": "Al-Qabid",
        "meaning_en": "The Withholder",
        "meaning_ar": "الذي يقبض الأرزاق بحكمته",
        "description_ar": "القابض: الذي يقبض الأرزاق عن من يشاء بحكمته، ويقبض الأرواح عند الممات. قبضه رحمة وإن بدا غير ذلك.",
        "description_en": "Al-Qabid: The One who withholds provisions from whom He wills in His wisdom, and takes souls at death. His withholding is mercy even if it may appear otherwise.",
        "category": "af'al"
    },
    {
        "number": 21,
        "name_ar": "البَاسِطُ",
        "name_simple": "الباسط",
        "transliteration": "Al-Basit",
        "meaning_en": "The Expander",
        "meaning_ar": "الذي يوسع الرزق لمن يشاء",
        "description_ar": "الباسط: الذي يبسط الرزق لمن يشاء من عباده ويوسعه عليهم. القابض الباسط يقترنان، فهو يقبض ويبسط بحكمته.",
        "description_en": "Al-Basit: The One who expands provision for whom He wills among His servants. Al-Qabid and Al-Basit are paired; He withholds and expands in His wisdom.",
        "category": "af'al"
    },
    {
        "number": 22,
        "name_ar": "الخَافِضُ",
        "name_simple": "الخافض",
        "transliteration": "Al-Khafid",
        "meaning_en": "The Abaser",
        "meaning_ar": "الذي يخفض الجبابرة والمتكبرين",
        "description_ar": "الخافض: الذي يخفض الجبارين ويذلهم، ويضع من شاء من خلقه بحكمته. يخفض الكافرين بالإبعاد والإهانة.",
        "description_en": "Al-Khafid: The One who lowers tyrants and humbles them, and abases whom He wills among His creation in His wisdom. He lowers the disbelievers through rejection and humiliation.",
        "category": "af'al"
    },
    {
        "number": 23,
        "name_ar": "الرَّافِعُ",
        "name_simple": "الرافع",
        "transliteration": "Ar-Rafi",
        "meaning_en": "The Exalter",
        "meaning_ar": "الذي يرفع أولياءه بالنصر والتأييد",
        "description_ar": "الرافع: الذي يرفع المؤمنين بالطاعة، ويرفع أولياءه بالنصر والتأييد. يرفع من يشاء بفضله ويضع من يشاء بعدله.",
        "description_en": "Ar-Rafi: The One who elevates believers through obedience, and raises His allies with victory and support. He elevates whom He wills by His grace and lowers whom He wills by His justice.",
        "category": "af'al"
    },
    {
        "number": 24,
        "name_ar": "المُعِزُّ",
        "name_simple": "المعز",
        "transliteration": "Al-Mu'izz",
        "meaning_en": "The Bestower of Honor",
        "meaning_ar": "الذي يعز من يشاء",
        "description_ar": "المعز: الذي يعز من يشاء من عباده، ويهب العزة لمن يستحقها. العزة لله جميعاً، ومن أراد العزة فليطلبها من الله.",
        "description_en": "Al-Mu'izz: The One who grants honor to whom He wills among His servants, bestowing honor upon those who deserve it. All honor belongs to Allah; whoever seeks honor should seek it from Allah.",
        "category": "af'al"
    },
    {
        "number": 25,
        "name_ar": "المُذِلُّ",
        "name_simple": "المذل",
        "transliteration": "Al-Mudhill",
        "meaning_en": "The Humiliator",
        "meaning_ar": "الذي يذل من يشاء من المتكبرين",
        "description_ar": "المذل: الذي يذل من يشاء من المتكبرين والجبارين بعدله. يذل من عصاه ويهينه بالحرمان من كرامته.",
        "description_en": "Al-Mudhill: The One who humiliates whom He wills among the arrogant and tyrants by His justice. He humiliates those who disobey Him and disgraces them by depriving them of His honor.",
        "category": "af'al"
    },
    {
        "number": 26,
        "name_ar": "السَّمِيعُ",
        "name_simple": "السميع",
        "transliteration": "As-Sami",
        "meaning_en": "The All-Hearing",
        "meaning_ar": "الذي يسمع كل شيء",
        "description_ar": "السميع: الذي وسع سمعه جميع الأصوات، يسمع السر والنجوى، ولا يخفى عليه شيء. يسمع دعاء الداعين ويستجيب لهم.",
        "description_en": "As-Sami: The One whose hearing encompasses all sounds, who hears secrets and private conversations, from whom nothing is hidden. He hears the supplication of those who call upon Him and responds to them.",
        "category": "dhat"
    },
    {
        "number": 27,
        "name_ar": "البَصِيرُ",
        "name_simple": "البصير",
        "transliteration": "Al-Basir",
        "meaning_en": "The All-Seeing",
        "meaning_ar": "الذي يبصر كل شيء",
        "description_ar": "البصير: الذي يرى كل شيء وإن دق وخفي، يرى دبيب النملة السوداء على الصخرة الصماء في الليلة الظلماء.",
        "description_en": "Al-Basir: The One who sees all things, however minute or hidden. He sees the crawling of a black ant on a black rock in the darkness of night.",
        "category": "dhat"
    },
    {
        "number": 28,
        "name_ar": "الحَكَمُ",
        "name_simple": "الحكم",
        "transliteration": "Al-Hakam",
        "meaning_en": "The Judge",
        "meaning_ar": "الحاكم بين خلقه بالعدل",
        "description_ar": "الحكم: الحاكم بين خلقه بالحق والعدل، الذي لا يجور في حكمه ولا يظلم. إليه يُرجع الأمر كله في الدنيا والآخرة.",
        "description_en": "Al-Hakam: The Judge between His creation with truth and justice, who never wrongs in His judgment. To Him all matters return in this world and the Hereafter.",
        "category": "jalal"
    },
    {
        "number": 29,
        "name_ar": "العَدْلُ",
        "name_simple": "العدل",
        "transliteration": "Al-Adl",
        "meaning_en": "The Just",
        "meaning_ar": "العادل الذي لا يظلم",
        "description_ar": "العدل: العادل في حكمه، المنزه عن الظلم والجور، لا يظلم مثقال ذرة. حرّم الظلم على نفسه وجعله بين عباده محرماً.",
        "description_en": "Al-Adl: The Just in His judgment, free from oppression and tyranny, who does not wrong even by an atom's weight. He has forbidden oppression for Himself and made it forbidden among His servants.",
        "category": "kamal"
    },
    {
        "number": 30,
        "name_ar": "اللَّطِيفُ",
        "name_simple": "اللطيف",
        "transliteration": "Al-Latif",
        "meaning_en": "The Subtle One",
        "meaning_ar": "العليم بدقائق الأمور الرفيق بعباده",
        "description_ar": "اللطيف: له معنيان: العليم بدقائق الأمور وخفاياها، والرفيق بعباده الذي يوصل إليهم مصالحهم بلطف من حيث لا يشعرون.",
        "description_en": "Al-Latif: Has two meanings: The One who knows the subtleties of matters and their secrets, and the Gentle with His servants who brings them their benefits kindly without them realizing.",
        "category": "jamal"
    },
    {
        "number": 31,
        "name_ar": "الخَبِيرُ",
        "name_simple": "الخبير",
        "transliteration": "Al-Khabir",
        "meaning_en": "The All-Aware",
        "meaning_ar": "العليم ببواطن الأمور",
        "description_ar": "الخبير: العليم بكنه الأشياء وحقائقها، المطلع على بواطن الأمور وخفاياها. لا تخفى عليه خافية من أمور عباده.",
        "description_en": "Al-Khabir: The One who knows the essence and reality of all things, aware of the inner dimensions of matters and their secrets. No hidden affair of His servants is concealed from Him.",
        "category": "dhat"
    },
    {
        "number": 32,
        "name_ar": "الحَلِيمُ",
        "name_simple": "الحليم",
        "transliteration": "Al-Halim",
        "meaning_en": "The Forbearing",
        "meaning_ar": "الذي يمهل ولا يعجل بالعقوبة",
        "description_ar": "الحليم: الذي لا يستخفه عصيان العاصين، ولا يستفزه جهل الجاهلين، يمهل ولا يهمل، يؤخر العقوبة ليتوب العبد.",
        "description_en": "Al-Halim: The One not provoked by the disobedience of sinners nor disturbed by the ignorance of the ignorant. He gives respite but does not neglect; He delays punishment so the servant may repent.",
        "category": "jamal"
    },
    {
        "number": 33,
        "name_ar": "العَظِيمُ",
        "name_simple": "العظيم",
        "transliteration": "Al-Azim",
        "meaning_en": "The Magnificent",
        "meaning_ar": "ذو العظمة والكبرياء",
        "description_ar": "العظيم: ذو العظمة الكاملة في ذاته وصفاته وأفعاله، لا تحيط به العقول ولا تدركه الأفهام. عظيم لا يُحد ولا يُكيف.",
        "description_en": "Al-Azim: The One of complete magnificence in His essence, attributes, and actions. Minds cannot encompass Him nor can understanding grasp Him. Magnificent beyond limits or description.",
        "category": "dhat"
    },
    {
        "number": 34,
        "name_ar": "الغَفُورُ",
        "name_simple": "الغفور",
        "transliteration": "Al-Ghafur",
        "meaning_en": "The All-Forgiving",
        "meaning_ar": "واسع المغفرة",
        "description_ar": "الغفور: واسع المغفرة، يغفر الذنوب العظيمة ويسترها. يتجاوز عن السيئات ويمحوها. باب مغفرته مفتوح لكل تائب.",
        "description_en": "Al-Ghafur: Vast in forgiveness, who forgives great sins and conceals them. He pardons misdeeds and erases them. The door of His forgiveness is open to every penitent.",
        "category": "jamal"
    },
    {
        "number": 35,
        "name_ar": "الشَّكُورُ",
        "name_simple": "الشكور",
        "transliteration": "Ash-Shakur",
        "meaning_en": "The Appreciative",
        "meaning_ar": "الذي يشكر القليل ويعطي الكثير",
        "description_ar": "الشكور: الذي يشكر العمل القليل فيثيب عليه الثواب الجزيل، ويعفو عن الكثير من الذنوب. يضاعف الحسنات أضعافاً مضاعفة.",
        "description_en": "Ash-Shakur: The One who appreciates little work and rewards it greatly, while pardoning many sins. He multiplies good deeds manifold.",
        "category": "jamal"
    },
    {
        "number": 36,
        "name_ar": "العَلِيُّ",
        "name_simple": "العلي",
        "transliteration": "Al-Aliyy",
        "meaning_en": "The Most High",
        "meaning_ar": "المتعالي عن خلقه",
        "description_ar": "العلي: العالي فوق خلقه بذاته، المتعالي عن صفات المخلوقين، العالي القدر والمنزلة. له العلو المطلق من كل وجه.",
        "description_en": "Al-Aliyy: The Exalted above His creation in His essence, transcendent above the attributes of created beings, high in status and rank. His is absolute highness in every respect.",
        "category": "dhat"
    },
    {
        "number": 37,
        "name_ar": "الكَبِيرُ",
        "name_simple": "الكبير",
        "transliteration": "Al-Kabir",
        "meaning_en": "The Great",
        "meaning_ar": "العظيم الكبير في ذاته وصفاته",
        "description_ar": "الكبير: الكبير في ذاته وصفاته، الذي كل شيء دونه صغير، وكل عظيم عند عظمته حقير.",
        "description_en": "Al-Kabir: The Great in His essence and attributes, before whom everything else is small, and every great thing is insignificant compared to His greatness.",
        "category": "dhat"
    },
    {
        "number": 38,
        "name_ar": "الحَفِيظُ",
        "name_simple": "الحفيظ",
        "transliteration": "Al-Hafiz",
        "meaning_en": "The Preserver",
        "meaning_ar": "الحافظ لكل شيء",
        "description_ar": "الحفيظ: الحافظ للسماوات والأرض وما فيهما، الحافظ لأعمال العباد حتى يجازيهم، الحافظ لأوليائه من الوقوع في الذنوب.",
        "description_en": "Al-Hafiz: The Preserver of the heavens and earth and all within them, who preserves the deeds of servants to recompense them, and guards His allies from falling into sins.",
        "category": "af'al"
    },
    {
        "number": 39,
        "name_ar": "المُقِيتُ",
        "name_simple": "المقيت",
        "transliteration": "Al-Muqit",
        "meaning_en": "The Sustainer",
        "meaning_ar": "المقتدر على الإطعام وإيصال القوت",
        "description_ar": "المقيت: خالق الأقوات ومُقدرها وموصلها إلى الأبدان، الحفيظ الشهيد، المقتدر على كل شيء.",
        "description_en": "Al-Muqit: The Creator of sustenance, who apportions it and delivers it to bodies. The Guardian and Witness, capable of all things.",
        "category": "af'al"
    },
    {
        "number": 40,
        "name_ar": "الحَسِيبُ",
        "name_simple": "الحسيب",
        "transliteration": "Al-Hasib",
        "meaning_en": "The Reckoner",
        "meaning_ar": "الكافي لعباده المحاسب لهم",
        "description_ar": "الحسيب: الكافي لمن توكل عليه، المحاسب لخلقه على أعمالهم. يحصي كل شيء ويعده، لا تخفى عليه من أعمالهم خافية.",
        "description_en": "Al-Hasib: The Sufficient for those who rely on Him, who will account His creation for their deeds. He counts and records everything; no deed of theirs is hidden from Him.",
        "category": "af'al"
    },
    {
        "number": 41,
        "name_ar": "الجَلِيلُ",
        "name_simple": "الجليل",
        "transliteration": "Al-Jalil",
        "meaning_en": "The Majestic",
        "meaning_ar": "العظيم الموصوف بالجلال",
        "description_ar": "الجليل: العظيم الموصوف بصفات الجلال والكمال، الذي يُجل أن يُدرك كيف هو. له جلال العزة والملكوت.",
        "description_en": "Al-Jalil: The Great One described with attributes of majesty and perfection, too exalted to be comprehended. His is the majesty of might and dominion.",
        "category": "jalal"
    },
    {
        "number": 42,
        "name_ar": "الكَرِيمُ",
        "name_simple": "الكريم",
        "transliteration": "Al-Karim",
        "meaning_en": "The Generous",
        "meaning_ar": "الكثير الخير والجود",
        "description_ar": "الكريم: الكثير الخير، الجواد المعطي الذي لا ينفد عطاؤه، يعطي من سأله ومن لم يسأله. كريم يعفو عمن أساء إليه.",
        "description_en": "Al-Karim: The Abundant in goodness, the Generous Giver whose giving never depletes. He gives to those who ask and those who don't. Generous in pardoning those who wrong Him.",
        "category": "jamal"
    },
    {
        "number": 43,
        "name_ar": "الرَّقِيبُ",
        "name_simple": "الرقيب",
        "transliteration": "Ar-Raqib",
        "meaning_en": "The Watchful",
        "meaning_ar": "الذي لا يغفل عن شيء",
        "description_ar": "الرقيب: الذي لا يغفل عن شيء، يراقب أحوال العباد ويحصي أعمالهم. رقيب على كل نفس بما كسبت.",
        "description_en": "Ar-Raqib: The One who is never heedless of anything, who watches over the states of servants and records their deeds. A Watcher over every soul for what it has earned.",
        "category": "dhat"
    },
    {
        "number": 44,
        "name_ar": "المُجِيبُ",
        "name_simple": "المجيب",
        "transliteration": "Al-Mujib",
        "meaning_en": "The Responsive",
        "meaning_ar": "الذي يجيب دعوة الداعي",
        "description_ar": "المجيب: الذي يجيب المضطر إذا دعاه، ويقبل على الطائع إذا ناداه. قريب يجيب دعوة الداعي إذا دعاه.",
        "description_en": "Al-Mujib: The One who answers the distressed when they call upon Him, and accepts the obedient when they invoke Him. Near, answering the call of the caller when they call.",
        "category": "jamal"
    },
    {
        "number": 45,
        "name_ar": "الوَاسِعُ",
        "name_simple": "الواسع",
        "transliteration": "Al-Wasi",
        "meaning_en": "The All-Encompassing",
        "meaning_ar": "الذي وسعت رحمته كل شيء",
        "description_ar": "الواسع: الذي وسع رزقه جميع خلقه، ووسعت رحمته كل شيء، ووسع علمه كل شيء. واسع الفضل والإحسان.",
        "description_en": "Al-Wasi: The One whose provision encompasses all His creation, whose mercy encompasses all things, and whose knowledge encompasses all things. Vast in bounty and goodness.",
        "category": "dhat"
    },
    {
        "number": 46,
        "name_ar": "الحَكِيمُ",
        "name_simple": "الحكيم",
        "transliteration": "Al-Hakim",
        "meaning_en": "The All-Wise",
        "meaning_ar": "ذو الحكمة البالغة",
        "description_ar": "الحكيم: ذو الحكمة البالغة في خلقه وأمره، الذي يضع الأشياء في مواضعها. أحكم كل شيء خلقه وأتقنه.",
        "description_en": "Al-Hakim: The One of complete wisdom in His creation and command, who places things in their proper places. He perfected everything He created and made it precise.",
        "category": "kamal"
    },
    {
        "number": 47,
        "name_ar": "الوَدُودُ",
        "name_simple": "الودود",
        "transliteration": "Al-Wadud",
        "meaning_en": "The Most Loving",
        "meaning_ar": "المحب لعباده الصالحين",
        "description_ar": "الودود: المحب لعباده المؤمنين، المحبوب في قلوبهم. يحبهم ويحبونه، ود يفيض على المطيعين.",
        "description_en": "Al-Wadud: The Loving of His believing servants, beloved in their hearts. He loves them and they love Him, with affection overflowing upon the obedient.",
        "category": "jamal"
    },
    {
        "number": 48,
        "name_ar": "المَجِيدُ",
        "name_simple": "المجيد",
        "transliteration": "Al-Majid",
        "meaning_en": "The Glorious",
        "meaning_ar": "الشريف العظيم المجد",
        "description_ar": "المجيد: الشريف الذاتوالصفات، الواسع الكرم والجود، العظيم القدر. جمع بين العظمة والكرم والإحسان.",
        "description_en": "Al-Majid: The Noble in essence and attributes, vast in generosity and giving, great in status. He combines greatness, generosity, and benevolence.",
        "category": "jalal"
    },
    {
        "number": 49,
        "name_ar": "البَاعِثُ",
        "name_simple": "الباعث",
        "transliteration": "Al-Ba'ith",
        "meaning_en": "The Resurrector",
        "meaning_ar": "الذي يبعث الخلق يوم القيامة",
        "description_ar": "الباعث: الذي يبعث الخلق من قبورهم للحساب، ويبعث الرسل للهداية. يبعث الموتى ويعيدهم كما بدأهم.",
        "description_en": "Al-Ba'ith: The One who will resurrect creation from their graves for judgment, and who sends messengers for guidance. He raises the dead and returns them as He originated them.",
        "category": "af'al"
    },
    {
        "number": 50,
        "name_ar": "الشَّهِيدُ",
        "name_simple": "الشهيد",
        "transliteration": "Ash-Shahid",
        "meaning_en": "The Witness",
        "meaning_ar": "المطلع على كل شيء",
        "description_ar": "الشهيد: الذي لا يغيب عنه شيء، يشهد كل شيء ويعلمه. شاهد على عباده بأعمالهم، حاضر لا يغيب.",
        "description_en": "Ash-Shahid: The One from whom nothing is absent, who witnesses and knows all things. A witness over His servants regarding their deeds, ever-present, never absent.",
        "category": "dhat"
    },
    {
        "number": 51,
        "name_ar": "الحَقُّ",
        "name_simple": "الحق",
        "transliteration": "Al-Haqq",
        "meaning_en": "The Truth",
        "meaning_ar": "الموجود حقاً، الثابت الوجود",
        "description_ar": "الحق: الموجود حقاً، الثابت وجوده، الذي لا يزول. كلامه حق، ووعده حق، ولقاؤه حق، وجنته حق، وناره حق.",
        "description_en": "Al-Haqq: The One who truly exists, whose existence is established and never ceases. His word is true, His promise is true, meeting Him is true, His Paradise is true, and His Fire is true.",
        "category": "dhat"
    },
    {
        "number": 52,
        "name_ar": "الوَكِيلُ",
        "name_simple": "الوكيل",
        "transliteration": "Al-Wakil",
        "meaning_en": "The Trustee",
        "meaning_ar": "الذي يُتوكل عليه في الأمور",
        "description_ar": "الوكيل: الكافي الذي توكل بأرزاق العباد وأقواتهم، المتولي لتدبير أمور خلقه. من توكل عليه كفاه.",
        "description_en": "Al-Wakil: The Sufficient One who has undertaken the provision and sustenance of His servants, managing the affairs of His creation. Whoever relies on Him, He suffices them.",
        "category": "jamal"
    },
    {
        "number": 53,
        "name_ar": "القَوِيُّ",
        "name_simple": "القوي",
        "transliteration": "Al-Qawiyy",
        "meaning_en": "The All-Strong",
        "meaning_ar": "التام القوة",
        "description_ar": "القوي: التام القوة الكاملة التي لا يعتريها ضعف، القادر على كل شيء. قوته لا تُحد ولا تُوصف.",
        "description_en": "Al-Qawiyy: The One of complete and perfect strength that is never touched by weakness, capable of all things. His strength is unlimited and indescribable.",
        "category": "jalal"
    },
    {
        "number": 54,
        "name_ar": "المَتِينُ",
        "name_simple": "المتين",
        "transliteration": "Al-Matin",
        "meaning_en": "The Firm",
        "meaning_ar": "الشديد القوة",
        "description_ar": "المتين: الشديد القوة الذي لا يلحقه في أفعاله مشقة ولا تعب. قوته متينة راسخة لا تتزعزع.",
        "description_en": "Al-Matin: The One of intense strength whose actions are never touched by difficulty or fatigue. His strength is solid and steadfast, never wavering.",
        "category": "jalal"
    },
    {
        "number": 55,
        "name_ar": "الوَلِيُّ",
        "name_simple": "الولي",
        "transliteration": "Al-Waliyy",
        "meaning_en": "The Protecting Friend",
        "meaning_ar": "الناصر المتولي لأمور عباده",
        "description_ar": "الولي: الناصر لأوليائه، المتولي لأمور عباده بالإحسان والتدبير. ولي المؤمنين يخرجهم من الظلمات إلى النور.",
        "description_en": "Al-Waliyy: The Supporter of His allies, managing the affairs of His servants with goodness and direction. The Ally of the believers, bringing them from darkness into light.",
        "category": "jamal"
    },
    {
        "number": 56,
        "name_ar": "الحَمِيدُ",
        "name_simple": "الحميد",
        "transliteration": "Al-Hamid",
        "meaning_en": "The Praiseworthy",
        "meaning_ar": "المحمود على كل حال",
        "description_ar": "الحميد: المستحق للحمد، المحمود على كل حال وفي كل فعل. يستحق الحمد على نعمه الظاهرة والباطنة.",
        "description_en": "Al-Hamid: The One deserving of praise, praised in every state and in every action. He deserves praise for His apparent and hidden blessings.",
        "category": "kamal"
    },
    {
        "number": 57,
        "name_ar": "المُحْصِي",
        "name_simple": "المحصي",
        "transliteration": "Al-Muhsi",
        "meaning_en": "The Reckoner",
        "meaning_ar": "الذي أحصى كل شيء",
        "description_ar": "المحصي: الذي أحصى كل شيء بعلمه، يحصي أعداد المخلوقات وأعمالهم. لا يفوته شيء من ذلك.",
        "description_en": "Al-Muhsi: The One who has counted all things with His knowledge, enumerating the numbers of creatures and their deeds. Nothing of that escapes Him.",
        "category": "dhat"
    },
    {
        "number": 58,
        "name_ar": "المُبْدِئُ",
        "name_simple": "المبدئ",
        "transliteration": "Al-Mubdi",
        "meaning_en": "The Originator",
        "meaning_ar": "الذي بدأ خلق الأشياء",
        "description_ar": "المبدئ: الذي أنشأ الأشياء واخترعها ابتداءً من غير سابق مثال. بدأ الخلق ثم يعيده وهو أهون عليه.",
        "description_en": "Al-Mubdi: The One who originated things and invented them from nothing without prior example. He began creation and will repeat it, and that is easier for Him.",
        "category": "af'al"
    },
    {
        "number": 59,
        "name_ar": "المُعِيدُ",
        "name_simple": "المعيد",
        "transliteration": "Al-Mu'id",
        "meaning_en": "The Restorer",
        "meaning_ar": "الذي يعيد الخلق بعد الموت",
        "description_ar": "المعيد: الذي يعيد الخلائق بعد موتهم للحساب والجزاء. كما بدأكم تعودون.",
        "description_en": "Al-Mu'id: The One who will restore creatures after their death for judgment and recompense. As He originated you, so will you return.",
        "category": "af'al"
    },
    {
        "number": 60,
        "name_ar": "المُحْيِي",
        "name_simple": "المحيي",
        "transliteration": "Al-Muhyi",
        "meaning_en": "The Giver of Life",
        "meaning_ar": "الذي يحيي الموتى",
        "description_ar": "المحيي: الذي يحيي النطفة الميتة فيخرج منها الحياة، ويحيي الأرض بعد موتها، ويحيي الموتى يوم القيامة.",
        "description_en": "Al-Muhyi: The One who brings life to the dead sperm and brings life from it, revives the earth after its death, and will resurrect the dead on the Day of Judgment.",
        "category": "af'al"
    },
    {
        "number": 61,
        "name_ar": "المُمِيتُ",
        "name_simple": "المميت",
        "transliteration": "Al-Mumit",
        "meaning_en": "The Taker of Life",
        "meaning_ar": "الذي يميت الأحياء",
        "description_ar": "المميت: الذي يميت الأحياء ويقبض أرواحهم عند انتهاء آجالهم. خلق الموت والحياة ليبلوكم أيكم أحسن عملاً.",
        "description_en": "Al-Mumit: The One who causes the living to die and takes their souls when their terms end. He created death and life to test which of you is best in deed.",
        "category": "af'al"
    },
    {
        "number": 62,
        "name_ar": "الحَيُّ",
        "name_simple": "الحي",
        "transliteration": "Al-Hayy",
        "meaning_en": "The Ever-Living",
        "meaning_ar": "الباقي الذي لا يموت",
        "description_ar": "الحي: الحي حياة كاملة أزلية أبدية، لا بداية لها ولا نهاية. الحي الذي لا يموت، والجن والإنس يموتون.",
        "description_en": "Al-Hayy: The Living One with complete eternal life, without beginning or end. The Living who does not die, while jinn and humans will die.",
        "category": "dhat"
    },
    {
        "number": 63,
        "name_ar": "القَيُّومُ",
        "name_simple": "القيوم",
        "transliteration": "Al-Qayyum",
        "meaning_en": "The Self-Subsisting",
        "meaning_ar": "القائم بنفسه المقيم لغيره",
        "description_ar": "القيوم: القائم بنفسه الغني عن غيره، المقيم لغيره الذي به قيام كل شيء. لا تأخذه سنة ولا نوم.",
        "description_en": "Al-Qayyum: The Self-Subsisting, independent of others, who sustains all else and by whom everything exists. Neither drowsiness nor sleep overtakes Him.",
        "category": "dhat"
    },
    {
        "number": 64,
        "name_ar": "الوَاجِدُ",
        "name_simple": "الواجد",
        "transliteration": "Al-Wajid",
        "meaning_en": "The Finder",
        "meaning_ar": "الغني الذي لا يفقد شيئاً",
        "description_ar": "الواجد: الغني الذي لا يحتاج إلى شيء، الذي وجد كل ما أراده ولا يعوزه شيء. يجد ما يريد حين يريد.",
        "description_en": "Al-Wajid: The Self-Sufficient who needs nothing, who finds whatever He wants and lacks nothing. He finds what He wills when He wills.",
        "category": "dhat"
    },
    {
        "number": 65,
        "name_ar": "المَاجِدُ",
        "name_simple": "الماجد",
        "transliteration": "Al-Majid",
        "meaning_en": "The Noble",
        "meaning_ar": "العظيم الكريم الواسع الإحسان",
        "description_ar": "الماجد: الكريم الشريف المتناهي في الكرم، الواسع الإحسان. مجده عظيم ونواله جسيم.",
        "description_en": "Al-Majid: The Noble and Generous, ultimate in generosity, vast in benevolence. His glory is great and His giving is immense.",
        "category": "jamal"
    },
    {
        "number": 66,
        "name_ar": "الوَاحِدُ",
        "name_simple": "الواحد",
        "transliteration": "Al-Wahid",
        "meaning_en": "The One",
        "meaning_ar": "الفرد الذي لا شريك له",
        "description_ar": "الواحد: الفرد الذي لا شريك له في ذاته ولا في صفاته ولا في أفعاله. المنفرد بالإلهية والربوبية.",
        "description_en": "Al-Wahid: The Single One who has no partner in His essence, attributes, or actions. Unique in divinity and lordship.",
        "category": "dhat"
    },
    {
        "number": 67,
        "name_ar": "الأَحَدُ",
        "name_simple": "الأحد",
        "transliteration": "Al-Ahad",
        "meaning_en": "The Unique",
        "meaning_ar": "المنفرد بصفات الكمال",
        "description_ar": "الأحد: المنفرد بصفات الكمال، الذي لا يقبل الانقسام ولا التجزئة. أحد في ذاته، ليس كمثله شيء.",
        "description_en": "Al-Ahad: The Unique in attributes of perfection, who cannot be divided or partitioned. One in His essence; there is nothing like Him.",
        "category": "dhat"
    },
    {
        "number": 68,
        "name_ar": "الصَّمَدُ",
        "name_simple": "الصمد",
        "transliteration": "As-Samad",
        "meaning_en": "The Eternal Refuge",
        "meaning_ar": "السيد الذي يُقصد في الحوائج",
        "description_ar": "الصمد: السيد الذي كمل في سؤدده، الذي يُصمد إليه في الحوائج، الغني عن الخلق وهم محتاجون إليه.",
        "description_en": "As-Samad: The Master complete in His sovereignty, to whom all turn in their needs, independent of creation while they depend on Him.",
        "category": "dhat"
    },
    {
        "number": 69,
        "name_ar": "القَادِرُ",
        "name_simple": "القادر",
        "transliteration": "Al-Qadir",
        "meaning_en": "The Capable",
        "meaning_ar": "المتمكن من إيجاد المعدوم",
        "description_ar": "القادر: الذي يقدر على إيجاد المعدوم وإعدام الموجود، القادر على كل شيء. إذا أراد شيئاً قال له كن فيكون.",
        "description_en": "Al-Qadir: The One able to bring the non-existent into existence and annihilate the existent, capable of all things. When He intends something, He says 'Be' and it is.",
        "category": "jalal"
    },
    {
        "number": 70,
        "name_ar": "المُقْتَدِرُ",
        "name_simple": "المقتدر",
        "transliteration": "Al-Muqtadir",
        "meaning_en": "The All-Powerful",
        "meaning_ar": "التام القدرة",
        "description_ar": "المقتدر: التام القدرة الذي لا يُعجزه شيء ولا يفوته مطلوب. قدرته مطلقة لا حد لها.",
        "description_en": "Al-Muqtadir: The One of complete power whom nothing incapacitates and from whom nothing sought escapes. His power is absolute without limit.",
        "category": "jalal"
    },
    {
        "number": 71,
        "name_ar": "المُقَدِّمُ",
        "name_simple": "المقدم",
        "transliteration": "Al-Muqaddim",
        "meaning_en": "The Expediter",
        "meaning_ar": "الذي يقدم الأشياء ويضعها في مواضعها",
        "description_ar": "المقدم: الذي يقدم الأشياء ويضعها في مواضعها بحكمته. يقدم من يشاء بالتوفيق والهداية.",
        "description_en": "Al-Muqaddim: The One who advances things and places them in their positions by His wisdom. He advances whom He wills with guidance and success.",
        "category": "af'al"
    },
    {
        "number": 72,
        "name_ar": "المُؤَخِّرُ",
        "name_simple": "المؤخر",
        "transliteration": "Al-Mu'akhkhir",
        "meaning_en": "The Delayer",
        "meaning_ar": "الذي يؤخر الأشياء ويضعها في مواضعها",
        "description_ar": "المؤخر: الذي يؤخر الأشياء ويضعها في مواضعها بحكمته. يؤخر من يشاء عن درجات القرب.",
        "description_en": "Al-Mu'akhkhir: The One who delays things and places them in their positions by His wisdom. He delays whom He wills from ranks of nearness.",
        "category": "af'al"
    },
    {
        "number": 73,
        "name_ar": "الأَوَّلُ",
        "name_simple": "الأول",
        "transliteration": "Al-Awwal",
        "meaning_en": "The First",
        "meaning_ar": "الذي ليس قبله شيء",
        "description_ar": "الأول: الذي ليس قبله شيء، السابق لكل شيء. كان ولم يكن شيء قبله، هو الأول بلا ابتداء.",
        "description_en": "Al-Awwal: The One before whom there is nothing, preceding all things. He existed when nothing else existed; He is the First without beginning.",
        "category": "dhat"
    },
    {
        "number": 74,
        "name_ar": "الآخِرُ",
        "name_simple": "الآخر",
        "transliteration": "Al-Akhir",
        "meaning_en": "The Last",
        "meaning_ar": "الذي ليس بعده شيء",
        "description_ar": "الآخر: الذي ليس بعده شيء، الباقي بعد فناء كل شيء. كل شيء هالك إلا وجهه، هو الآخر بلا انتهاء.",
        "description_en": "Al-Akhir: The One after whom there is nothing, remaining after everything perishes. Everything will perish except His face; He is the Last without end.",
        "category": "dhat"
    },
    {
        "number": 75,
        "name_ar": "الظَّاهِرُ",
        "name_simple": "الظاهر",
        "transliteration": "Az-Zahir",
        "meaning_en": "The Manifest",
        "meaning_ar": "الظاهر فوق كل شيء",
        "description_ar": "الظاهر: الظاهر فوق كل شيء بقهره، الغالب لكل شيء. ظهرت آياته ودلائل وجوده في كل شيء.",
        "description_en": "Az-Zahir: The Manifest above all things through His dominance, prevailing over everything. His signs and proofs of existence are apparent in everything.",
        "category": "dhat"
    },
    {
        "number": 76,
        "name_ar": "البَاطِنُ",
        "name_simple": "الباطن",
        "transliteration": "Al-Batin",
        "meaning_en": "The Hidden",
        "meaning_ar": "المحتجب عن الأبصار",
        "description_ar": "الباطن: المحتجب عن الأبصار في الدنيا، العليم ببواطن الأمور. لا تدركه الأبصار وهو يدرك الأبصار.",
        "description_en": "Al-Batin: The Hidden from sight in this world, who knows the inner dimensions of all matters. Vision cannot perceive Him, but He perceives all vision.",
        "category": "dhat"
    },
    {
        "number": 77,
        "name_ar": "الوَالِي",
        "name_simple": "الوالي",
        "transliteration": "Al-Wali",
        "meaning_en": "The Governor",
        "meaning_ar": "المالك المتصرف في الأمور",
        "description_ar": "الوالي: المالك للأشياء المتصرف فيها، الذي يلي أمور خلقه ويدبرها. له الولاية العامة على جميع الخلق.",
        "description_en": "Al-Wali: The Owner and Disposer of things, who governs the affairs of His creation and manages them. His is the general authority over all creation.",
        "category": "jalal"
    },
    {
        "number": 78,
        "name_ar": "المُتَعَالِي",
        "name_simple": "المتعالي",
        "transliteration": "Al-Muta'ali",
        "meaning_en": "The Most Exalted",
        "meaning_ar": "المرتفع عن صفات المخلوقين",
        "description_ar": "المتعالي: العلي الذي جل عن إفك المفترين، المرتفع عن صفات المخلوقين. تعالى عما يقول الظالمون علواً كبيراً.",
        "description_en": "Al-Muta'ali: The Exalted who is above the fabrications of liars, transcendent above the attributes of created beings. Highly exalted above what the wrongdoers say.",
        "category": "dhat"
    },
    {
        "number": 79,
        "name_ar": "البَرُّ",
        "name_simple": "البر",
        "transliteration": "Al-Barr",
        "meaning_en": "The Source of Goodness",
        "meaning_ar": "الكثير البر والإحسان",
        "description_ar": "البر: الكثير البر والإحسان إلى عباده، الذي يحسن إليهم في السراء والضراء. بره يشمل الخلق كلهم.",
        "description_en": "Al-Barr: The One abundant in kindness and benevolence to His servants, who is good to them in ease and hardship. His goodness encompasses all creation.",
        "category": "jamal"
    },
    {
        "number": 80,
        "name_ar": "التَّوَّابُ",
        "name_simple": "التواب",
        "transliteration": "At-Tawwab",
        "meaning_en": "The Accepter of Repentance",
        "meaning_ar": "الذي يقبل التوبة ويوفق لها",
        "description_ar": "التواب: الذي يقبل توبة عباده مهما عظمت ذنوبهم، ويوفقهم للتوبة. يتوب على التائب مرة بعد مرة.",
        "description_en": "At-Tawwab: The One who accepts the repentance of His servants no matter how great their sins, and guides them to repentance. He accepts repentance time after time.",
        "category": "jamal"
    },
    {
        "number": 81,
        "name_ar": "المُنْتَقِمُ",
        "name_simple": "المنتقم",
        "transliteration": "Al-Muntaqim",
        "meaning_en": "The Avenger",
        "meaning_ar": "الذي ينتقم من الظالمين",
        "description_ar": "المنتقم: الذي ينتقم ممن عصاه بعد الإنذار والإعذار، يعاقب الظالمين بعدله. انتقامه من كمال عدله.",
        "description_en": "Al-Muntaqim: The One who takes vengeance on those who disobey Him after warning and excuse, punishing the wrongdoers by His justice. His vengeance is part of His perfect justice.",
        "category": "jalal"
    },
    {
        "number": 82,
        "name_ar": "العَفُوُّ",
        "name_simple": "العفو",
        "transliteration": "Al-Afuww",
        "meaning_en": "The Pardoner",
        "meaning_ar": "الذي يعفو عن الذنوب",
        "description_ar": "العفو: الذي يمحو السيئات ويتجاوز عن المعاصي، يعفو عن ذنوب عباده ويسترها. محبته للعفو فوق محبته للعقوبة.",
        "description_en": "Al-Afuww: The One who erases sins and overlooks transgressions, pardoning the sins of His servants and concealing them. His love for pardoning exceeds His love for punishing.",
        "category": "jamal"
    },
    {
        "number": 83,
        "name_ar": "الرَّؤُوفُ",
        "name_simple": "الرؤوف",
        "transliteration": "Ar-Ra'uf",
        "meaning_en": "The Compassionate",
        "meaning_ar": "ذو الرأفة الشديدة",
        "description_ar": "الرؤوف: ذو الرأفة الشديدة، أرحم بعباده من الأم بولدها. رأفته ألطف الرحمة وأرقها.",
        "description_en": "Ar-Ra'uf: The One of intense compassion, more merciful to His servants than a mother to her child. His compassion is the gentlest and most tender mercy.",
        "category": "jamal"
    },
    {
        "number": 84,
        "name_ar": "مَالِكُ المُلْكِ",
        "name_simple": "مالك الملك",
        "transliteration": "Malik al-Mulk",
        "meaning_en": "The Owner of Sovereignty",
        "meaning_ar": "المتصرف في ملكه كيف يشاء",
        "description_ar": "مالك الملك: المتصرف في ملكه كيف يشاء، يؤتي الملك من يشاء وينزعه ممن يشاء، ويعز من يشاء ويذل من يشاء.",
        "description_en": "Malik al-Mulk: The Disposer of His dominion as He wills, who gives sovereignty to whom He wills and removes it from whom He wills, honors whom He wills and humiliates whom He wills.",
        "category": "jalal"
    },
    {
        "number": 85,
        "name_ar": "ذُو الجَلَالِ وَالإِكْرَامِ",
        "name_simple": "ذو الجلال والإكرام",
        "transliteration": "Dhul-Jalali wal-Ikram",
        "meaning_en": "The Lord of Majesty and Bounty",
        "meaning_ar": "المستحق للتعظيم والإجلال والإكرام",
        "description_ar": "ذو الجلال والإكرام: صاحب العظمة والكبرياء، المستحق أن يُجل ويُكرم فلا يُكفر. تبارك اسم ربك ذي الجلال والإكرام.",
        "description_en": "Dhul-Jalali wal-Ikram: The Possessor of majesty and grandeur, deserving to be revered and honored, never to be disbelieved. Blessed is the name of your Lord, the Possessor of Majesty and Honor.",
        "category": "kamal"
    },
    {
        "number": 86,
        "name_ar": "المُقْسِطُ",
        "name_simple": "المقسط",
        "transliteration": "Al-Muqsit",
        "meaning_en": "The Equitable",
        "meaning_ar": "العادل في حكمه",
        "description_ar": "المقسط: العادل الذي ينصف المظلوم من الظالم، يقسط بين عباده بالحق. لا يظلم أحداً شيئاً.",
        "description_en": "Al-Muqsit: The Just who gives the oppressed their due from the oppressor, dealing equitably between His servants with truth. He wrongs no one in anything.",
        "category": "kamal"
    },
    {
        "number": 87,
        "name_ar": "الجَامِعُ",
        "name_simple": "الجامع",
        "transliteration": "Al-Jami",
        "meaning_en": "The Gatherer",
        "meaning_ar": "الذي يجمع الخلائق ليوم الحساب",
        "description_ar": "الجامع: الذي يجمع الخلائق ليوم لا ريب فيه، جامع الناس ليوم القيامة. يجمع بين المتفرقات والمتماثلات.",
        "description_en": "Al-Jami: The One who will gather the creatures for a Day about which there is no doubt, gathering mankind for the Day of Resurrection. He brings together disparate and similar things.",
        "category": "af'al"
    },
    {
        "number": 88,
        "name_ar": "الغَنِيُّ",
        "name_simple": "الغني",
        "transliteration": "Al-Ghaniyy",
        "meaning_en": "The Self-Sufficient",
        "meaning_ar": "المستغني عن كل ما سواه",
        "description_ar": "الغني: المستغني عن كل ما سواه، الذي لا يحتاج إلى شيء من خلقه. غني عن العالمين، وكل ما سواه فقير إليه.",
        "description_en": "Al-Ghaniyy: The Self-Sufficient who needs nothing other than Himself, who needs nothing from His creation. Independent of all the worlds, while all else is in need of Him.",
        "category": "dhat"
    },
    {
        "number": 89,
        "name_ar": "المُغْنِي",
        "name_simple": "المغني",
        "transliteration": "Al-Mughni",
        "meaning_en": "The Enricher",
        "meaning_ar": "الذي يغني من يشاء من خلقه",
        "description_ar": "المغني: الذي يغني من يشاء من عباده، يمدهم بالغنى الظاهر والباطن. يغني النفوس بالقناعة والأبدان بالكفاية.",
        "description_en": "Al-Mughni: The One who enriches whom He wills among His servants, providing them with apparent and hidden wealth. He enriches souls with contentment and bodies with sufficiency.",
        "category": "jamal"
    },
    {
        "number": 90,
        "name_ar": "المَانِعُ",
        "name_simple": "المانع",
        "transliteration": "Al-Mani",
        "meaning_en": "The Withholder",
        "meaning_ar": "الذي يمنع من يشاء بحكمته",
        "description_ar": "المانع: الذي يمنع من يشاء ما يشاء بحكمته، يمنع أولياءه مما يضرهم. ما منع منعاً إلا لحكمة.",
        "description_en": "Al-Mani: The One who withholds from whom He wills what He wills in His wisdom, protecting His allies from what harms them. He never withholds except with wisdom.",
        "category": "af'al"
    },
    {
        "number": 91,
        "name_ar": "الضَّارُّ",
        "name_simple": "الضار",
        "transliteration": "Ad-Darr",
        "meaning_en": "The Distressor",
        "meaning_ar": "الذي يقدر الضر على من يشاء",
        "description_ar": "الضار: الذي يقدر الضر على من يشاء من خلقه بحكمته، لا يقع ضر إلا بإذنه. يبتلي عباده بالضراء لحكمة.",
        "description_en": "Ad-Darr: The One who ordains harm for whom He wills among His creation in His wisdom. No harm occurs except by His permission. He tests His servants with hardship for a wisdom.",
        "category": "af'al"
    },
    {
        "number": 92,
        "name_ar": "النَّافِعُ",
        "name_simple": "النافع",
        "transliteration": "An-Nafi",
        "meaning_en": "The Benefactor",
        "meaning_ar": "الذي يقدر النفع لمن يشاء",
        "description_ar": "النافع: الذي يقدر النفع لمن يشاء من عباده، كل نفع من عنده. لا نافع ولا ضار إلا هو.",
        "description_en": "An-Nafi: The One who ordains benefit for whom He wills among His servants. All benefit comes from Him. There is no benefactor or harmer except Him.",
        "category": "af'al"
    },
    {
        "number": 93,
        "name_ar": "النُّورُ",
        "name_simple": "النور",
        "transliteration": "An-Nur",
        "meaning_en": "The Light",
        "meaning_ar": "نور السماوات والأرض",
        "description_ar": "النور: نور السماوات والأرض، الهادي الذي بنوره يهتدي الحائرون. نور على نور، يهدي الله لنوره من يشاء.",
        "description_en": "An-Nur: The Light of the heavens and the earth, the Guide by whose light the lost find their way. Light upon light; Allah guides to His light whom He wills.",
        "category": "jamal"
    },
    {
        "number": 94,
        "name_ar": "الهَادِي",
        "name_simple": "الهادي",
        "transliteration": "Al-Hadi",
        "meaning_en": "The Guide",
        "meaning_ar": "الذي يهدي إلى الحق",
        "description_ar": "الهادي: الذي هدى الخلق إلى معرفته ووحدانيته، وهدى المؤمنين إلى طاعته. يهدي من يشاء إلى صراط مستقيم.",
        "description_en": "Al-Hadi: The One who guided creation to know Him and His oneness, and guided believers to His obedience. He guides whom He wills to a straight path.",
        "category": "jamal"
    },
    {
        "number": 95,
        "name_ar": "البَدِيعُ",
        "name_simple": "البديع",
        "transliteration": "Al-Badi",
        "meaning_en": "The Originator",
        "meaning_ar": "المبتدع للخلق على غير مثال",
        "description_ar": "البديع: المبتدع للخلق على غير مثال سابق، الخالق المخترع للأشياء بلا احتذاء. بديع السماوات والأرض.",
        "description_en": "Al-Badi: The Originator of creation without any prior example, the Creator and Inventor of things without imitation. Originator of the heavens and earth.",
        "category": "af'al"
    },
    {
        "number": 96,
        "name_ar": "البَاقِي",
        "name_simple": "الباقي",
        "transliteration": "Al-Baqi",
        "meaning_en": "The Ever-Lasting",
        "meaning_ar": "الدائم الذي لا يفنى",
        "description_ar": "الباقي: الدائم الوجود الذي لا يفنى ولا يزول، الباقي بعد فناء خلقه. كل من عليها فان ويبقى وجه ربك.",
        "description_en": "Al-Baqi: The Eternal in existence who never perishes or ceases, remaining after the annihilation of His creation. Everyone upon it will perish, but the Face of your Lord will remain.",
        "category": "dhat"
    },
    {
        "number": 97,
        "name_ar": "الوَارِثُ",
        "name_simple": "الوارث",
        "transliteration": "Al-Warith",
        "meaning_en": "The Inheritor",
        "meaning_ar": "الباقي بعد فناء الخلق",
        "description_ar": "الوارث: الباقي بعد فناء الخلق، الذي يرث الأرض ومن عليها. إنا نحن نرث الأرض ومن عليها وإلينا يُرجعون.",
        "description_en": "Al-Warith: The Remaining after the annihilation of creation, who will inherit the earth and all upon it. Indeed, it is We who will inherit the earth and all upon it, and to Us they will be returned.",
        "category": "dhat"
    },
    {
        "number": 98,
        "name_ar": "الرَّشِيدُ",
        "name_simple": "الرشيد",
        "transliteration": "Ar-Rashid",
        "meaning_en": "The Guide to the Right Path",
        "meaning_ar": "المرشد إلى الحق والصواب",
        "description_ar": "الرشيد: المرشد إلى الحق والصواب، الذي تنساق تدبيراته إلى غاياتها على سنن السداد. أفعاله كلها رشد وحكمة.",
        "description_en": "Ar-Rashid: The Guide to truth and right, whose dispositions lead to their aims on the path of rectitude. All His actions are guidance and wisdom.",
        "category": "kamal"
    },
    {
        "number": 99,
        "name_ar": "الصَّبُورُ",
        "name_simple": "الصبور",
        "transliteration": "As-Sabur",
        "meaning_en": "The Patient",
        "meaning_ar": "الذي يمهل ولا يعجل",
        "description_ar": "الصبور: الذي لا يعجل بالعقوبة على من عصاه، يمهل العاصين ولا يهملهم. صبره كمال لا عجز.",
        "description_en": "As-Sabur: The One who does not hasten to punish those who disobey Him, giving respite to sinners without neglecting them. His patience is perfection, not inability.",
        "category": "kamal"
    },
]

# Category labels for UI display
CATEGORY_LABELS = {
    "dhat": {
        "ar": "الذات",
        "en": "Essence"
    },
    "jamal": {
        "ar": "الجمال",
        "en": "Beauty"
    },
    "jalal": {
        "ar": "الجلال",
        "en": "Majesty"
    },
    "kamal": {
        "ar": "الكمال",
        "en": "Perfection"
    },
    "af'al": {
        "ar": "الأفعال",
        "en": "Actions"
    },
}


def get_name_by_number(number: int) -> AllahName | None:
    """Get a specific name by its number (1-99)."""
    for name in ALLAH_NAMES_99:
        if name["number"] == number:
            return name
    return None


def get_names_by_category(category: str) -> list[AllahName]:
    """Get all names in a specific category."""
    return [name for name in ALLAH_NAMES_99 if name["category"] == category]


def get_all_categories() -> list[str]:
    """Get all unique category values."""
    return list(CATEGORY_LABELS.keys())
