#!/usr/bin/env python3
"""
Generate missing Quranic stories using Ollama (qwen2.5:14b).
Outputs TypeScript-compatible JSON structures for each story.
Run: python3 scripts/generate_missing_stories.py
"""
import json
import subprocess
import sys
import time

MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434"

STORY_SPECS = [
    {
        "id": "sulayman",
        "name_ar": "سليمان",
        "name_en": "Solomon",
        "surahs": "Sad 38:30-40, Anbiya 21:79-82, Saba 34:10-14, Naml 27:15-19",
        "key_events": [
            "Wisdom and judgment given at young age (38:30)",
            "Command over wind (34:12, 21:81)",
            "Command over jinn (34:12-13, 38:37-38)",
            "Understanding speech of birds (27:16-19)",
            "Army of jinn, men, and birds (27:17)",
            "Solomon's trials and repentance (38:30-35)",
            "The ring incident and test (38:34)",
            "Death while leaning on staff, jinn unaware (34:14)",
        ],
        "themes": ["gratitude", "prophethood", "divine_blessing", "kingship"],
    },
    {
        "id": "ilyas",
        "name_ar": "إلياس",
        "name_en": "Elijah",
        "surahs": "Saffat 37:123-132, Anam 6:85",
        "key_events": [
            "Called as prophet (6:85)",
            "Called his people away from Baal worship (37:125)",
            "Challenged people to leave idol worship (37:126)",
            "People rejected him (37:127)",
            "Praised by Allah, peace upon him (37:130)",
            "Among the sincere servants of Allah (37:132)",
        ],
        "themes": ["prophethood", "tawheed", "persecution", "divine_support"],
    },
    {
        "id": "alyasa",
        "name_ar": "اليسع",
        "name_en": "Elisha",
        "surahs": "Anam 6:86, Sad 38:48",
        "key_events": [
            "Mentioned among the prophets given guidance (6:86)",
            "Praised as among the best (38:47-48)",
            "Mentioned alongside Dhul-Kifl (38:48)",
            "Given favor and guidance from Allah",
        ],
        "themes": ["prophethood", "guidance", "divine_blessing"],
    },
    {
        "id": "dhulkifl",
        "name_ar": "ذو الكفل",
        "name_en": "Dhul-Kifl",
        "surahs": "Anbiya 21:85-86, Sad 38:48",
        "key_events": [
            "Mentioned with Ismail and Idris among the patient (21:85)",
            "Allah admitted him into His mercy (21:86)",
            "Among the righteous (21:86)",
            "Mentioned with Elisha as among the best (38:47-48)",
        ],
        "themes": ["patience", "prophethood", "righteousness"],
    },
    {
        "id": "harun",
        "name_ar": "هارون",
        "name_en": "Aaron",
        "surahs": "Taha 20:29-36, Araf 7:142-150, Taha 20:85-97, Maryam 19:53",
        "key_events": [
            "Moses asks Allah to make Aaron his helper (20:29-32)",
            "Aaron given prophethood and eloquence (20:36, 19:53)",
            "Aaron left in charge when Moses went to the mountain (7:142)",
            "The golden calf incident — Aaron tried to stop them (20:90-97)",
            "Moses' anger at Aaron on return (7:150, 20:92-94)",
            "Aaron's defense: feared division among people (20:94)",
            "Aaron vindicated as faithful (37:120)",
        ],
        "themes": ["prophethood", "brotherhood", "leadership", "trial"],
    },
    {
        "id": "ishaq",
        "name_ar": "إسحاق",
        "name_en": "Isaac",
        "surahs": "Hud 11:71, Saffat 37:112-113, Ankabut 29:27, Ibrahim 14:39",
        "key_events": [
            "Announced to Ibrahim and Sarah by angels (11:71)",
            "Sarah's shock at pregnancy in old age (11:71-73)",
            "Blessed with prophethood after his father Ibrahim (37:112)",
            "Granted righteous offspring (37:113)",
            "Ibrahim praises Allah for granting Ismail and Ishaq (14:39)",
        ],
        "themes": ["prophethood", "divine_blessing", "family", "gratitude"],
    },
    {
        "id": "yaqub",
        "name_ar": "يعقوب",
        "name_en": "Jacob",
        "surahs": "Yusuf 12 (throughout), Baqarah 2:132-133, Anbiya 21:72",
        "key_events": [
            "Prophet son of Ishaq, grandson of Ibrahim (21:72)",
            "Commands his sons to die only as Muslims (2:133)",
            "Grief over Yusuf's disappearance — whitened eyes from grief (12:84)",
            "Never despaired of Allah's relief (12:87)",
            "Kept Yusuf's shirt to recover his sight (12:93)",
            "Reunion with Yusuf in Egypt (12:100)",
            "His prayer fulfilled — blessed family (12:101)",
        ],
        "themes": ["patience", "faith", "family", "prophethood", "tawheed"],
    },
    {
        "id": "miraj",
        "name_ar": "الإسراء والمعراج",
        "name_en": "The Night Journey and Ascension",
        "surahs": "Isra 17:1, Najm 53:1-18, Baqarah 2:285",
        "key_events": [
            "Night journey from Masjid al-Haram to Masjid al-Aqsa (17:1)",
            "The Prophet ﷺ led prayers of all prophets in Jerusalem",
            "Ascension through the heavens",
            "Seeing the Sidrat al-Muntaha (53:14-16)",
            "The revelation of 50 then 5 daily prayers",
            "The Prophet ﷺ saw the signs of his Lord (17:1, 53:18)",
            "Described as a trial for people (17:60)",
        ],
        "themes": ["prophethood", "divine_honor", "prayer", "faith", "miracle"],
    },
]

SYSTEM_PROMPT = """You are a Quranic studies assistant. Generate educational summaries for a Quran learning app.
Rules:
- Kids summaries: simple, age-appropriate, 2-3 sentences
- Adults summaries: reference specific Quran verses and classical tafsir sources (Ibn Kathir, Tabari, Qurtubi)
- Always add [needs scholarly verification] to adults summaries
- No extra-Quranic details (no Israiliyyat)
- Arabic text must be fluent Modern Standard Arabic
- Be accurate to what is mentioned in the Quran only
"""


def call_ollama(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 500},
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{OLLAMA_URL}/api/generate",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=120
    )
    try:
        resp = json.loads(result.stdout)
        return resp.get("response", "").strip()
    except Exception as e:
        print(f"Error: {e}, stdout: {result.stdout[:200]}", file=sys.stderr)
        return ""


def generate_story_summaries(spec: dict) -> dict:
    name_en = spec["name_en"]
    name_ar = spec["name_ar"]
    surahs = spec["surahs"]
    events = "\n".join(f"- {e}" for e in spec["key_events"])

    print(f"  Generating kids summary (EN)...", flush=True)
    kids_en = call_ollama(
        f"Write a 2-3 sentence kids summary (ages 7-12) for the story of Prophet {name_en} ({name_ar}) "
        f"in the Quran. Key events from {surahs}:\n{events}\n\nWrite ONLY the kids summary in English."
    )

    print(f"  Generating kids summary (AR)...", flush=True)
    kids_ar = call_ollama(
        f"اكتب ملخصاً بسيطاً للأطفال (3-2 جملة) لقصة النبي {name_ar} في القرآن الكريم. "
        f"الأحداث الرئيسية من {surahs}:\n{events}\n\nاكتب الملخص باللغة العربية الفصحى البسيطة فقط."
    )

    print(f"  Generating adults summary (EN)...", flush=True)
    adults_en = call_ollama(
        f"Write a 3-4 sentence scholarly summary for the story of Prophet {name_en} ({name_ar}) "
        f"in the Quran ({surahs}). Reference Ibn Kathir, Tabari or Qurtubi. "
        f"Key events:\n{events}\n\nWrite ONLY the adults summary in English. "
        f"Add [Reference: Tafsir Ibn Kathir — {surahs.split(',')[0].strip()}, needs verification] at the end."
    )

    print(f"  Generating adults summary (AR)...", flush=True)
    adults_ar = call_ollama(
        f"اكتب ملخصاً علمياً (3-4 جمل) لقصة النبي {name_ar} في القرآن الكريم ({surahs}). "
        f"استشهد بتفسير ابن كثير أو الطبري أو القرطبي. "
        f"الأحداث الرئيسية:\n{events}\n\nاكتب الملخص باللغة العربية الفصحى فقط. "
        f"أضف [المصدر: تفسير ابن كثير، يحتاج تحقق] في النهاية."
    )

    print(f"  Generating core theme (EN/AR)...", flush=True)
    theme_en = call_ollama(
        f"In 5-8 words, what is the core theme of the story of {name_en} in the Quran? "
        f"Write ONLY the theme phrase."
    )
    theme_ar = call_ollama(
        f"في 5-7 كلمات، ما الموضوع الجوهري لقصة {name_ar} في القرآن؟ "
        f"اكتب العبارة باللغة العربية فقط."
    )

    return {
        "kids_en": kids_en,
        "kids_ar": kids_ar,
        "adults_en": adults_en,
        "adults_ar": adults_ar,
        "theme_en": theme_en,
        "theme_ar": theme_ar,
    }


def main():
    print(f"Generating summaries using {MODEL}...")
    results = {}
    for spec in STORY_SPECS:
        sid = spec["id"]
        print(f"\n[{sid}] Processing story: {spec['name_en']} ({spec['name_ar']})")
        summaries = generate_story_summaries(spec)
        results[sid] = {"spec": spec, "summaries": summaries}
        print(f"  Done: {sid}")

    out_path = "/home/mhamdan/tadabbur/scripts/generated_story_summaries.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
