"""
App-shell smoke test: navigation, 404, dialogs, fonts, location privacy and
axe-core accessibility checks.

Run against a running frontend (vite dev or preview):

    BASE_URL=http://localhost:19347 python3 e2e/shell_a11y_smoke.py

Requires the Python `playwright` package with Chromium, and axe-core from
frontend/node_modules (a devDependency). Exits non-zero on any failure.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = os.environ.get("BASE_URL", "http://localhost:19347").rstrip("/")
AXE = (Path(__file__).resolve().parent.parent / "node_modules" / "axe-core" / "axe.min.js").read_text()
PERSONA = json.dumps({"state": {"persona": None, "hasChosen": True}, "version": 0})
FAILURES: list[str] = []
NAV_PATHS = [
    "/continue", "/explore", "/ask", "/memorise",
    "/mushaf", "/quran",
    "/search", "/stories", "/prophets", "/themes", "/concepts", "/surah-atlas", "/tafsir/compare",
    "/asma-allah", "/asbab", "/quranic-calls", "/timeline", "/roots", "/tools/vocabulary", "/miracles",
    "/tasmee", "/flashcards", "/memorization", "/tools/surah-memory-atlas", "/compare", "/quiz",
    "/therapy", "/guidance", "/journal", "/challenge", "/tools/prompt-guide",
    "/bookmarks", "/reading-plan", "/stats",
    "/tools/prayer-times", "/tools/maps", "/tools/calendar", "/dhikr", "/duas", "/tools/finance", "/tools/trips", "/tools",
    "/learn", "/names", "/about", "/sources", "/privacy", "/licenses",
    "/tools/books", "/tools/videos", "/tools/web",
]


def check(cond: bool, msg: str) -> None:
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILURES.append(msg)


def new_page(browser, lang: str, width: int, **ctx) -> Page:
    context = browser.new_context(viewport={"width": width, "height": 860}, locale="ar-SA" if lang == "ar" else "en-US", **ctx)
    language = json.dumps({"state": {"language": lang, "direction": "rtl" if lang == "ar" else "ltr"}, "version": 0})
    context.add_init_script(
        f"localStorage.setItem('tadabbur-persona', {json.dumps(PERSONA)});"
        f"localStorage.setItem('tadabbur-language', {json.dumps(language)});"
    )
    # Nothing in these checks needs third-party hosts; never call them.
    context.route(
        "**/*",
        lambda route: route.abort()
        if not route.request.url.startswith(BASE) and not route.request.url.startswith("data:")
        else route.continue_(),
    )
    page = context.new_page()
    page.errors = []  # type: ignore[attr-defined]
    page.on("pageerror", lambda e: page.errors.append(str(e)))  # type: ignore[attr-defined]
    return page


def axe(page: Page, include: list[str] | None = None, rules: list[str] | None = None) -> list[dict]:
    page.add_script_tag(content=AXE)
    ctx = json.dumps({"include": [[s] for s in include]} if include else {"exclude": []})
    opts = json.dumps({"runOnly": {"type": "rule", "values": rules}} if rules else {"resultTypes": ["violations"]})
    res = page.evaluate(f"async () => (await axe.run({ctx}, {opts})).violations")
    return [v for v in res if v.get("impact") in ("serious", "critical")]


def summarize(violations: list[dict]) -> str:
    return ", ".join(f"{v['id']}({len(v['nodes'])})" for v in violations) or "none"


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # 1. Mobile shell at three widths, both languages
        for width in (360, 390, 412):
            for lang in ("ar", "en"):
                page = new_page(browser, lang, width)
                page.goto(BASE + "/", wait_until="networkidle")
                tabs = page.locator("nav.fixed li")
                check(tabs.count() == 5, f"[{lang} {width}] bottom bar has 5 tabs (got {tabs.count()})")
                header_h = page.evaluate("document.querySelector('header').getBoundingClientRect().height")
                check(header_h <= 64, f"[{lang} {width}] header height {header_h}px <= 64")
                sw = page.evaluate("document.documentElement.scrollWidth")
                check(sw <= width, f"[{lang} {width}] no horizontal scroll (scrollWidth {sw})")
                page.keyboard.press("Tab")
                first = page.evaluate("document.activeElement && document.activeElement.getAttribute('href')")
                check(first == "#main", f"[{lang} {width}] first Tab reaches the skip link (got {first})")
                page.context.close()

        # 2. Every nav path is reachable within two taps (tab, then hub/sheet item)
        page = new_page(browser, "en", 390)
        reachable: set[str] = set()
        page.goto(BASE + "/", wait_until="networkidle")
        reachable |= set(page.eval_on_selector_all("nav.fixed a", "els => els.map(e => e.getAttribute('href'))"))
        page.click("nav.fixed button")  # More
        page.wait_for_selector("[role=dialog]")
        reachable |= set(page.eval_on_selector_all("[role=dialog] a", "els => els.map(e => e.getAttribute('href'))"))
        page.keyboard.press("Escape")
        for hub in ("/explore", "/memorise"):
            page.goto(BASE + hub, wait_until="networkidle")
            reachable |= set(page.eval_on_selector_all("main a", "els => els.map(e => e.getAttribute('href'))"))
        missing = [p for p in NAV_PATHS if p not in reachable and p not in ("/continue", "/quran")]
        check(not missing, f"all nav paths reachable in 2 taps (missing: {missing})")
        check("/status" not in reachable and not any(h and h.startswith("/admin") for h in reachable), "no /status or /admin links in the shell")
        page.context.close()

        # 3. 404 is localized
        for lang, title in (("ar", "الصفحة غير موجودة"), ("en", "Page not found")):
            page = new_page(browser, lang, 390)
            page.goto(BASE + "/nonexistent-route", wait_until="networkidle")
            h1 = page.text_content("main h1") or ""
            check(title in h1, f"[{lang}] /nonexistent-route shows '{title}' (got '{h1}')")
            page.context.close()

        # 4. Feedback dialog: role, focus inside, Escape closes and restores focus
        page = new_page(browser, "ar", 390)
        page.goto(BASE + "/stories", wait_until="networkidle")
        fab = page.locator("button.fab-offset")
        check(fab.count() == 1, "feedback button present on /stories")
        fab.click()
        page.wait_for_selector("[role=dialog][aria-modal=true]")
        inside = page.evaluate("!!document.activeElement.closest('[role=dialog]')")
        check(inside, "focus moves into the feedback dialog")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        closed = page.locator("[role=dialog]").count() == 0
        restored = page.evaluate("document.activeElement.classList.contains('fab-offset')")
        check(closed and restored, "Escape closes the dialog and focus returns to the button")
        page.goto(BASE + "/mushaf", wait_until="domcontentloaded")
        page.wait_for_timeout(500)
        check(page.locator("button.fab-offset").count() == 0, "no floating feedback button on /mushaf")
        page.context.close()

        # 5. Uthmani font: Scheherazade New wins in the Arabic UI, self-hosted
        page = new_page(browser, "ar", 390)
        page.goto(BASE + "/", wait_until="networkidle")
        fam = page.evaluate(
            """async () => {
              const d = document.createElement('div');
              d.dir = 'rtl'; d.className = 'font-mushaf'; d.textContent = 'بسم';
              document.querySelector('main').appendChild(d);
              await document.fonts.load('16px "Scheherazade New"', 'بسم');
              return [getComputedStyle(d).fontFamily, document.fonts.check('16px "Scheherazade New"', 'بسم')];
            }"""
        )
        check(fam[0].startswith('"Scheherazade New"') and fam[1], f"[ar] .font-mushaf uses self-hosted Scheherazade New ({fam})")
        page.context.close()

        # 6. Location leaves the device rounded to 2 decimals
        page = new_page(
            browser, "en", 390,
            geolocation={"latitude": 21.422487, "longitude": 39.826206}, permissions=["geolocation"],
        )
        sent: list[str] = []
        page.on("request", lambda r: sent.append((r.url + " " + (r.post_data or ""))) if any(
            h in r.url for h in ("aladhan", "nominatim", "overpass")) else None)
        page.goto(BASE + "/tools/prayer-times", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.goto(BASE + "/tools/maps", wait_until="networkidle")
        page.wait_for_timeout(1500)
        precise = [s for s in sent if "21.4224" in s or "39.8262" in s]
        check(bool(sent) and not precise, f"location requests use ~1 km precision ({len(sent)} requests, precise: {precise[:2]})")
        page.context.close()

        # 7. Zakat: warning instead of stale prices, no goldapi call
        page = new_page(browser, "ar", 390)
        calls: list[str] = []
        page.on("request", lambda r: calls.append(r.url) if "goldapi" in r.url else None)
        page.goto(BASE + "/tools/finance", wait_until="networkidle")
        check(page.locator("#zakat-gold-price").count() == 1, "zakat shows manual gold price input")
        check(page.input_value("#zakat-gold-price") == "", "manual price input starts empty")
        check(not calls, "no goldapi.io request")
        page.context.close()

        # 8. /compare loads without a page error
        for lang in ("ar", "en"):
            page = new_page(browser, lang, 412)
            page.goto(BASE + "/compare", wait_until="networkidle")
            page.wait_for_timeout(800)
            check(not page.errors, f"[{lang}] /compare has no page error ({page.errors[:1]})")  # type: ignore[attr-defined]
            page.context.close()

        # 9. axe: shell pages fully clean; home hero/header/nav/footer clean
        for lang in ("ar", "en"):
            for route in ("/explore", "/memorise", "/more", "/about", "/nonexistent-route"):
                page = new_page(browser, lang, 360)
                page.goto(BASE + route, wait_until="networkidle")
                v = axe(page)
                check(not v, f"[{lang}] axe {route}: serious/critical {summarize(v)}")
                page.context.close()
            page = new_page(browser, lang, 360)
            page.goto(BASE + "/", wait_until="networkidle")
            v = axe(page, include=["header", "nav.fixed", "footer", "main > div > section:first-child"])
            check(not v, f"[{lang}] axe / (shell + hero): serious/critical {summarize(v)}")
            full = axe(page)
            print(f"INFO [{lang}] axe / full page (other workstreams' components included): {summarize(full)}")
            page.context.close()

        browser.close()

    print(f"\n{len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
