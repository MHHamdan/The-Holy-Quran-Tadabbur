#!/usr/bin/env python3
"""Store screenshots for Google Play and the App Store, in English and Arabic.

Captures the running web app with Playwright (Chromium) at the exact pixel
sizes the stores accept:

    android-phone  1080 x 2340  (Play phone, 9:19.5)
    iphone-6.9     1320 x 2868  (App Store 6.9-inch iPhone)
    ipad-13        2064 x 2752  (App Store 13-inch iPad; required because the
                                 app supports iPad: TARGETED_DEVICE_FAMILY 1,2)

Output: fastlane/screenshots/<device>/<locale>/<NN>_<name>.png, where locale is
en-US or ar (fastlane's metadata folder names).

Usage (a dev stack or a production build must be serving the app):

    python3 scripts/store/screenshots.py --base-url http://localhost:19300
    python3 scripts/store/screenshots.py --devices ipad-13 --locales ar

Screenshots show real app content only (Qur'an text comes from the API, i.e.
the canonical Tanzil text); nothing is mocked or retouched. Review every image
before uploading: store reviewers reject screenshots that show errors or
placeholder data.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fastlane" / "screenshots"

# name: (CSS viewport width, height, device scale factor, mobile)
DEVICES: dict[str, tuple[int, int, int, bool]] = {
    "android-phone": (360, 780, 3, True),     # 1080 x 2340
    "iphone-6.9": (440, 956, 3, True),        # 1320 x 2868
    "ipad-13": (1032, 1376, 2, True),         # 2064 x 2752
}

# (file stem, path). Same order in every locale.
ROUTES: list[tuple[str, str]] = [
    ("home", "/"),
    ("surah-al-fatiha", "/quran/1"),
    ("ayat-al-kursi", "/quran/2?aya=255"),
    ("ask", "/ask"),
    ("prayer-times", "/tools/prayer-times"),
    ("privacy", "/privacy"),
]

LOCALES = {"en-US": "en", "ar": "ar"}


def expected_size(device: str) -> tuple[int, int]:
    w, h, dpr, _ = DEVICES[device]
    return w * dpr, h * dpr


def init_script(lang: str) -> str:
    """Pre-seed the persisted stores so the app opens in `lang` with no dialogs."""
    direction = "rtl" if lang == "ar" else "ltr"
    language = json.dumps({"state": {"language": lang, "direction": direction}, "version": 0})
    persona = json.dumps({"state": {"persona": None, "hasChosen": True}, "version": 0})
    return (
        "try {"
        f"localStorage.setItem('tadabbur-language', {json.dumps(language)});"
        f"localStorage.setItem('tadabbur-persona', {json.dumps(persona)});"
        "} catch (e) {}"
    )


def png_size(path: Path) -> tuple[int, int]:
    """Width and height from the PNG IHDR chunk (no Pillow needed)."""
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def capture(base_url: str, devices: list[str], locales: list[str], settle_ms: int) -> int:
    from playwright.sync_api import sync_playwright

    failures = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for device in devices:
            w, h, dpr, mobile = DEVICES[device]
            for locale in locales:
                lang = LOCALES[locale]
                ctx = browser.new_context(
                    viewport={"width": w, "height": h},
                    device_scale_factor=dpr,
                    is_mobile=mobile,
                    has_touch=mobile,
                    locale="ar" if lang == "ar" else "en-US",
                    # Prayer times: a fixed public location (Makkah) instead of the
                    # machine's, so no personal location ends up in a screenshot.
                    geolocation={"latitude": 21.4225, "longitude": 39.8262},
                    permissions=["geolocation"],
                )
                ctx.add_init_script(init_script(lang))
                page = ctx.new_page()
                out_dir = OUT / device / locale
                out_dir.mkdir(parents=True, exist_ok=True)
                for i, (stem, path) in enumerate(ROUTES, start=1):
                    target = out_dir / f"{i:02d}_{stem}.png"
                    try:
                        page.goto(base_url.rstrip("/") + path, wait_until="networkidle", timeout=60_000)
                        page.wait_for_timeout(settle_ms)
                        page.screenshot(path=str(target), full_page=False)
                    except Exception as exc:  # noqa: BLE001 - report and continue
                        print(f"FAIL {device}/{locale} {path}: {exc}", file=sys.stderr)
                        failures += 1
                        continue
                    size = png_size(target)
                    ok = size == expected_size(device)
                    failures += 0 if ok else 1
                    print(f"{'ok  ' if ok else 'SIZE'} {target.relative_to(ROOT)} {size[0]}x{size[1]}")
                ctx.close()
        browser.close()
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:19300", help="where the web app is served")
    ap.add_argument("--devices", nargs="*", default=list(DEVICES), choices=list(DEVICES))
    ap.add_argument("--locales", nargs="*", default=list(LOCALES), choices=list(LOCALES))
    ap.add_argument("--settle-ms", type=int, default=1500, help="wait after load for fonts and animations")
    args = ap.parse_args()
    failures = capture(args.base_url, args.devices, args.locales, args.settle_ms)
    if failures:
        print(f"{failures} screenshot(s) failed or have the wrong size", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
