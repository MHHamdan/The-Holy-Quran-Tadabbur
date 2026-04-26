#!/usr/bin/env python3
"""
Download Quran audio fixtures for integration testing.

Uses EveryAyah.com which provides free verse-by-verse Quran recitation.
Audio is licensed for personal and educational use.

Reciters available:
- Alafasy_128kbps (Mishary Rashid Al Afasy) - Clear, popular recitation
- Husary_128kbps (Mahmoud Khalil Al-Husary) - Classic, precise tajweed
- Minshawi_Murattal_128kbps (Mohamed Siddiq El-Minshawi)

Usage:
    python download_fixtures.py
    python download_fixtures.py --reciter Husary_128kbps
"""

import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
import subprocess
import argparse

# Base URL for EveryAyah.com
EVERYAYAH_BASE_URL = "https://everyayah.com/data"

# Default reciter (clear pronunciation, good for STT)
DEFAULT_RECITER = "Alafasy_128kbps"

# Test verses to download (surah_no, ayah_no, description)
TEST_VERSES = [
    (1, 1, "bismillah"),           # بسم الله الرحمن الرحيم
    (1, 2, "alhamdulillah"),       # الحمد لله رب العالمين
    (1, 3, "arrahman"),            # الرحمن الرحيم
    (1, 4, "maliki"),              # مالك يوم الدين
    (1, 5, "iyyaka"),              # إياك نعبد وإياك نستعين
    (1, 6, "ihdina"),              # اهدنا الصراط المستقيم
    (1, 7, "sirat"),               # صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالين
    (112, 1, "ikhlas_1"),          # قل هو الله أحد
    (112, 2, "ikhlas_2"),          # الله الصمد
    (112, 3, "ikhlas_3"),          # لم يلد ولم يولد
    (112, 4, "ikhlas_4"),          # ولم يكن له كفوا أحد
    (2, 255, "ayat_kursi"),        # آية الكرسي
]

# Expected text for each verse (for test verification)
VERSE_TEXTS = {
    (1, 1): "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
    (1, 2): "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
    (1, 3): "الرَّحْمَٰنِ الرَّحِيمِ",
    (1, 4): "مَالِكِ يَوْمِ الدِّينِ",
    (1, 5): "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
    (1, 6): "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ",
    (1, 7): "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
    (112, 1): "قُلْ هُوَ اللَّهُ أَحَدٌ",
    (112, 2): "اللَّهُ الصَّمَدُ",
    (112, 3): "لَمْ يَلِدْ وَلَمْ يُولَدْ",
    (112, 4): "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
    (2, 255): "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ",
}


def get_audio_url(surah: int, ayah: int, reciter: str = DEFAULT_RECITER) -> str:
    """Generate EveryAyah.com URL for a specific verse."""
    # Format: SSSAAA.mp3 (e.g., 001001.mp3 for 1:1)
    filename = f"{surah:03d}{ayah:03d}.mp3"
    return f"{EVERYAYAH_BASE_URL}/{reciter}/{filename}"


def get_output_path(surah: int, ayah: int, description: str, output_dir: Path) -> Path:
    """Generate output file path."""
    return output_dir / f"{surah:03d}_{ayah:03d}_{description}.mp3"


def get_wav_path(mp3_path: Path) -> Path:
    """Get corresponding WAV path for MP3 file."""
    return mp3_path.with_suffix(".wav")


def download_file(url: str, output_path: Path) -> bool:
    """Download file from URL."""
    try:
        print(f"  Downloading: {url}")
        urllib.request.urlretrieve(url, output_path)
        print(f"  Saved to: {output_path}")
        return True
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {url}")
        return False
    except urllib.error.URLError as e:
        print(f"  URL Error: {e.reason}")
        return False


def convert_to_wav(mp3_path: Path, wav_path: Path, sample_rate: int = 16000) -> bool:
    """Convert MP3 to WAV format suitable for STT (16kHz mono PCM)."""
    try:
        # Use ffmpeg for conversion
        cmd = [
            "ffmpeg", "-y", "-i", str(mp3_path),
            "-ar", str(sample_rate),  # Sample rate
            "-ac", "1",                # Mono
            "-c:a", "pcm_s16le",       # 16-bit PCM
            str(wav_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  Converted to WAV: {wav_path}")
            return True
        else:
            print(f"  FFmpeg error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("  Warning: ffmpeg not found. Install with: sudo apt install ffmpeg")
        return False


def download_all_fixtures(output_dir: Path, reciter: str = DEFAULT_RECITER,
                          convert_wav: bool = True) -> dict:
    """Download all test audio fixtures."""
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "downloaded": [],
        "skipped": [],
        "failed": [],
        "converted": [],
    }

    print(f"\nDownloading Quran audio fixtures from EveryAyah.com")
    print(f"Reciter: {reciter}")
    print(f"Output: {output_dir}\n")

    for surah, ayah, description in TEST_VERSES:
        mp3_path = get_output_path(surah, ayah, description, output_dir)
        wav_path = get_wav_path(mp3_path)

        print(f"Verse {surah}:{ayah} ({description}):")

        # Check if already downloaded
        if mp3_path.exists():
            print(f"  Already exists: {mp3_path}")
            results["skipped"].append((surah, ayah))
        else:
            url = get_audio_url(surah, ayah, reciter)
            if download_file(url, mp3_path):
                results["downloaded"].append((surah, ayah))
            else:
                results["failed"].append((surah, ayah))
                continue

        # Convert to WAV if requested
        if convert_wav and not wav_path.exists():
            if convert_to_wav(mp3_path, wav_path):
                results["converted"].append((surah, ayah))
        elif wav_path.exists():
            print(f"  WAV already exists: {wav_path}")

    # Create metadata file
    metadata_path = output_dir / "metadata.py"
    write_metadata(metadata_path, reciter)

    print(f"\n{'='*50}")
    print(f"Download Summary:")
    print(f"  Downloaded: {len(results['downloaded'])}")
    print(f"  Skipped (existing): {len(results['skipped'])}")
    print(f"  Failed: {len(results['failed'])}")
    print(f"  Converted to WAV: {len(results['converted'])}")

    if results["failed"]:
        print(f"\nFailed verses: {results['failed']}")

    return results


def write_metadata(path: Path, reciter: str):
    """Write metadata file for test fixtures."""
    content = f'''"""
Audio fixture metadata for Tasmeeʿ integration tests.

Source: EveryAyah.com
Reciter: {reciter}
License: Free for personal and educational use

This file is auto-generated by download_fixtures.py
"""

RECITER = "{reciter}"

# Verse texts (with tashkeel)
VERSE_TEXTS = {repr(VERSE_TEXTS)}

# Test verses available
TEST_VERSES = {repr([(s, a, d) for s, a, d in TEST_VERSES])}


def get_audio_path(surah: int, ayah: int, format: str = "wav") -> str:
    """Get path to audio file for a verse."""
    from pathlib import Path
    base_dir = Path(__file__).parent

    for s, a, desc in TEST_VERSES:
        if s == surah and a == ayah:
            return str(base_dir / f"{{s:03d}}_{{a:03d}}_{{desc}}.{{format}}")

    raise ValueError(f"No audio fixture for {{surah}}:{{ayah}}")


def get_verse_text(surah: int, ayah: int) -> str:
    """Get expected text for a verse."""
    return VERSE_TEXTS.get((surah, ayah), "")
'''

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nMetadata written to: {path}")


def check_dependencies():
    """Check required dependencies."""
    issues = []

    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except FileNotFoundError:
        issues.append("ffmpeg not found. Install with: sudo apt install ffmpeg")

    return issues


def main():
    parser = argparse.ArgumentParser(description="Download Quran audio test fixtures")
    parser.add_argument(
        "--reciter",
        default=DEFAULT_RECITER,
        help=f"Reciter name (default: {DEFAULT_RECITER})"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: same as script)"
    )
    parser.add_argument(
        "--no-wav",
        action="store_true",
        help="Skip WAV conversion"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check dependencies, don't download"
    )

    args = parser.parse_args()

    # Check dependencies
    issues = check_dependencies()
    if issues:
        print("Dependency issues found:")
        for issue in issues:
            print(f"  - {issue}")
        if args.check:
            sys.exit(1 if issues else 0)
        if not args.no_wav:
            print("\nWAV conversion will be skipped. Use --no-wav to suppress this warning.")

    if args.check:
        print("All dependencies OK!")
        return

    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent

    # Download fixtures
    results = download_all_fixtures(
        output_dir=output_dir,
        reciter=args.reciter,
        convert_wav=not args.no_wav
    )

    # Exit with error if any downloads failed
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
