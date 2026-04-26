"""
Tadabbur - Comprehensive Quranic Knowledge Platform
Streamlit Cloud Version

Features:
- Quran browsing (Surah, Juz, Page)
- Multiple Tafseer editions
- Quranic Themes explorer
- Prophet Stories browser
- Concepts & Prophets
- Verse Search
- Similar Verses finder
- Arabic/English bilingual support
"""
import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
import streamlit as st
import httpx

# =============================================================================
# Page Configuration
# =============================================================================
st.set_page_config(
    page_title="Tadabbur - Quranic Platform",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Custom CSS
# =============================================================================
st.markdown("""
<style>
    /* Import Arabic fonts */
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&family=Amiri:wght@400;700&display=swap');

    /* Arabic text styling */
    .arabic-text {
        font-family: 'Amiri', 'Scheherazade New', 'Traditional Arabic', serif;
        font-size: 1.8rem;
        line-height: 2.2;
        direction: rtl;
        text-align: right;
        color: #1a365d;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.8rem 0;
        border-right: 4px solid #3182ce;
    }

    .arabic-text-large {
        font-family: 'Amiri', 'Scheherazade New', serif;
        font-size: 2.5rem;
        line-height: 2.5;
        direction: rtl;
        text-align: center;
        color: #1a365d;
        padding: 1.5rem;
    }

    /* Verse number badge */
    .verse-badge {
        display: inline-block;
        background: #3182ce;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        text-align: center;
        line-height: 30px;
        font-size: 0.85rem;
        margin-left: 8px;
        font-family: sans-serif;
    }

    /* Translation text */
    .translation-text {
        font-size: 1.05rem;
        color: #4a5568;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 3px solid #48bb78;
        margin: 0.5rem 0;
        line-height: 1.7;
    }

    /* Tafseer box */
    .tafseer-box {
        background: #fffbeb;
        border: 1px solid #f6e05e;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.8rem 0;
        font-size: 0.95rem;
        line-height: 1.8;
    }

    .tafseer-arabic {
        font-family: 'Amiri', serif;
        direction: rtl;
        text-align: right;
        font-size: 1.1rem;
    }

    /* Surah header */
    .surah-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #2b6cb0 0%, #1a365d 100%);
        color: white;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }

    .surah-header h2 {
        margin: 0;
        font-size: 1.8rem;
    }

    .surah-header .arabic-name {
        font-family: 'Amiri', serif;
        font-size: 2.5rem;
        margin-top: 0.5rem;
    }

    /* Meta badges */
    .meta-badge {
        display: inline-block;
        background: #e2e8f0;
        color: #4a5568;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 2px 4px;
    }

    .meta-badge-primary {
        background: #3182ce;
        color: white;
    }

    /* Theme card */
    .theme-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .theme-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .theme-title-ar {
        font-family: 'Amiri', serif;
        font-size: 1.5rem;
        color: #2b6cb0;
        direction: rtl;
    }

    /* Story card */
    .story-card {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border: 1px solid #9ae6b4;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
    }

    /* Concept card */
    .concept-card {
        background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
        border: 1px solid #90cdf4;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    /* Category badges */
    .category-aqidah { background: #805ad5; color: white; }
    .category-iman { background: #3182ce; color: white; }
    .category-ibadat { background: #38a169; color: white; }
    .category-akhlaq { background: #dd6b20; color: white; }
    .category-muamalat { background: #e53e3e; color: white; }

    /* Bismillah */
    .bismillah {
        font-family: 'Amiri', serif;
        font-size: 2rem;
        text-align: center;
        color: #2b6cb0;
        padding: 1rem;
        direction: rtl;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #f7fafc;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Data Loading Functions
# =============================================================================
@st.cache_data(ttl=3600)
def load_quran_data() -> List[Dict]:
    """Load Quran verses from local JSON or API."""
    local_paths = [
        Path("streamlit_data/hafs_smart_v8.json"),
        Path("assets/hafs_smart_v8.json"),
    ]

    for path in local_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)

    # Fallback to API
    try:
        with httpx.Client(timeout=60.0) as client:
            uthmani = client.get("https://api.alquran.cloud/v1/quran/quran-uthmani").json()
            simple = client.get("https://api.alquran.cloud/v1/quran/quran-simple").json()

        simple_lookup = {a["number"]: a["text"] for s in simple["data"]["surahs"] for a in s["ayahs"]}
        verses = []
        vid = 0
        for sura in uthmani["data"]["surahs"]:
            for ayah in sura["ayahs"]:
                vid += 1
                verses.append({
                    "id": vid, "sura_no": sura["number"],
                    "sura_name_ar": sura["name"], "sura_name_en": sura["englishName"],
                    "aya_no": ayah["numberInSurah"], "aya_text": ayah["text"],
                    "aya_text_emlaey": simple_lookup.get(ayah["number"], ayah["text"]),
                    "page": ayah.get("page", 1), "jozz": ayah.get("juz", 1),
                })
        return verses
    except Exception as e:
        st.error(f"Failed to load Quran data: {e}")
        return []


@st.cache_data(ttl=3600)
def load_themes_data() -> Dict:
    """Load Quranic themes."""
    path = Path("streamlit_data/quranic_themes.json")
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"themes": []}


@st.cache_data(ttl=3600)
def load_stories_data() -> Dict:
    """Load Quranic stories."""
    path = Path("streamlit_data/stories.json")
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"stories": []}


@st.cache_data(ttl=3600)
def load_concepts_data() -> Dict:
    """Load Quranic concepts (prophets, places, etc.)."""
    path = Path("streamlit_data/curated_concepts.json")
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"persons": [], "places": [], "nations": []}


@st.cache_data(ttl=300)
def fetch_translations_bulk(surah: int) -> Dict[int, str]:
    """Fetch all translations for a surah."""
    try:
        url = f"https://api.alquran.cloud/v1/surah/{surah}/en.sahih"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                return {a["numberInSurah"]: a["text"] for a in data["data"]["ayahs"]}
    except:
        pass
    return {}


@st.cache_data(ttl=300)
def fetch_translation(surah: int, ayah: int) -> Optional[str]:
    """Fetch single verse translation."""
    try:
        url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.sahih"
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                return response.json()["data"]["text"]
    except:
        pass
    return None


@st.cache_data(ttl=300)
def fetch_tafseer(surah: int, ayah: int, edition: str = "ar.muyassar") -> Optional[str]:
    """Fetch tafseer for a verse."""
    try:
        url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{edition}"
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                return response.json()["data"]["text"]
    except:
        pass
    return None


@st.cache_data(ttl=3600)
def fetch_tafseer_editions() -> List[Dict]:
    """Get available tafseer editions."""
    try:
        url = "https://api.alquran.cloud/v1/edition/type/tafsir"
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                editions = response.json()["data"]
                # Filter to most useful ones
                priority = ["ar.muyassar", "en.ibn-kathir", "ar.jalalayn", "en.sahih"]
                return sorted(editions, key=lambda x: priority.index(x["identifier"]) if x["identifier"] in priority else 999)
    except:
        pass
    return [
        {"identifier": "ar.muyassar", "name": "Tafseer Al-Muyassar", "language": "ar"},
        {"identifier": "ar.jalalayn", "name": "Tafseer Jalalayn", "language": "ar"},
    ]


# =============================================================================
# Helper Functions
# =============================================================================
def get_surahs(verses: List[Dict]) -> List[Dict]:
    """Get unique list of surahs with metadata."""
    surahs = {}
    for v in verses:
        sn = v["sura_no"]
        if sn not in surahs:
            surahs[sn] = {
                "number": sn,
                "name_ar": v["sura_name_ar"],
                "name_en": v["sura_name_en"],
                "verse_count": 0
            }
        surahs[sn]["verse_count"] += 1
    return list(surahs.values())


def get_surah_verses(verses: List[Dict], surah_no: int) -> List[Dict]:
    """Get all verses for a specific surah."""
    return [v for v in verses if v["sura_no"] == surah_no]


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for search."""
    text = re.sub(r'[\u064B-\u0652\u0670]', '', text)  # Remove diacritics
    text = re.sub(r'[إأآا]', 'ا', text)  # Normalize alef
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    return text.strip().lower()


def search_verses(verses: List[Dict], query: str) -> List[Dict]:
    """Search verses by text."""
    query_norm = normalize_arabic(query)
    results = []
    for v in verses:
        text_norm = normalize_arabic(v.get("aya_text", ""))
        if query_norm in text_norm or query.lower() in v.get("sura_name_en", "").lower():
            results.append(v)
    return results[:100]


def get_category_color(category: str) -> str:
    """Get color class for theme category."""
    colors = {
        "aqidah": "#805ad5", "iman": "#3182ce", "ibadat": "#38a169",
        "akhlaq_fardi": "#dd6b20", "akhlaq_ijtima": "#e53e3e",
        "muharramat": "#c53030", "sunan_ilahiyyah": "#2c5282"
    }
    return colors.get(category, "#718096")


# =============================================================================
# UI Components
# =============================================================================
def render_bismillah():
    """Render Bismillah."""
    st.markdown('<div class="bismillah">بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</div>', unsafe_allow_html=True)


def render_surah_header(surah_info: Dict):
    """Render surah header."""
    st.markdown(f"""
    <div class="surah-header">
        <div class="arabic-name">{surah_info['name_ar']}</div>
        <h2>{surah_info['name_en']}</h2>
        <p>Surah {surah_info['number']} • {surah_info['verse_count']} Verses</p>
    </div>
    """, unsafe_allow_html=True)


def render_verse(verse: Dict, translation: str = None, tafseer: str = None,
                 show_surah: bool = False, tafseer_lang: str = "ar"):
    """Render a single verse with optional translation and tafseer."""
    if show_surah:
        st.markdown(f"**{verse['sura_name_en']}** ({verse['sura_name_ar']}) - {verse['sura_no']}:{verse['aya_no']}")

    # Arabic verse
    st.markdown(f"""
    <div class="arabic-text">
        {verse['aya_text']}
        <span class="verse-badge">{verse['aya_no']}</span>
    </div>
    """, unsafe_allow_html=True)

    # Metadata
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f'<span class="meta-badge">Juz {verse["jozz"]}</span>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<span class="meta-badge">Page {verse["page"]}</span>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<span class="meta-badge meta-badge-primary">{verse["sura_no"]}:{verse["aya_no"]}</span>', unsafe_allow_html=True)

    # Translation
    if translation:
        st.markdown(f'<div class="translation-text">{translation}</div>', unsafe_allow_html=True)

    # Tafseer
    if tafseer:
        with st.expander("📖 View Tafseer"):
            css_class = "tafseer-arabic" if tafseer_lang == "ar" else ""
            st.markdown(f'<div class="tafseer-box {css_class}">{tafseer}</div>', unsafe_allow_html=True)


def render_theme_card(theme: Dict):
    """Render a theme card."""
    cat_color = get_category_color(theme.get("category", ""))
    st.markdown(f"""
    <div class="theme-card">
        <div class="theme-title-ar">{theme.get('title_ar', '')}</div>
        <h4>{theme.get('title_en', '')}</h4>
        <span class="meta-badge" style="background:{cat_color};color:white">{theme.get('category', '').replace('_', ' ').title()}</span>
        <p style="margin-top:0.8rem;color:#4a5568">{theme.get('description_en', '')}</p>
    </div>
    """, unsafe_allow_html=True)


def render_story_card(story: Dict):
    """Render a story card."""
    st.markdown(f"""
    <div class="story-card">
        <h4 style="color:#276749;margin:0">{story.get('name_en', '')}</h4>
        <div style="font-family:'Amiri',serif;font-size:1.3rem;color:#2f855a;direction:rtl">{story.get('name_ar', '')}</div>
        <p style="margin-top:0.8rem;color:#4a5568">{story.get('summary_en', '')}</p>
        <div style="margin-top:0.5rem">
            <span class="meta-badge">{story.get('category', '').title()}</span>
            <span class="meta-badge">Suras: {', '.join(map(str, story.get('suras_mentioned', [])[:5]))}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_concept_card(concept: Dict, concept_type: str):
    """Render a concept/prophet card."""
    st.markdown(f"""
    <div class="concept-card">
        <h4 style="color:#2b6cb0;margin:0">{concept.get('label_en', '')}</h4>
        <div style="font-family:'Amiri',serif;font-size:1.2rem;direction:rtl">{concept.get('label_ar', '')}</div>
        <p style="margin-top:0.5rem;color:#4a5568;font-size:0.9rem">{concept.get('description_ar', '')}</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# Page Functions
# =============================================================================
def page_quran_browser(verses: List[Dict], surahs: List[Dict]):
    """Quran browsing page."""
    st.header("📖 Quran Browser")

    # View mode tabs
    tab1, tab2, tab3 = st.tabs(["By Surah", "By Juz", "By Page"])

    # Sidebar controls
    with st.sidebar:
        st.subheader("Display Options")
        show_translation = st.checkbox("Show Translation", value=True)
        show_tafseer = st.checkbox("Show Tafseer", value=False)

        if show_tafseer:
            editions = fetch_tafseer_editions()
            edition_names = {e["identifier"]: f"{e['name']} ({e['language']})" for e in editions[:10]}
            selected_edition = st.selectbox(
                "Tafseer Edition",
                options=list(edition_names.keys()),
                format_func=lambda x: edition_names.get(x, x)
            )
        else:
            selected_edition = "ar.muyassar"

    with tab1:
        # Surah selector
        col1, col2 = st.columns([2, 1])
        with col1:
            surah_options = [f"{s['number']}. {s['name_en']} ({s['name_ar']})" for s in surahs]
            selected = st.selectbox("Select Surah", surah_options)
            surah_no = int(selected.split(".")[0])

        surah_verses = get_surah_verses(verses, surah_no)
        surah_info = next((s for s in surahs if s["number"] == surah_no), None)

        with col2:
            verse_range = st.slider("Verse Range", 1, len(surah_verses), (1, min(10, len(surah_verses))))

        if surah_info:
            render_surah_header(surah_info)
            if surah_no != 9:  # No Bismillah for Surah Tawbah
                render_bismillah()

        # Load translations
        translations = fetch_translations_bulk(surah_no) if show_translation else {}

        # Display verses
        for v in surah_verses:
            if verse_range[0] <= v["aya_no"] <= verse_range[1]:
                trans = translations.get(v["aya_no"])
                tafs = fetch_tafseer(surah_no, v["aya_no"], selected_edition) if show_tafseer else None
                tafs_lang = "ar" if selected_edition.startswith("ar.") else "en"
                render_verse(v, trans, tafs, tafseer_lang=tafs_lang)
                st.divider()

    with tab2:
        juz_no = st.selectbox("Select Juz", list(range(1, 31)), key="juz_select")
        juz_verses = [v for v in verses if v["jozz"] == juz_no]

        st.info(f"Juz {juz_no}: {len(juz_verses)} verses")

        # Group by surah and show first 30 verses
        current_surah = None
        for i, v in enumerate(juz_verses[:30]):
            if v["sura_no"] != current_surah:
                current_surah = v["sura_no"]
                si = next((s for s in surahs if s["number"] == current_surah), None)
                if si:
                    st.subheader(f"{si['name_en']} ({si['name_ar']})")

            trans = fetch_translation(v["sura_no"], v["aya_no"]) if show_translation else None
            render_verse(v, trans)
            st.divider()

        if len(juz_verses) > 30:
            st.warning(f"Showing 30 of {len(juz_verses)} verses. Use Surah view for full content.")

    with tab3:
        page_no = st.number_input("Page Number", min_value=1, max_value=604, value=1)
        page_verses = [v for v in verses if v["page"] == page_no]

        st.info(f"Page {page_no}: {len(page_verses)} verses")

        current_surah = None
        for v in page_verses:
            if v["sura_no"] != current_surah:
                current_surah = v["sura_no"]
                si = next((s for s in surahs if s["number"] == current_surah), None)
                if si:
                    st.subheader(f"{si['name_en']} ({si['name_ar']})")

            trans = fetch_translation(v["sura_no"], v["aya_no"]) if show_translation else None
            render_verse(v, trans)
            st.divider()


def page_themes(themes_data: Dict, verses: List[Dict]):
    """Quranic themes explorer."""
    st.header("🎯 Quranic Themes")
    st.markdown("Explore major themes and topics discussed in the Quran")

    themes = themes_data.get("themes", [])

    # Category filter
    categories = list(set(t.get("category", "") for t in themes if t.get("category")))
    category_labels = {
        "aqidah": "Aqidah (Creed)",
        "iman": "Iman (Faith)",
        "ibadat": "Ibadat (Worship)",
        "akhlaq_fardi": "Personal Ethics",
        "akhlaq_ijtima": "Social Ethics",
        "muharramat": "Prohibitions",
        "sunan_ilahiyyah": "Divine Laws"
    }

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_cat = st.selectbox(
            "Filter by Category",
            ["All"] + categories,
            format_func=lambda x: category_labels.get(x, x.title()) if x != "All" else "All Categories"
        )

    with col2:
        search_theme = st.text_input("Search themes", placeholder="Enter theme name...")

    # Filter themes
    filtered = themes
    if selected_cat != "All":
        filtered = [t for t in filtered if t.get("category") == selected_cat]
    if search_theme:
        search_lower = search_theme.lower()
        filtered = [t for t in filtered if search_lower in t.get("title_en", "").lower()
                   or search_lower in t.get("title_ar", "")]

    # Display themes
    st.markdown(f"**{len(filtered)} themes found**")

    for theme in filtered:
        with st.container():
            render_theme_card(theme)

            # Show related info in expander
            with st.expander("View Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Key Concepts:**")
                    concepts = theme.get("key_concepts", [])
                    st.markdown(" • ".join(concepts[:5]))

                with col2:
                    st.markdown("**Related Themes:**")
                    related = theme.get("related_theme_ids", [])
                    for rid in related[:3]:
                        rel_theme = next((t for t in themes if t["id"] == rid), None)
                        if rel_theme:
                            st.markdown(f"- {rel_theme['title_en']}")

                # Arabic description
                if theme.get("description_ar"):
                    st.markdown("**Arabic Description:**")
                    st.markdown(f'<div style="font-family:Amiri;direction:rtl;text-align:right">{theme["description_ar"]}</div>',
                               unsafe_allow_html=True)


def page_stories(stories_data: Dict, verses: List[Dict]):
    """Quranic stories explorer."""
    st.header("📚 Quranic Stories")
    st.markdown("Explore narratives of Prophets and nations in the Quran")

    stories = stories_data.get("stories", [])

    # Category filter
    categories = list(set(s.get("category", "") for s in stories if s.get("category")))

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_cat = st.selectbox(
            "Filter by Category",
            ["All"] + sorted(categories),
            format_func=lambda x: x.title() if x != "All" else "All Stories"
        )

    with col2:
        search_story = st.text_input("Search stories", placeholder="Enter prophet or story name...")

    # Filter stories
    filtered = stories
    if selected_cat != "All":
        filtered = [s for s in filtered if s.get("category") == selected_cat]
    if search_story:
        search_lower = search_story.lower()
        filtered = [s for s in filtered if search_lower in s.get("name_en", "").lower()
                   or search_lower in s.get("name_ar", "")
                   or any(search_lower in f.lower() for f in s.get("main_figures", []))]

    st.markdown(f"**{len(filtered)} stories found**")

    for story in filtered:
        render_story_card(story)

        with st.expander("View Story Segments"):
            # Main figures
            st.markdown("**Main Figures:** " + ", ".join(story.get("main_figures", [])))

            # Themes
            st.markdown("**Themes:** " + ", ".join(story.get("themes", [])))

            # Segments
            segments = story.get("segments", [])
            if segments:
                st.markdown("**Story Segments:**")
                for seg in segments[:10]:
                    with st.container():
                        st.markdown(f"**{seg.get('aspect', 'Segment').replace('_', ' ').title()}** - Surah {seg.get('sura_no')}:{seg.get('aya_start')}-{seg.get('aya_end')}")
                        st.markdown(f"_{seg.get('summary_en', '')}_")

                        # Show the verses
                        for v in verses:
                            if (v["sura_no"] == seg.get("sura_no") and
                                seg.get("aya_start") <= v["aya_no"] <= seg.get("aya_end")):
                                st.markdown(f'<div class="arabic-text" style="font-size:1.3rem">{v["aya_text"]}</div>',
                                           unsafe_allow_html=True)
                                break


def page_concepts(concepts_data: Dict):
    """Concepts and Prophets explorer."""
    st.header("👥 Prophets & Concepts")

    tab1, tab2, tab3 = st.tabs(["Prophets", "Places", "Nations"])

    with tab1:
        st.subheader("Prophets Mentioned in the Quran")
        persons = concepts_data.get("persons", [])

        cols = st.columns(2)
        for i, person in enumerate(persons):
            with cols[i % 2]:
                render_concept_card(person, "person")

    with tab2:
        st.subheader("Sacred Places")
        places = concepts_data.get("places", [])
        if places:
            for place in places:
                render_concept_card(place, "place")
        else:
            st.info("Place data coming soon...")

    with tab3:
        st.subheader("Nations & Peoples")
        nations = concepts_data.get("nations", [])
        if nations:
            for nation in nations:
                render_concept_card(nation, "nation")
        else:
            st.info("Nations data coming soon...")


def page_search(verses: List[Dict], surahs: List[Dict]):
    """Search page."""
    st.header("🔍 Search the Quran")

    query = st.text_input("Enter search term", placeholder="Search in Arabic or English...")

    col1, col2 = st.columns(2)
    with col1:
        show_translation = st.checkbox("Show translations", value=True, key="search_trans")
    with col2:
        show_tafseer = st.checkbox("Show tafseer", value=False, key="search_tafs")

    if query:
        with st.spinner("Searching..."):
            results = search_verses(verses, query)

        if results:
            st.success(f"Found {len(results)} matching verses")

            for v in results:
                trans = fetch_translation(v["sura_no"], v["aya_no"]) if show_translation else None
                tafs = fetch_tafseer(v["sura_no"], v["aya_no"]) if show_tafseer else None
                render_verse(v, trans, tafs, show_surah=True)
                st.divider()
        else:
            st.warning("No verses found. Try different search terms.")
    else:
        st.info("Enter Arabic text or surah name to search")

        # Quick search suggestions
        st.markdown("### Quick Searches")
        suggestions = ["الرحمن", "الصبر", "الجنة", "التوبة", "Al-Fatiha", "Ayat Al-Kursi"]
        cols = st.columns(3)
        for i, sug in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(sug, key=f"sug_{i}"):
                    st.session_state["search_query"] = sug
                    st.rerun()


def page_about():
    """About page."""
    st.header("ℹ️ About Tadabbur")

    st.markdown("""
    ### Tadabbur - Quranic Knowledge Platform

    **Tadabbur** (تدبر) means deep reflection and contemplation of the Quran's meanings.

    This platform provides tools for exploring the Holy Quran:

    - **📖 Quran Browser** - Read the Quran by Surah, Juz, or Page
    - **🎯 Themes** - Explore 30+ major Quranic themes
    - **📚 Stories** - Browse stories of Prophets and nations
    - **👥 Concepts** - Learn about Prophets, places, and key figures
    - **🔍 Search** - Find verses by Arabic text or topics

    ### Data Sources

    - Quran text: [alquran.cloud](https://alquran.cloud)
    - Translations: Sahih International (English)
    - Tafseer: Al-Muyassar, Ibn Kathir, Jalalayn, and more

    ### Methodology

    This platform follows **Sunni Orthodox methodology** based on the four Madhabs,
    with content grounded in classical tafsir sources including:
    - Tafsir Ibn Kathir
    - Tafsir Al-Tabari
    - Tafsir Al-Qurtubi

    ---

    Built with Streamlit | [GitHub Repository](https://github.com/mhamdan/tadabbur)
    """)


# =============================================================================
# Main Application
# =============================================================================
def main():
    # Load all data
    verses = load_quran_data()
    themes_data = load_themes_data()
    stories_data = load_stories_data()
    concepts_data = load_concepts_data()

    if not verses:
        st.error("Failed to load Quran data. Please refresh.")
        return

    surahs = get_surahs(verses)

    # Sidebar Navigation
    with st.sidebar:
        st.title("📖 Tadabbur")
        st.markdown("*Quranic Knowledge Platform*")
        st.divider()

        page = st.radio(
            "Navigation",
            ["Quran Browser", "Themes", "Stories", "Prophets & Concepts", "Search", "About"],
            label_visibility="collapsed"
        )

        st.divider()

        # Stats
        st.markdown("### Quick Stats")
        st.markdown(f"- **114** Surahs")
        st.markdown(f"- **6,236** Verses")
        st.markdown(f"- **{len(themes_data.get('themes', []))}** Themes")
        st.markdown(f"- **{len(stories_data.get('stories', []))}** Stories")

        st.divider()
        st.markdown("---")
        st.caption("Data from alquran.cloud API")

    # Page routing
    if page == "Quran Browser":
        page_quran_browser(verses, surahs)
    elif page == "Themes":
        page_themes(themes_data, verses)
    elif page == "Stories":
        page_stories(stories_data, verses)
    elif page == "Prophets & Concepts":
        page_concepts(concepts_data)
    elif page == "Search":
        page_search(verses, surahs)
    elif page == "About":
        page_about()


if __name__ == "__main__":
    main()
