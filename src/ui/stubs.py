"""State handlers for INTRO, MENU, LEVEL_INTRO, LEVEL_CLEAR, ENDING, etc."""

import json
import math
import random
from pathlib import Path

import pygame
from src.core.game_loop import GameState
from src.ui.story_render import StoryRenderer
from src.utils.font_helper import get_font


# Warm calamity palette
BG_DARK = (12, 8, 6)
TEXT_WARM = (235, 215, 175)
TEXT_GOLD = (255, 225, 100)
TEXT_MUTED = (160, 140, 110)


def _load_story():
    path = Path("data/story.json")
    if not path.exists():
        path = Path(__file__).parent.parent.parent / "data" / "story.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------
# INTRO — typewriter story prologue
# ------------------------------------------------------------------
class IntroState:
    def __init__(self):
        self.story = None
        self.skipped = False

    def enter(self, game):
        data = _load_story()
        lines = data.get("intro", ["天劫将至..."])
        self.story = StoryRenderer(lines, game.SCREEN_WIDTH, game.SCREEN_HEIGHT)
        self.story.start()
        self.skipped = False

    def update(self, game):
        self.story.update(game.dt)
        if self.story.finished and not self.skipped:
            self.skipped = True
        if self.skipped:
            game.switch_state(GameState.LEVEL_INTRO)

    def render(self, screen, game):
        screen.fill(BG_DARK)
        self.story.render(screen)

    def handle_event(self, event, game):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if not self.story.finished:
                self.story.skip()
            elif self.skipped:
                game.switch_state(GameState.LEVEL_INTRO)


# ------------------------------------------------------------------
# LEVEL_INTRO — shows tribulation name + narration before each level
# ------------------------------------------------------------------
class LevelIntroState:
    DISPLAY_TIME = 2.5
    SPECIAL_TIME = 6.0

    def __init__(self):
        self.timer = 0.0
        self.display_time = self.DISPLAY_TIME
        self.lines = []
        self.is_special = False

    def enter(self, game):
        level_index = game.game_data["current_level"]
        data = _load_story()
        self.is_special = False
        self.lines = []

        if level_index == 4:
            self.lines = data.get("level5_master_farewell", [])
            self.is_special = True
            self.display_time = self.SPECIAL_TIME
        elif level_index == 9:
            self.lines = data.get("level10_inner_demon", [])
            self.is_special = True
            self.display_time = self.SPECIAL_TIME
        else:
            level_key = str(level_index + 1)
            level_intros = data.get("level_intros", {})
            narration = level_intros.get(level_key, "")
            self.lines = [narration] if narration else []
            self.display_time = self.DISPLAY_TIME

        self.timer = self.display_time
        self.story = StoryRenderer(
            self.lines, game.SCREEN_WIDTH, game.SCREEN_HEIGHT, font_size=28
        )
        self.story.start()
        self._done = False

    def update(self, game):
        self.story.update(game.dt)
        self.timer -= game.dt
        if self.timer <= 0 or (self.story.finished and self.lines):
            if not self._done:
                self._done = True

    def render(self, screen, game):
        screen.fill(BG_DARK)
        if self.lines:
            self.story.render(screen)

    def handle_event(self, event, game):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._done = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.story and not self.story.finished:
                self.story.skip()
            else:
                self._done = True
        if self._done:
            game.switch_state(GameState.PLAYING)


# ------------------------------------------------------------------
# LEVEL_CLEAR — enhanced score screen with background + particles
# ------------------------------------------------------------------
class LevelClearState:
    RATING_THRESHOLDS = [
        (3000, "S", (255, 220, 80)),
        (2000, "A", (160, 230, 140)),
        (1000, "B", (190, 190, 230)),
        (0, "C", (160, 150, 140)),
    ]

    def __init__(self):
        self.timer = 0.0
        self.display_time = 3.5
        self._particles = []

    def enter(self, game):
        self.timer = self.display_time
        self.cleared_level = game.game_data["current_level"] - 1
        scores = game.game_data["level_scores"]
        self.level_score = scores[-1] if scores else 0
        self._total_score = game.game_data["total_score"]
        self._level_time = game.game_data.get("last_level_time", 99)
        self._talent = self._get_talent()
        self._init_particles(game)
        # Auto-save after each cleared level
        game.save_game()

    # Per-level talent titles: [≤10s, ≤15s, ≤20s, ≤30s, >30s]
    TALENTS = [
        ["御风登仙",   "风驰苍穹", "踏风而行", "迎风而立", "逆风挣扎"],   # 风劫
        ["涅槃真火",   "烈焰焚天", "浴火不灭", "星火燎原", "焦头烂额"],   # 火劫
        ["万雷归一",   "雷霆贯体", "雷音淬骨", "闻雷不惊", "雷击踉跄"],   # 雷劫
        ["冰心玉魄",   "寒霜不侵", "踏冰无痕", "破冰前行", "冻僵发抖"],   # 冰劫
        ["五行归宗",   "四象通玄", "三才贯通", "两仪初悟", "五行相冲"],   # 五行劫
        ["阴阳合道",   "两极归心", "黑白分明", "初窥阴阳", "阴阳颠倒"],   # 阴阳劫
        ["超脱时空",   "一念千年", "光阴逆旅", "时空迷途", "迷失虚空"],   # 时空劫
        ["寂灭涅槃",   "万法归寂", "心如止水", "枯荣参半", "生机渐熄"],   # 寂灭劫
        ["超越轮回",   "三世贯通", "轮回觉醒", "因果初悟", "轮回困顿"],   # 轮回劫
        ["斩断心魔",   "降伏其心", "心魔退散", "心魔缠身", "道心破碎"],   # 心魔劫
    ]
    TALENT_COLORS = [
        (255, 220, 40),   # ≤10s: 金色
        (220, 200, 120),  # ≤15s: 暗金
        (180, 210, 220),  # ≤20s: 青蓝
        (160, 200, 140),  # ≤30s: 翠绿
        (200, 140, 100),  # >30s: 暗红 (搞笑吐槽档)
    ]

    def _get_talent(self):
        lv = max(0, min(self.cleared_level, 9))
        t = self._level_time
        if t <= 22:    i = 0
        elif t <= 35:  i = 1
        elif t <= 55:  i = 2
        else:          i = 4  # >55s 全部吐槽档
        return self.TALENTS[lv][i], self.TALENT_COLORS[i]

    def _get_rating(self):
        for threshold, grade, color in self.RATING_THRESHOLDS:
            if self.level_score >= threshold:
                return grade, color
        return "C", (160, 150, 140)

    def _init_particles(self, game):
        self._particles = []
        w, h = game.SCREEN_WIDTH, game.SCREEN_HEIGHT
        for _ in range(50):
            self._particles.append([
                random.randint(0, w),
                random.randint(0, h),
                random.uniform(-40, 40),
                random.uniform(-80, -20),
                random.uniform(0.6, 2.0),
                random.randint(3, 7),
                random.choice([
                    (255, 220, 80), (255, 200, 120), (220, 180, 100),
                    (200, 160, 60), (240, 210, 150),
                ]),
            ])

    def update(self, game):
        dt = game.dt
        self.timer -= dt
        # Animate particles
        w, h = game.SCREEN_WIDTH, game.SCREEN_HEIGHT
        for p in self._particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 50 * dt
            p[4] -= dt
            if p[4] <= 0 or p[1] > h or p[0] < -20 or p[0] > w + 20:
                p[0] = random.randint(0, w)
                p[1] = random.randint(-30, h // 3)
                p[2] = random.uniform(-45, 45)
                p[3] = random.uniform(-90, -25)
                p[4] = random.uniform(0.8, 2.0)

        if self.timer <= 0:
            if self.cleared_level >= 9:
                game.switch_state(GameState.ENDING)
            else:
                game.switch_state(GameState.LEVEL_INTRO)

    def render(self, screen, game):
        cx = game.SCREEN_WIDTH // 2
        cy = game.SCREEN_HEIGHT // 2

        # Battle background underneath
        bg = game.draw_bg("battle_bg")
        if bg:
            screen.blit(bg, (0, 0))

        # Dark overlay
        dim = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
        dim.set_alpha(200)
        dim.fill((4, 3, 2))
        screen.blit(dim, (0, 0))

        # Decorative panel
        panel_w, panel_h = 380, 290
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((25, 18, 10, 175))
        pygame.draw.rect(panel, (180, 140, 60, 200), panel.get_rect(),
                         width=2, border_radius=16)
        # Inner subtle border
        inner = panel.get_rect().inflate(-12, -12)
        pygame.draw.rect(panel, (180, 140, 60, 60), inner, width=1, border_radius=10)
        screen.blit(panel, (cx - panel_w // 2, cy - panel_h // 2 - 5))

        # Level name
        level_names = [
            "第一重·风劫", "第二重·火劫", "第三重·雷劫", "第四重·冰劫",
            "第五重·五行劫", "第六重·阴阳劫", "第七重·时空劫",
            "第八重·寂灭劫", "第九重·轮回劫", "心魔劫"
        ]
        level_name = level_names[self.cleared_level] if self.cleared_level < len(level_names) else "天劫"
        font_large = get_font(36)
        title = font_large.render(f"{level_name}  —  渡劫成功!", True, TEXT_GOLD)
        screen.blit(title, title.get_rect(center=(cx, cy - 95)))

        # Decorative divider line
        div_y = cy - 65
        pygame.draw.line(screen, (100, 70, 40), (cx - 120, div_y), (cx + 120, div_y), 1)

        # Score
        font_score = get_font(28)
        score_text = font_score.render(f"本关得分  {self.level_score}", True, TEXT_WARM)
        screen.blit(score_text, score_text.get_rect(center=(cx, cy - 38)))

        # Total score
        font_total = get_font(18)
        total_text = font_total.render(f"累计总分  {self._total_score}", True, TEXT_MUTED)
        screen.blit(total_text, total_text.get_rect(center=(cx, cy - 10)))

        # Talent title (天赋评级)
        talent_text, talent_color = self._talent
        font_talent = get_font(22)
        t_label = font_talent.render(f"用时 {self._level_time}秒  ·  {talent_text}", True, talent_color)
        screen.blit(t_label, t_label.get_rect(center=(cx, cy + 16)))

        # Rating glow behind
        grade, color = self._get_rating()
        glow = pygame.Surface((140, 140), pygame.SRCALPHA)
        for r in range(55, 8, -10):
            a = max(0, 35 - r // 3)
            pygame.draw.circle(glow, (*color, a), (70, 70), r)
        screen.blit(glow, glow.get_rect(center=(cx, cy + 55)))

        # Rating letter — pulsing
        pulse = 1.0 + 0.06 * math.sin(self.timer * 4.5)
        font_grade = get_font(int(68 * pulse))
        grade_text = font_grade.render(grade, True, color)
        screen.blit(grade_text, grade_text.get_rect(center=(cx, cy + 55)))

        # Bottom countdown bar
        bar_w, bar_h = 300, 4
        bar_y = cy + 110
        progress = max(0, self.timer / self.display_time)
        pygame.draw.rect(screen, (35, 25, 15),
                         (cx - bar_w // 2, bar_y, bar_w, bar_h), border_radius=2)
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            fc = (200, 160, 60) if progress > 0.3 else (180, 120, 40)
            pygame.draw.rect(screen, fc,
                             (cx - bar_w // 2, bar_y, fill_w, bar_h), border_radius=2)

        # Hint
        font_hint = get_font(15)
        hint = "下一关即将开始..." if self.cleared_level < 9 else "最终考验将至..."
        hint_text = font_hint.render(hint, True, TEXT_MUTED)
        screen.blit(hint_text, hint_text.get_rect(center=(cx, bar_y + 16)))

        # Celebration gold particles
        for p in self._particles:
            x, y, _, _, life, size, pc = p
            alpha = int(180 * max(0, min(1, life / 1.5)))
            s = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*pc, alpha), (size + 1, size + 1), size)
            screen.blit(s, (x - size, y - size))


# ------------------------------------------------------------------
# CHAPTER_BREAK — every 5 levels
# ------------------------------------------------------------------
class ChapterBreakState:
    def enter(self, game):
        game.game_data["chapter_scores"].append(game.game_data["total_score"])
        game.switch_state(GameState.LEVEL_CLEAR)


# ------------------------------------------------------------------
# GAME_OVER — placeholder
# ------------------------------------------------------------------
class GameOverState:
    """Dramatic failure screen — 道心破碎."""

    def __init__(self):
        self.timer = 0.0
        self._particles = []
        self.selected = 0
        self.options = ["重试本关", "返回菜单"]

    def enter(self, game):
        self.timer = 0.0
        self.selected = 0
        self._failed_level = game.game_data.get("failed_level", 0)
        self._failed_score = game.game_data.get("failed_score", 0)
        self._init_particles(game)

    def _init_particles(self, game):
        self._particles = []
        w, h = game.SCREEN_WIDTH, game.SCREEN_HEIGHT
        for _ in range(60):
            self._particles.append([
                random.randint(0, w),
                random.randint(-h, 0),
                random.uniform(-15, 15),   # drift
                random.uniform(30, 70),     # fall speed
                random.uniform(1, 4),       # size
                random.uniform(0, 3),       # phase delay
                random.choice([(120, 90, 60), (80, 60, 40), (60, 45, 30), (140, 100, 70)]),
            ])

    def update(self, game):
        dt = game.dt
        self.timer += dt
        w, h = game.SCREEN_WIDTH, game.SCREEN_HEIGHT
        for p in self._particles:
            p[1] += p[3] * dt
            p[0] += p[2] * dt + math.sin(self.timer * 2 + p[5]) * 0.3
            if p[1] > h + 20:
                p[0] = random.randint(0, w)
                p[1] = random.randint(-30, -5)
                p[4] = random.uniform(1, 4)

    def render(self, screen, game):
        cx = game.SCREEN_WIDTH // 2
        cy = game.SCREEN_HEIGHT // 2

        # Battle bg with heavy overlay
        bg = game.draw_bg("ending_bg") or game.draw_bg("battle_bg")
        if bg:
            screen.blit(bg, (0, 0))
        # Very dark overlay — oppressive atmosphere
        dim = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
        dim.set_alpha(200)
        dim.fill((2, 1, 1))
        screen.blit(dim, (0, 0))

        # Red vignette pulse
        vignette_alpha = 30 + int(15 * math.sin(self.timer * 1.5))
        vig = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT), pygame.SRCALPHA)
        vignette_color = (60, 5, 5, vignette_alpha)
        for r in range(max(game.SCREEN_WIDTH, game.SCREEN_HEIGHT) // 2, 100, -40):
            a = max(0, vignette_alpha - r // 8)
            pygame.draw.circle(vig, (40, 3, 3, a), (cx, cy), r)
        screen.blit(vig, (0, 0))

        # Falling dark ash particles
        for p in self._particles:
            x, y, _, _, size, _, color = p
            alpha = int(150 * (0.5 + 0.5 * math.sin(self.timer * 3 + p[5])))
            s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, min(200, alpha)), (int(size), int(size)), size)
            screen.blit(s, (x - size, y - size))

        # ---- Title: 道心破碎 ----
        # Pulsing red glow behind text
        glow_alpha = 20 + int(10 * math.sin(self.timer * 2))
        glow_s = pygame.Surface((300, 100), pygame.SRCALPHA)
        for r in range(80, 20, -15):
            a = max(0, 60 - r // 2)
            pygame.draw.circle(glow_s, (180, 30, 20, a), (150, 50), r)
        screen.blit(glow_s, glow_s.get_rect(center=(cx, cy - 80)))

        # Main title — large, dramatic
        font_big = get_font(56)
        title = font_big.render("道心破碎", True, (220, 80, 60))
        screen.blit(title, title.get_rect(center=(cx, cy - 80)))

        # Subtitle
        font_sub = get_font(22)
        sub = font_sub.render("渡 劫 失 败", True, (180, 140, 110))
        screen.blit(sub, sub.get_rect(center=(cx, cy - 35)))

        # Divider
        div_y = cy
        pygame.draw.line(screen, (120, 60, 40), (cx - 130, div_y), (cx + 130, div_y), 1)

        # Failed level info
        level_names = [
            "第一重·风劫", "第二重·火劫", "第三重·雷劫", "第四重·冰劫",
            "第五重·五行劫", "第六重·阴阳劫", "第七重·时空劫",
            "第八重·寂灭劫", "第九重·轮回劫", "心魔劫"
        ]
        lname = level_names[self._failed_level] if self._failed_level < len(level_names) else "天劫"
        font_info = get_font(20)
        info = font_info.render(f"止步于 {lname}", True, TEXT_MUTED)
        screen.blit(info, info.get_rect(center=(cx, cy + 25)))

        # Score
        score_t = font_info.render(f"本关得分: {self._failed_score}", True, (200, 160, 120))
        screen.blit(score_t, score_t.get_rect(center=(cx, cy + 52)))

        # ---- Options ----
        option_font = get_font(24)
        for i, text in enumerate(self.options):
            oy = cy + 98 + i * 40
            is_sel = (i == self.selected)
            color = (255, 220, 180) if is_sel else TEXT_MUTED

            opt = option_font.render(text, True, color)
            screen.blit(opt, opt.get_rect(center=(cx, oy)))

            if is_sel:
                indicator = option_font.render(">", True, (255, 220, 60))
                screen.blit(indicator, (cx - 80, oy - indicator.get_height() // 2))
                indicator2 = option_font.render("<", True, (255, 220, 60))
                screen.blit(indicator2, (cx + 60, oy - indicator2.get_height() // 2))

        # Bottom hint
        font_hint = get_font(14)
        hint = font_hint.render("道心不灭，终可重来", True, (100, 80, 60))
        screen.blit(hint, hint.get_rect(center=(cx, game.SCREEN_HEIGHT - 28)))

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
                oy = cy + 98 + i * 40
                if abs(mx - cx) < 120 and abs(my - oy) < 16:
                    self.selected = i
                    self._select(game)

    def _select(self, game):
        if self.selected == 0:
            # Retry: go back to same level
            game.switch_state(GameState.LEVEL_INTRO)
        else:
            # Return to menu
            game.switch_state(GameState.MENU)


# ------------------------------------------------------------------
# ENDING — final story + score + immortal title
# ------------------------------------------------------------------
class EndingState:
    TITLE_THRESHOLDS = [
        (25000, "大罗金仙", (255, 220, 80)),
        (18000, "太乙真仙", (210, 190, 255)),
        (12000, "天仙", (190, 230, 255)),
        (0, "散仙", (190, 180, 170)),
    ]

    STORY_PHASE = 0
    SCORE_PHASE = 1

    def __init__(self):
        self.timer = 0.0
        self.phase = self.STORY_PHASE

    def _get_title(self, total_score):
        for threshold, title, color in self.TITLE_THRESHOLDS:
            if total_score >= threshold:
                return title, color
        return "散仙", (190, 180, 170)

    def enter(self, game):
        data = _load_story()
        lines = data.get("ending", ["渡劫成功。"])
        self.story = StoryRenderer(lines, game.SCREEN_WIDTH, game.SCREEN_HEIGHT)
        self.story.start()
        self.phase = self.STORY_PHASE
        self.total = game.game_data["total_score"]
        self.title, self.title_color = self._get_title(self.total)
        self.score_timer = 15.0

    def update(self, game):
        if self.phase == self.STORY_PHASE:
            self.story.update(game.dt)
            if self.story.finished:
                self.phase = self.SCORE_PHASE
        else:
            self.score_timer -= game.dt
            if self.score_timer <= 0:
                game.quit()

    def render(self, screen, game):
        # Ending background image
        bg = game.draw_bg("ending_bg")
        if bg:
            screen.blit(bg, (0, 0))
            # Dark overlay for text readability
            overlay = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
            overlay.set_alpha(140)
            overlay.fill((4, 3, 2))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill((10, 7, 5))

        cx = game.SCREEN_WIDTH // 2
        cy = game.SCREEN_HEIGHT // 2

        if self.phase == self.STORY_PHASE:
            self.story.render(screen)
        else:
            self._render_score_phase(screen, cx, cy, game)

    def _render_score_phase(self, screen, cx, cy, game):
        for i in range(60):
            angle = i * (math.pi * 2 / 60) + (self.score_timer * 0.3)
            radius = 120 + math.sin(self.score_timer * 3 + i) * 30
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius * 0.6
            alpha = max(0, min(255, int(100 + math.sin(self.score_timer * 2 + i) * 80)))
            s = pygame.Surface((5, 5), pygame.SRCALPHA)
            s.fill((255, 220, 80, alpha))
            screen.blit(s, (px, py))

        font_big = get_font(56)
        t1 = font_big.render("渡劫成功 · 羽化登仙", True, TEXT_GOLD)
        screen.blit(t1, t1.get_rect(center=(cx, cy - 90)))

        font_title = get_font(48)
        t2 = font_title.render(self.title, True, self.title_color)
        screen.blit(t2, t2.get_rect(center=(cx, cy - 30)))

        font_score = get_font(36)
        t3 = font_score.render(f"总分: {self.total}", True, TEXT_WARM)
        screen.blit(t3, t3.get_rect(center=(cx, cy + 25)))

        font_small = get_font(16)
        scores = game.game_data["level_scores"]
        if scores:
            summary = "  |  ".join(f"第{i + 1}关:{s}" for i, s in enumerate(scores))
            t4 = font_small.render(summary, True, TEXT_MUTED)
            screen.blit(t4, t4.get_rect(center=(cx, cy + 70)))

        font_hint = get_font(20)
        t5 = font_hint.render("按 ESC 退出游戏", True, TEXT_MUTED)
        screen.blit(t5, t5.get_rect(center=(cx, game.SCREEN_HEIGHT - 35)))

    def handle_event(self, event, game):
        if self.phase == self.STORY_PHASE:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if not self.story.finished:
                    self.story.skip()
                else:
                    self.phase = self.SCORE_PHASE
