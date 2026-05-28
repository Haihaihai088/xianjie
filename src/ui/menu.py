"""Main menu and level-select screen."""

import random
import pygame
from src.core.game_loop import GameState
from src.utils.font_helper import get_font

# Warm calamity palette — "大劫难" atmosphere
BG_COLOR = (15, 10, 8)
TITLE_GOLD = (255, 225, 100)
TEXT_WARM = (235, 215, 175)
TEXT_MUTED = (180, 155, 120)
BTN_BG = (30, 20, 12)
BTN_BORDER_GOLD = (200, 165, 90)
BTN_BORDER_BLUE = (140, 170, 190)
BTN_BORDER_GHOST = (120, 90, 60)
BTN_PRIMARY_COLOR = (255, 240, 200)
BTN_HOVER_BG = (45, 30, 16)
BOSS_RED = (200, 70, 50)
BOSS_BG = (50, 15, 15)
CELL_UNLOCKED = (25, 18, 14)
CELL_LOCKED = (12, 10, 8)
CELL_BORDER = (70, 55, 40)
CELL_BORDER_SEL = (255, 220, 80)

# Ash particle for menu atmosphere
class AshParticle:
    __slots__ = ("x", "y", "size", "speed", "drift", "alpha", "life", "max_life")
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(h * 0.3, h)
        self.size = random.uniform(1.5, 8)
        self.speed = random.uniform(15, 45)
        self.drift = random.uniform(-15, 15)
        self.life = random.uniform(0, 12)
        self.max_life = self.life
        self.alpha = random.randint(60, 160)
    def update(self, dt, w, h):
        self.life -= dt
        if self.life <= 0:
            self.life = random.uniform(8, 14)
            self.max_life = self.life
            self.x = random.uniform(0, w)
            self.y = h + random.uniform(0, 40)
            self.alpha = random.randint(60, 160)
        self.y -= self.speed * dt
        self.x += self.drift * dt
        if self.y < -20:
            self.y = h + random.uniform(0, 40)
            self.x = random.uniform(0, w)
    def render(self, screen):
        ratio = max(0, min(1, self.life / max(0.1, self.max_life)))
        a = min(255, int(self.alpha * (0.4 + 0.6 * ratio)))
        s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (60, 45, 30, a), (int(self.size), int(self.size)), self.size)
        screen.blit(s, (self.x - self.size, self.y - self.size))


class MenuState:
    """Main menu with options: Start, Level Select, Quit."""

    def __init__(self):
        self.options = []
        self.selected = 0
        self._alpha = 0.0
        self._fade_in = True
        self._ashes = []

    def enter(self, game):
        self._alpha = 0.0
        self._fade_in = True

        # Check if save exists (don't load yet — just check file)
        import os
        save_paths = [os.path.join("saves", "save.json"), os.path.join("..", "saves", "save.json")]
        self._has_save = any(os.path.exists(p) for p in save_paths)

        # Build options
        self.options = []
        if self._has_save:
            self.options.append(("继续游戏", "continue", (255, 240, 180)))
        self.options += [
            ("开始渡劫", "start", BTN_PRIMARY_COLOR),
            ("选择关卡", "level_select", (200, 190, 210)),
            ("退出", "quit", (180, 150, 130)),
        ]
        self.selected = 0

        w, h = game.SCREEN_WIDTH, game.SCREEN_HEIGHT
        self._ashes = [AshParticle(w, h) for _ in range(40)]

    def update(self, game):
        if self._fade_in:
            self._alpha = min(1.0, self._alpha + game.dt * 1.2)
        for a in self._ashes:
            a.update(game.dt, game.SCREEN_WIDTH, game.SCREEN_HEIGHT)

    def render(self, screen, game):
        cx = game.SCREEN_WIDTH // 2
        cy = game.SCREEN_HEIGHT // 2

        # Background image or fallback (aspect ratio preserved)
        bg = game.draw_bg("menu_bg")
        if bg:
            screen.blit(bg, (0, 0))
            # Ash particles on top of bg
            for a in self._ashes:
                a.render(screen)
            # Dark overlay for text readability
            overlay = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 5, 3, 140))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)

        # No title, no subtitle, no divider — clean background image

        # Menu buttons with frosted-glass feel
        option_font = get_font(32)
        for i, (text, key, color) in enumerate(self.options):
            y = cy - 20 + i * 50
            is_sel = (i == self.selected)

            # Button background
            bw, bh = 240, 42
            br = pygame.Rect(cx - bw // 2, y - bh // 2, bw, bh)

            # Semi-transparent dark pill
            btn_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bg_alpha = 180 if is_sel else 100
            btn_surf.fill((25, 15, 8, bg_alpha))
            screen.blit(btn_surf, (br.x, br.y))

            # Border
            if is_sel:
                border_c = TITLE_GOLD
                border_w = 2
            elif key == "start":
                border_c = BTN_BORDER_GOLD
                border_w = 1
            elif key == "level_select":
                border_c = BTN_BORDER_BLUE
                border_w = 1
            else:
                border_c = BTN_BORDER_GHOST
                border_w = 1
            pygame.draw.rect(screen, border_c, br, border_w, border_radius=20)

            # Text
            txt_color = (255, 248, 220) if is_sel else color
            opt = option_font.render(text, True, txt_color)
            screen.blit(opt, opt.get_rect(center=(cx, y)))

            # Selection indicator beads
            if is_sel:
                dot_font = get_font(20)
                for dx, sign in [(-bw//2 + 14, ">"), (bw//2 - 14, "<")]:
                    d = dot_font.render(sign, True, TITLE_GOLD)
                    screen.blit(d, (cx + dx - d.get_width()//2, y - d.get_height()//2))

    def handle_event(self, event, game):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select(game)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            cx = game.SCREEN_WIDTH // 2
            cy = game.SCREEN_HEIGHT // 2
            mx, my = event.pos
            for i in range(len(self.options)):
                y = cy - 20 + i * 50
                if abs(mx - cx) < 130 and abs(my - y) < 22:
                    self.selected = i
                    self._select(game)

    def _select(self, game):
        key = self.options[self.selected][1]
        if key == "continue":
            game.load_game()  # Load the save now
            game.switch_state(GameState.LEVEL_INTRO)
        elif key == "start":
            game.game_data["current_level"] = 0
            game.game_data["rare_bonus"] = 0
            game.game_data["level_scores"] = []
            game.game_data["total_score"] = 0
            # Delete old save
            import os
            for p in [os.path.join("saves", "save.json"), os.path.join("..", "saves", "save.json")]:
                if os.path.exists(p):
                    os.remove(p)
            game.switch_state(GameState.INTRO)
        elif key == "level_select":
            game.switch_state(GameState.LEVEL_SELECT)
        elif key == "quit":
            game.quit()


class LevelSelectState:
    """Grid of 10 levels, only unlocked ones are playable."""

    def __init__(self):
        self.selected = 0
        self.highest_unlocked = 0

    def enter(self, game):
        self.selected = 0
        scores = game.game_data.get("level_scores", [])
        self.highest_unlocked = len(scores)
        self._scores = scores

    def update(self, game):
        pass

    def render(self, screen, game):
        cx = game.SCREEN_WIDTH // 2

        # Background
        bg = game.draw_bg("menu_bg")
        if bg:
            screen.blit(bg, (0, 0))
            overlay = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 5, 3, 150))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)

        # Header
        header_font = get_font(38)
        h = header_font.render("选择天劫", True, TITLE_GOLD)
        screen.blit(h, h.get_rect(center=(cx, 38)))

        # Level grid: 2 rows of 5
        level_names = [
            "风劫", "火劫", "雷劫", "冰劫", "五行劫",
            "阴阳劫", "时空劫", "寂灭劫", "轮回劫", "心魔劫"
        ]

        cell_w, cell_h = 130, 70
        gap_x, gap_y = 20, 15
        grid_w = 5 * (cell_w + gap_x) - gap_x
        start_x = cx - grid_w // 2
        start_y = 75

        small_font = get_font(20)
        mid_font = get_font(22)

        for i in range(10):
            row = i // 5
            col = i % 5
            x = start_x + col * (cell_w + gap_x)
            y = start_y + row * (cell_h + gap_y)
            rect = pygame.Rect(x, y, cell_w, cell_h)

            unlocked = i <= self.highest_unlocked
            is_boss = i in (4, 9)
            is_sel = (i == self.selected)

            # Cell background
            if is_boss and unlocked:
                bg_color = BOSS_BG
            elif unlocked:
                bg_color = CELL_UNLOCKED
            else:
                bg_color = CELL_LOCKED

            pygame.draw.rect(screen, bg_color, rect, border_radius=6)

            # Border
            if is_sel:
                border_color = CELL_BORDER_SEL
                border_w = 2
            elif is_boss and unlocked:
                border_color = BOSS_RED
                border_w = 2
            elif unlocked:
                border_color = CELL_BORDER
                border_w = 1
            else:
                border_color = (35, 25, 20)
                border_w = 1

            pygame.draw.rect(screen, border_color, rect, border_w, border_radius=6)

            # Level number
            num_color = (235, 215, 180) if unlocked else (80, 70, 60)
            num_text = mid_font.render(f"第{i + 1}重", True, num_color)
            screen.blit(num_text, num_text.get_rect(center=(x + cell_w // 2, y + 18)))

            # Level name
            if is_boss and unlocked:
                name_color = (255, 180, 80)
            elif unlocked:
                name_color = (200, 175, 150)
            else:
                name_color = (60, 50, 40)
            name_text = small_font.render(level_names[i], True, name_color)
            screen.blit(name_text, name_text.get_rect(center=(x + cell_w // 2, y + 40)))

            # Score if cleared
            if i < len(self._scores):
                sc_text = small_font.render(str(self._scores[i]), True, (160, 200, 140))
                screen.blit(sc_text, sc_text.get_rect(center=(x + cell_w // 2, y + 57)))

        # Footer hint
        hint_font = get_font(18)
        hint = hint_font.render("↑↓←→ 选择  回车 开始  ESC 返回", True, TEXT_MUTED)
        screen.blit(hint, hint.get_rect(center=(cx, game.SCREEN_HEIGHT - 22)))

    def handle_event(self, event, game):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game.switch_state(GameState.MENU)
            elif event.key == pygame.K_LEFT:
                self.selected = max(0, self.selected - 1)
            elif event.key == pygame.K_RIGHT:
                self.selected = min(9, self.selected + 1)
            elif event.key == pygame.K_UP:
                self.selected = max(0, self.selected - 5)
            elif event.key == pygame.K_DOWN:
                self.selected = min(9, self.selected + 5)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_level(game)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            cell_w, cell_h = 130, 70
            gap_x, gap_y = 20, 15
            grid_w = 5 * (cell_w + gap_x) - gap_x
            start_x = game.SCREEN_WIDTH // 2 - grid_w // 2
            start_y = 75
            mx, my = event.pos

            for i in range(10):
                row = i // 5
                col = i % 5
                x = start_x + col * (cell_w + gap_x)
                y = start_y + row * (cell_h + gap_y)
                if x <= mx <= x + cell_w and y <= my <= y + cell_h:
                    self.selected = i
                    self._start_level(game)

    def _start_level(self, game):
        if self.selected <= self.highest_unlocked:
            game.game_data["current_level"] = self.selected
            game.game_data["rare_bonus"] = self.selected * 5
            game.switch_state(GameState.LEVEL_INTRO)
