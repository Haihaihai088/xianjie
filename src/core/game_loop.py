"""Game loop with state machine.

States: INTRO, MENU, LEVEL_SELECT, LEVEL_INTRO, PLAYING,
        LEVEL_CLEAR, CHAPTER_BREAK, GAME_OVER, ENDING
"""

import sys
from enum import Enum, auto

import pygame


class GameState(Enum):
    INTRO = auto()
    MENU = auto()
    LEVEL_SELECT = auto()
    LEVEL_INTRO = auto()
    PLAYING = auto()
    LEVEL_CLEAR = auto()
    CHAPTER_BREAK = auto()
    GAME_OVER = auto()
    ENDING = auto()


class GameLoop:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    def __init__(self):
        self.screen = pygame.display.set_mode(
            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        )
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.INTRO

        # Shared game data that all states can access
        self.game_data = {
            "current_level": 0,
            "total_score": 0,
            "level_scores": [],       # per-level score list
            "chapter_scores": [],     # every 5 levels summary
            "rare_bonus": 0,          # cumulative rare rate bonus
            "highest_combo": 0,
            "perfect_levels": 0,
        }

        # Preload UI assets
        self._load_assets()

    def _load_assets(self):
        """Load and cache shared UI images (keep original aspect ratio)."""
        import os
        self.assets = {}

        for key, fname in [("menu_bg", "menu_bg.png"), ("battle_bg", "battle_bg.png"), ("ending_bg", "ending_bg.png")]:
            for p in [os.path.join("ui", fname), os.path.join("..", "ui", fname)]:
                if os.path.exists(p):
                    try:
                        self.assets[key] = pygame.image.load(p).convert()
                        break
                    except Exception:
                        pass

        # State handlers (lazy-loaded to avoid circular imports)
        self._state_handlers = {}

        # Delta time for frame-independent updates
        self.dt = 0.0

    def draw_bg(self, key):
        """Return a surface with the background drawn, preserving aspect ratio.
        Scales to fit height, centers horizontally (crops wide edges)."""
        img = self.assets.get(key)
        if img is None:
            return None

        iw, ih = img.get_size()
        scale = self.SCREEN_HEIGHT / ih
        new_w = int(iw * scale)
        new_h = self.SCREEN_HEIGHT
        scaled = pygame.transform.smoothscale(img, (new_w, new_h))

        surf = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        # Center horizontally
        x_offset = (self.SCREEN_WIDTH - new_w) // 2
        surf.blit(scaled, (x_offset, 0))
        return surf

    def run(self):
        while self.running:
            self.dt = self.clock.tick(self.FPS) / 1000.0
            self._handle_events()
            self._update()
            self._render()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            self._dispatch_event(event)

    def _dispatch_event(self, event):
        handler = self._state_handlers.get(self.state)
        if handler and hasattr(handler, "handle_event"):
            handler.handle_event(event, self)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def _update(self):
        handler = self._state_handlers.get(self.state)
        if handler and hasattr(handler, "update"):
            handler.update(self)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def _render(self):
        self.screen.fill((18, 16, 24))  # deep ink-black background

        handler = self._state_handlers.get(self.state)
        if handler and hasattr(handler, "render"):
            handler.render(self.screen, self)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------
    def register_handler(self, state, handler):
        self._state_handlers[state] = handler

    def switch_state(self, new_state):
        old_handler = self._state_handlers.get(self.state)
        if old_handler and hasattr(old_handler, "exit"):
            old_handler.exit(self)

        self.state = new_state

        new_handler = self._state_handlers.get(self.state)
        if new_handler and hasattr(new_handler, "enter"):
            new_handler.enter(self)

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------
    def save_game(self):
        """Save current game_data to save.json."""
        import json, os
        data = {
            "current_level": self.game_data["current_level"],
            "total_score": self.game_data["total_score"],
            "level_scores": self.game_data["level_scores"],
            "chapter_scores": self.game_data["chapter_scores"],
            "rare_bonus": self.game_data["rare_bonus"],
            "highest_combo": self.game_data["highest_combo"],
            "perfect_levels": self.game_data["perfect_levels"],
        }
        path = os.path.join("saves", "save.json")
        os.makedirs("saves", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_game(self):
        """Load saved game_data. Returns True if save existed."""
        import json, os
        path = os.path.join("saves", "save.json")
        if not os.path.exists(path):
            path = os.path.join("..", "saves", "save.json")
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in data:
            self.game_data[key] = data[key]
        return True

    def quit(self):
        self.running = False
