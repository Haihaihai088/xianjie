"""Story text renderer with typewriter effect.

Supports character-by-character reveal, line-by-line advancement,
and skip-on-click/keypress.
"""

import pygame
from src.utils.font_helper import get_font


class StoryRenderer:
    """Renders multi-line story text with a typewriter animation.

    Usage:
        renderer = StoryRenderer(lines, screen_width, screen_height)
        renderer.start()

        # Each frame:
        renderer.update(dt)
        renderer.render(screen)

        # Check completion:
        if renderer.finished:
            ...
    """

    CHAR_INTERVAL = 0.04   # seconds per character
    LINE_PAUSE = 0.3       # extra pause at end of each line
    FADE_SPEED = 2.0       # alpha per second

    def __init__(self, lines, screen_width, screen_height, font_size=26):
        self.lines = lines
        self.sw = screen_width
        self.sh = screen_height
        self._font_size = font_size
        self.font = None
        self.small_font = None

        self.char_timer = 0.0
        self.line_index = 0
        self.char_index = 0
        self.finished = False
        self.skippable = True
        self.alpha = 255

    def start(self):
        self.char_timer = 0.0
        self.line_index = 0
        self.char_index = 0
        self.finished = False
        self.alpha = 255

    def skip(self):
        """Instantly reveal all text."""
        if self.finished:
            return
        self.finished = True

    def update(self, dt):
        if self.finished:
            return

        self.char_timer += dt
        current_line = self.lines[self.line_index] if self.line_index < len(self.lines) else ""

        if self.char_index < len(current_line):
            # Still revealing current line
            while self.char_timer >= self.CHAR_INTERVAL and self.char_index < len(current_line):
                self.char_timer -= self.CHAR_INTERVAL
                self.char_index += 1
        else:
            # Line fully revealed — pause then advance
            if self.char_timer >= self.LINE_PAUSE:
                self.char_timer = 0.0
                self.char_index = 0
                self.line_index += 1
                if self.line_index >= len(self.lines):
                    self.finished = True

    def render(self, screen):
        """Draw revealed text centered on screen."""
        if self.font is None:
            self.font = get_font( self._font_size)
            self.small_font = get_font( 18)

        # Calculate total height of visible lines
        line_h = 34
        visible_lines = self._visible_lines()
        total_h = len(visible_lines) * line_h
        start_y = self.sh // 2 - total_h // 2

        for i, line_text in enumerate(visible_lines):
            y = start_y + i * line_h
            if not line_text:
                continue

            color = (235, 215, 175)  # warm beige for dark bg
            suf = self.font.render(line_text, True, color)
            suf_rect = suf.get_rect(center=(self.sw // 2, y))
            screen.blit(suf, suf_rect)

        # Skippable hint
        if not self.finished and self.skippable:
            hint = self.small_font.render("点击或按空格跳过", True, (140, 120, 90))
            screen.blit(hint, hint.get_rect(center=(self.sw // 2, self.sh - 30)))

    def _visible_lines(self):
        result = []
        for i in range(self.line_index):
            result.append(self.lines[i])  # fully revealed
        if self.line_index < len(self.lines):
            partial = self.lines[self.line_index][:self.char_index]
            result.append(partial)
        return result

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.skip()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.skip()
