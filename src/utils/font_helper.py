"""Font helper — ensures Chinese text is always renderable.

Uses a multi-strategy approach to find a working CJK font:
1. Direct font file paths (most reliable)
2. SysFont by name
3. Pygame default (last resort — cannot render CJK)

Avoids pygame.font.get_fonts() which has a bug with non-ASCII paths.
"""

import os
import pygame

_font_cache = {}

# ── CJK font names for SysFont lookup (priority order) ──────────────
_CJK_FONT_NAMES = [
    "microsoft yahei",
    "simhei",
    "simsun",
    "simkai",
    "dengxian",
    "fangsong",
    "kaiti",
    "nsimsun",
    "youyuan",
    "fzyaoti",
    "stzhongsong",
    "stkaiti",
    "stfangsong",
]

# ── Known CJK font file paths on Windows ────────────────────────────
_CJK_FONT_PATHS = []


def _build_font_paths():
    """Collect known CJK font file paths from the system."""
    font_dirs = []

    # Windows font directory
    windir = os.environ.get("WINDIR", "C:\\Windows")
    win_font_dir = os.path.join(windir, "Fonts")
    if os.path.isdir(win_font_dir):
        font_dirs.append(win_font_dir)

    # Known CJK font filenames
    cjk_files = [
        "msyh.ttc", "msyh.ttf",
        "simhei.ttf",
        "simsun.ttc", "simsun.ttf",
        "simkai.ttf",
        "DengXian.ttf", "Deng.ttf",
        "FangSong.ttf", "Fangsong.ttf",
        "KaiTi.ttf",
        "YouYuan.ttf",
        "STZHONGS.ttf",
        "STKAITI.ttf",
        "STFANGSO.ttf",
    ]

    paths = []
    for d in font_dirs:
        for fname in cjk_files:
            fpath = os.path.join(d, fname)
            if os.path.isfile(fpath):
                paths.append(fpath)
    return paths


_CJK_FONT_PATHS = _build_font_paths()


def _verify_cjk(font):
    """Return True if *font* renders real CJK glyphs, not tofu/boxes.

    Strategy: render a CJK character and a Latin 'A'.  If the font
    doesn't have CJK glyphs it will render a replacement glyph (tofu)
    whose width usually equals the Latin glyph width.  A real CJK
    glyph is typically wider than a Latin letter at the same size.
    """
    try:
        cjk = font.render("\u5929", True, (255, 255, 255))   # 天
        latin = font.render("A", True, (255, 255, 255))

        cjk_w = cjk.get_width()
        latin_w = latin.get_width()

        # Tofu replacement glyph almost always matches Latin width.
        # A real CJK glyph at the same font size is wider.
        if cjk_w <= latin_w:
            return False

        # Extra sanity: try a second CJK glyph
        cjk2 = font.render("\u5730", True, (255, 255, 255))  # 地
        if cjk2.get_width() <= latin_w:
            return False

        return True
    except Exception:
        return False


def get_font(size=24):
    """Return a pygame Font that can render Chinese text."""
    key = (None, size)
    if key in _font_cache:
        return _font_cache[key]

    # Strategy 1: direct font file paths (most reliable)
    for fpath in _CJK_FONT_PATHS:
        try:
            font = pygame.font.Font(fpath, size)
            if _verify_cjk(font):
                _font_cache[key] = font
                return font
        except Exception:
            continue

    # Strategy 2: SysFont by name
    for name in _CJK_FONT_NAMES:
        try:
            font = pygame.font.SysFont(name, size)
            if _verify_cjk(font):
                _font_cache[key] = font
                return font
        except Exception:
            continue

    # Strategy 3: pygame default fallback (will NOT render CJK)
    font = pygame.font.Font(None, size)
    _font_cache[key] = font
    return font
