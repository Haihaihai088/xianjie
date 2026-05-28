"""PLAYING state — the core gameplay loop."""

import json
import random
from pathlib import Path

import pygame

from src.entities.card import CardStyle, CardRarity
from src.systems.card_generator import CardGenerator
from src.core.game_loop import GameState
from src.utils.juice import JuiceManager
from src.utils.audio import get_audio
from src.utils.font_helper import get_font


class PlayingState:
    """Handles the PLAYING game state: card selection, stat tracking,
    timer, and target checking."""

    STEP_TIME = 8.0  # default seconds per step (overridden by level config)

    def __init__(self):
        self.card_gen = CardGenerator()
        self.juice = JuiceManager()
        self._levels = self._load_levels()
        self.reset()

    def _load_levels(self):
        path = Path("data/levels.json")
        if not path.exists():
            path = Path(__file__).parent.parent.parent / "data" / "levels.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["levels"]

    def reset(self):
        self.cards = []                   # current two cards
        self.stats = {"atk": 0, "def": 0, "spd": 0}
        self.targets = {"atk": 20, "def": 20, "spd": 20}  # default
        self.timer = self.STEP_TIME
        self.level_index = 0
        self.rare_bonus = 0              # cumulative +5 per cleared level
        self.is_boss = False
        self.combo_count = 0
        self.last_style = None
        self.selected_card = None        # card just chosen (for anim)
        self.anim_timer = 0.0            # animation cooldown
        self._picked_idx = -1            # which card was picked (for render anim)
        self.steps_taken = 0
        self.level_complete = False
        self.level_name = "未知天劫"
        self.MAX_STEPS = 6
        self.paused = False
        self._pause_selected = 0
        self._pause_opts = ["继续渡劫", "重开本关", "返回菜单"]
        self.total_time = 0.0

        # Scoring
        self.level_score = 0
        self.time_bonus = 0
        self.combo_bonus = 0
        self.overflow_bonus = 0
        self.crit_count = 0
        self.fast_picks = 0
        self.streak_mult = 1.0

    # ------------------------------------------------------------------
    # State lifecycle
    # ------------------------------------------------------------------
    def enter(self, game):
        self.juice.clear()
        self._init_ashes(game)
        level_cfg = self._get_level_config(game.game_data["current_level"])
        self._apply_level_config(level_cfg, game)
        self._draw_new_cards()
        self.level_complete = False

    def exit(self, game):
        self.cards = []
        self.selected_card = None

    def update(self, game):
        dt = game.dt

        if self.paused:
            return

        if not self.level_complete:
            self.timer -= dt
            self.total_time += dt

        # Animation cooldown (always run; needed for level-complete transition)
        if self.anim_timer > 0:
            self.anim_timer -= dt
            if self.anim_timer <= 0:
                if self.level_complete:
                    # Animation finished, advance to next state
                    self._calc_final_score()
                    self._advance_level(game)
                else:
                    self.selected_card = None
                    self._picked_idx = -1
                    self._draw_new_cards()

        # Tick warning when timer is low
        if not self.level_complete and self.anim_timer <= 0 and 0 < self.timer <= 3:
            import time
            # Tick every second
            prev_tick = getattr(self, "_last_tick", 0)
            if int(self.timer) != prev_tick:
                get_audio().play("tick")
                self._last_tick = int(self.timer)

        # Timeout: auto-pick random card (only when playing)
        if not self.level_complete and self.timer <= 0 and self.anim_timer <= 0:
            self._auto_pick(game)

    def render(self, screen, game):
        """Render game view with juice effects."""
        # Battle background image (aspect ratio preserved)
        bg = game.draw_bg("battle_bg")
        if bg:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((14, 10, 7))

        # Update & render ash particles
        self._update_ashes(game)
        self._render_ashes(screen)

        # Update juice
        self.juice.update(game.dt)

        # Render base UI
        self._render_cards(screen, game)
        self._render_stats(screen, game)

        # Render juice on top
        self.juice.render(screen)

        # Pause overlay (must be last)
        if self.paused:
            self._render_pause_overlay(screen, game)


    def handle_event(self, event, game):
        # Pause menu handling
        if self.paused:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = False
                elif event.key == pygame.K_UP:
                    self._pause_selected = (self._pause_selected - 1) % len(self._pause_opts)
                elif event.key == pygame.K_DOWN:
                    self._pause_selected = (self._pause_selected + 1) % len(self._pause_opts)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._pause_select(game)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                cx = game.SCREEN_WIDTH // 2
                cy = game.SCREEN_HEIGHT // 2
                mx, my = event.pos
                for i in range(len(self._pause_opts)):
                    oy = cy - 20 + i * 45
                    if abs(mx - cx) < 120 and abs(my - oy) < 18:
                        self._pause_selected = i
                        self._pause_select(game)
            return

        if self.level_complete:
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = True
            self._pause_selected = 0
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.anim_timer > 0:
                return
            x, y = event.pos
            self._handle_click(x, y, game)

    # ------------------------------------------------------------------
    # Card selection
    # ------------------------------------------------------------------
    def _handle_click(self, mx, my, game):
        card_rects = self._card_rects(game)
        for i, rect in enumerate(card_rects):
            if rect.collidepoint(mx, my) and i < len(self.cards):
                self._pick_card(i, game)
                break

    def _auto_pick(self, game):
        if len(self.cards) >= 2:
            idx = random.randint(0, 1)
        elif len(self.cards) == 1:
            idx = 0
        else:
            return
        self._pick_card(idx, game)

    def _pick_card(self, idx, game):
        if idx >= len(self.cards):
            return
        card = self.cards[idx]
        self.selected_card = card
        self._picked_idx = idx
        self.anim_timer = 0.8  # cooldown until next draw
        self.steps_taken += 1

        # Burst particles from picked card
        rects = self._card_rects(game)
        self.juice.spawn_particles(
            rects[idx].centerx, rects[idx].centery,
            (255, 200, 60), 12, 60
        )

        # Check for critical hit
        is_crit = self._check_crit(card)

        # Apply modifiers (critical multiplies)
        mult = 1.5 if is_crit else 1.0
        atk_gain = int(card.atk_mod * mult)
        def_gain = int(card.def_mod * mult)
        spd_gain = int(card.spd_mod * mult)

        self.stats["atk"] += atk_gain
        self.stats["def"] += def_gain
        self.stats["spd"] += spd_gain

        # Combo tracking (MUST be before juice that references combo_count)
        self._update_combo(card)

        # Card position for juice effects
        rects = self._card_rects(game)
        card_x = rects[idx].centerx
        card_y = rects[idx].centery

        # Flying texts for each stat change
        stat_colors = {
            "atk": (255, 100, 100), "def": (255, 200, 60), "spd": (100, 220, 100)
        }
        labels = {"atk": "灵力", "def": "根骨", "spd": "身法"}
        gains = {"atk": atk_gain, "def": def_gain, "spd": spd_gain}
        for j, key in enumerate(("atk", "def", "spd")):
            val = gains[key]
            if val == 0:
                continue
            color = (255, 220, 80) if is_crit else stat_colors[key]
            size_m = 1.5 if is_crit else 1.0
            text = f"{labels[key]} {val:+d}"
            self.juice.add_fly_text(
                card_x + random.randint(-30, 30),
                card_y + j * 25 - 40,
                text, color, size_m
            )

        # Audio
        audio = get_audio()
        audio.play_select(card)
        if is_crit:
            audio.play("crit")

        # Critical hit: screen shake + extra text
        if is_crit:
            self.juice.trigger_shake(8, 0.25)
            self.juice.add_fly_text(card_x, card_y - 70, "暴击!", (255, 220, 40), 2.0, 1.2)

        # Combo visual + audio
        if self.combo_count >= 2:
            audio.play_combo(self.combo_count)
        if self.combo_count >= 3:
            combo_names = {3: "万法归宗!", 4: "天人合一!"}
            cname = combo_names.get(self.combo_count, "天人合一!")
            self.juice.add_fly_text(card_x, card_y - 100, cname, (200, 180, 255), 1.8, 1.5)

        # Fast pick tracking (streak clear)
        if self.timer > self.STEP_TIME * 0.7:
            self.fast_picks += 1

        # Score accumulation
        self.time_bonus += max(0, int(self.timer) * 50)
        if is_crit:
            self.crit_count += 1
            self.level_score += 150

        # Check targets immediately after stat change
        self._check_targets(game)

        # Replenish timer (only if not yet complete)
        if not self.level_complete:
            self.timer = self.STEP_TIME

    # ------------------------------------------------------------------
    # Target checking
    # ------------------------------------------------------------------
    def _check_targets(self, game):
        met = all(
            self.stats[k] >= self.targets[k]
            for k in ("atk", "def", "spd")
        )
        if met:
            self.level_complete = True
            self.timer = 999  # freeze timer
            get_audio().play("level_clear")
            # Level clear juice
            self.juice.trigger_shake(12, 0.4)
            cx, cy = game.SCREEN_WIDTH // 2, game.SCREEN_HEIGHT // 2
            self.juice.add_fly_text(cx, cy - 40, "渡劫成功!", (255, 220, 40), 2.5, 2.0)
            self.juice.spawn_particles(cx, cy + 40, (255, 220, 80), 30, 120)
            # Rare bonus notification
            new_rare = game.game_data["rare_bonus"] + 5
            self.juice.add_fly_text(
                cx, cy + 80,
                f"天劫淬体！稀有机缘感知 +5%  → {new_rare}%",
                (180, 200, 255), 1.2, 2.5
            )

    def _trigger_game_over(self, game):
        """Triggered when steps exhausted without meeting targets."""
        self.level_complete = True
        self.timer = 999
        get_audio().play("curse")
        game.game_data["failed_level"] = game.game_data["current_level"]
        game.game_data["failed_score"] = self.level_score
        self.anim_timer = 0.0
        self._picked_idx = -1
        game.switch_state(GameState.GAME_OVER)

    def _advance_level(self, game):
        """Called after level_complete animation finishes."""
        level = game.game_data["current_level"]
        game.game_data["last_level_time"] = int(self.total_time)
        self._update_game_data(game)

        if level == 4:
            game.game_data["chapter_scores"].append(
                game.game_data["total_score"]
            )

        if level < 9:
            game.game_data["current_level"] += 1
        game.switch_state(GameState.LEVEL_CLEAR)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def _calc_final_score(self):
        # Combo bonus
        self.combo_bonus = self.combo_count * 200

        # Overflow bonus
        for key in ("atk", "def", "spd"):
            overflow = self.stats[key] - self.targets[key]
            if overflow > self.targets[key] * 0.3:
                self.overflow_bonus += overflow * 10

        # Streak multiplier
        if self.fast_picks >= 5:
            self.streak_mult = 1.5
        elif self.fast_picks >= 3:
            self.streak_mult = 1.2

        self.level_score += (
            1000 +
            self.time_bonus +
            self.combo_bonus +
            self.overflow_bonus
        )
        self.level_score = int(self.level_score * self.streak_mult)

    def _update_game_data(self, game):
        game.game_data["level_scores"].append(self.level_score)
        game.game_data["total_score"] += self.level_score
        game.game_data["rare_bonus"] += 5
        game.game_data["highest_combo"] = max(
            game.game_data["highest_combo"], self.combo_count
        )
        self.rare_bonus = game.game_data["rare_bonus"]

    # ------------------------------------------------------------------
    # Combo
    # ------------------------------------------------------------------
    def _update_combo(self, card):
        if card.is_curse:
            self.combo_count = 0
            self.last_style = None
            return
        if self.last_style is None or card.style != self.last_style:
            self.combo_count = 1
        else:
            self.combo_count += 1
        self.last_style = card.style

        # Apply combo bonus
        bonus = 0
        if self.combo_count >= 4:
            bonus = 6
        elif self.combo_count >= 3:
            bonus = 4
        elif self.combo_count >= 2:
            bonus = 2

        if bonus:
            self.stats["atk"] += bonus
            self.stats["def"] += bonus
            self.stats["spd"] += bonus

    # ------------------------------------------------------------------
    # Critical hit
    # ------------------------------------------------------------------
    def _check_crit(self, card):
        from src.entities.card import CardRarity
        if card.rarity == CardRarity.EPIC:
            return random.random() < 0.15
        elif card.rarity == CardRarity.RARE:
            return random.random() < 0.05
        return False

    # ------------------------------------------------------------------
    # Card drawing
    # ------------------------------------------------------------------
    def _draw_new_cards(self):
        # Boss levels: chance for god card or curse card
        if self.is_boss:
            god_chance = self._level_cfg.get("god_card_chance", 0)
            curse_chance = self._level_cfg.get("curse_card_chance", 0)

            if god_chance and random.random() < god_chance / 100.0:
                card1 = self.card_gen.generate_god_card()
            else:
                card1 = self.card_gen.generate(
                    self.rare_bonus, self.is_boss
                )

            if curse_chance and random.random() < curse_chance / 100.0:
                card2 = self.card_gen.generate_curse_card()
            else:
                card2 = self.card_gen.generate(
                    self.rare_bonus, self.is_boss
                )
            self.cards = [card1, card2]
        else:
            self.cards = list(self.card_gen.generate_pair(
                rare_bonus=self.rare_bonus,
                is_boss=self.is_boss
            ))

    # ------------------------------------------------------------------
    # Level config
    # ------------------------------------------------------------------
    def _get_level_config(self, level_index):
        """Load level config from JSON data."""
        if 0 <= level_index < len(self._levels):
            return self._levels[level_index]
        # Fallback for out-of-range
        return {
            "name": f"第{level_index + 1}关",
            "targets": {"atk": 30, "def": 30, "spd": 30},
            "step_time": 8,
            "is_boss": False,
            "rare_bonus": level_index * 5,
            "narrative": "",
        }

    def _apply_level_config(self, cfg, game):
        self._level_cfg = cfg  # Keep for god/curse card access
        self.stats = {"atk": 0, "def": 0, "spd": 0}
        self.targets = cfg["targets"]
        self.STEP_TIME = cfg["step_time"]
        self.timer = self.STEP_TIME
        self.level_index = game.game_data["current_level"]
        self.rare_bonus = game.game_data["rare_bonus"]
        self.is_boss = cfg.get("is_boss", False)
        self.level_name = cfg["name"]
        self.combo_count = 0
        self.last_style = None
        self.level_score = 0
        self.time_bonus = 0
        self.combo_bonus = 0
        self.overflow_bonus = 0
        self.crit_count = 0
        self.fast_picks = 0
        self.streak_mult = 1.0
        self.steps_taken = 0
        self.total_time = 0.0

    # ------------------------------------------------------------------
    # Simple rendering (will be enhanced in PR4)
    # ------------------------------------------------------------------
    def _pause_select(self, game):
        if self._pause_selected == 0:
            self.paused = False
        elif self._pause_selected == 1:
            self.paused = False
            self.reset()
            self.enter(game)
        elif self._pause_selected == 2:
            self.paused = False
            game.switch_state(GameState.MENU)

    def _render_pause_overlay(self, screen, game):
        cx = game.SCREEN_WIDTH // 2
        cy = game.SCREEN_HEIGHT // 2

        # Dark overlay
        overlay = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((2, 1, 1))
        screen.blit(overlay, (0, 0))

        # Pause title
        font_title = get_font(42)
        t = font_title.render("渡 劫 中", True, (255, 225, 100))
        screen.blit(t, t.get_rect(center=(cx, cy - 100)))

        # Options
        font_opt = get_font(26)
        for i, text in enumerate(self._pause_opts):
            oy = cy - 20 + i * 45
            is_sel = (i == self._pause_selected)
            color = (255, 240, 200) if is_sel else (160, 140, 110)
            opt = font_opt.render(text, True, color)
            screen.blit(opt, opt.get_rect(center=(cx, oy)))
            if is_sel:
                ind = font_opt.render(">", True, (255, 225, 100))
                screen.blit(ind, (cx - 90, oy - ind.get_height() // 2))
                screen.blit(font_opt.render("<", True, (255, 225, 100)),
                            (cx + 70, oy - ind.get_height() // 2))

        # Hint
        font_hint = get_font(14)
        h = font_hint.render("ESC 返回战斗", True, (100, 80, 60))
        screen.blit(h, h.get_rect(center=(cx, cy + 130)))

    def _card_rects(self, game):
        """Calculate the two card bounding boxes."""
        w, h = 180, 240
        spacing = 40
        left_x = game.SCREEN_WIDTH // 2 - w - spacing // 2
        right_x = game.SCREEN_WIDTH // 2 + spacing // 2
        y = game.SCREEN_HEIGHT // 2 - h // 2
        return [
            pygame.Rect(left_x, y, w, h),
            pygame.Rect(right_x, y, w, h),
        ]

    # ------------------------------------------------------------------
    # Ash particles (劫灰粒子)
    # ------------------------------------------------------------------
    def _init_ashes(self, game):
        w, h = game.SCREEN_WIDTH, game.SCREEN_HEIGHT
        self._ashes = []
        for _ in range(40):
            self._ashes.append([
                random.uniform(0, w),      # x
                random.uniform(h * 0.3, h), # y
                random.uniform(1.5, 7),     # size
                random.uniform(20, 50),     # speed
                random.uniform(-20, 20),    # drift
                random.uniform(0, 10),      # life (countdown)
                random.randint(50, 150),    # alpha
            ])
        # Embers
        self._embers = []
        for _ in range(12):
            self._embers.append([
                random.uniform(0, w),
                random.uniform(h * 0.3, h),
                random.uniform(1, 3),
                random.uniform(30, 60),
                random.uniform(-15, 15),
                random.uniform(0, 6),
                random.randint(180, 255),  # r
                random.randint(40, 80),    # g
                random.randint(5, 25),     # b
            ])

    def _update_ashes(self, game):
        w, h = game.SCREEN_WIDTH, game.SCREEN_HEIGHT
        dt = game.dt
        for a in self._ashes:
            a[5] -= dt
            if a[5] <= 0:
                a[0] = random.uniform(0, w)
                a[1] = h + random.uniform(0, 30)
                a[5] = random.uniform(8, 14)
                a[6] = random.randint(50, 150)
            a[1] -= a[3] * dt
            a[0] += a[4] * dt
            if a[1] < -10:
                a[1] = h + random.uniform(0, 30)
                a[0] = random.uniform(0, w)
        for e in self._embers:
            e[5] -= dt
            if e[5] <= 0:
                e[0] = random.uniform(0, w)
                e[1] = h + random.uniform(0, 30)
                e[5] = random.uniform(5, 10)
            e[1] -= e[3] * dt
            e[0] += e[4] * dt
            if e[1] < -10:
                e[1] = h + random.uniform(0, 30)
                e[0] = random.uniform(0, w)

    def _render_ashes(self, screen):
        for a in self._ashes:
            x, y, size, _, _, life, alpha = a
            a_val = int(alpha * (0.3 + 0.7 * max(0, min(1, life / 10))))
            s = pygame.Surface((int(size * 2) + 2, int(size * 2) + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (55, 40, 25, a_val),
                               (int(size) + 1, int(size) + 1), size)
            screen.blit(s, (x - size, y - size))
        for e in self._embers:
            x, y, size, _, _, life, r, g, b = e
            a_val = int(200 * (0.3 + 0.7 * max(0, min(1, life / 8))))
            es = pygame.Surface((int(size * 3), int(size * 3)), pygame.SRCALPHA)
            # glow
            pygame.draw.circle(es, (r, g, b, a_val // 3),
                               (int(size * 1.5), int(size * 1.5)), size * 1.5)
            # core
            pygame.draw.circle(es, (r, g, b, a_val),
                               (int(size * 1.5), int(size * 1.5)), size)
            screen.blit(es, (x - size * 1.5, y - size * 1.5))

    def _render_cards(self, screen, game):
        rects = self._card_rects(game)
        is_animating = self.anim_timer > 0 and self._picked_idx >= 0
        anim_progress = 1.0 - (self.anim_timer / 0.8) if is_animating else 0

        for i, card in enumerate(self.cards):
            rect = rects[i]

            # ---- Animation transforms ----
            scale = 1.0
            alpha = 255
            if is_animating:
                if i == self._picked_idx:
                    # Selected card: scale up + fade out
                    scale = 1.0 + anim_progress * 0.18
                    # ease-out: fade later
                    fade_p = max(0, (anim_progress - 0.25) / 0.75)
                    alpha = int(255 * (1.0 - fade_p))
                else:
                    # Other card: dim
                    alpha = int(255 * max(0.25, 1.0 - anim_progress * 0.7))

            # ---- Draw card with transforms ----
            if scale != 1.0 or alpha < 255:
                # Create a surface for the card
                card_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)

                # Card background
                pygame.draw.rect(card_surf, (* (35, 28, 22), alpha), card_surf.get_rect(), border_radius=10)
                pygame.draw.rect(card_surf, (* card.rarity_color, alpha), card_surf.get_rect(), width=2, border_radius=10)

                # Scale and position
                if scale != 1.0:
                    new_w = int(rect.w * scale)
                    new_h = int(rect.h * scale)
                    card_surf = pygame.transform.smoothscale(card_surf, (new_w, new_h))
                    draw_rect = card_surf.get_rect(center=rect.center)
                else:
                    draw_rect = rect

                # Apply alpha to card surface for dimming
                if alpha < 255:
                    card_surf.set_alpha(alpha)

                screen.blit(card_surf, draw_rect)
            else:
                # Normal draw — no animation
                pygame.draw.rect(screen, (35, 28, 22), rect, border_radius=10)
                pygame.draw.rect(screen, card.rarity_color, rect, width=2, border_radius=10)

            # ---- Card name (draw on screen directly for text clarity) ----
            font = get_font(22)
            name_color = (* (240, 225, 200), alpha) if alpha < 255 else (240, 225, 200)
            name_surf = font.render(card.name, True, name_color[:3] if isinstance(name_color, tuple) else name_color)
            if alpha < 255:
                name_surf.set_alpha(alpha)
            # Position adjusts with scale
            cx = rect.centerx
            cy = rect.top + 30
            if scale != 1.0:
                cy = rect.centery - int(rect.h * scale / 2) + 30
            screen.blit(name_surf, name_surf.get_rect(center=(cx, cy)))

            # ---- Stats (simplified color logic) ----
            small_font = get_font(20)
            stat_lines = [
                (f"灵力 {card.atk_mod:+d}", card.atk_mod),
                (f"根骨 {card.def_mod:+d}", card.def_mod),
                (f"身法 {card.spd_mod:+d}", card.spd_mod),
            ]
            for j, (line, val) in enumerate(stat_lines):
                c2 = (160, 230, 140) if val >= 0 else (230, 130, 110)
                s = small_font.render(line, True, c2)
                if alpha < 255:
                    s.set_alpha(alpha)
                sy = rect.top + 80 + j * 30
                if scale != 1.0:
                    sy = rect.centery - int(rect.h * scale / 2) + 80 + j * 30
                screen.blit(s, s.get_rect(center=(cx, sy)))

            # ---- Rarity label ----
            r_color = (*card.rarity_color, alpha) if alpha < 255 else card.rarity_color
            r_surf = small_font.render(f"[{card.rarity_name}]", True, r_color[:3] if isinstance(r_color, tuple) else r_color)
            if alpha < 255:
                r_surf.set_alpha(alpha)
            rb = rect.bottom - 30
            if scale != 1.0:
                rb = rect.centery + int(rect.h * scale / 2) - 30
            screen.blit(r_surf, r_surf.get_rect(center=(cx, rb)))

    def _render_stats(self, screen, game):
        font = get_font( 24)

        # Level name + timer
        timer_s = max(0, int(self.timer))
        header = f"{self.level_name}   ⏱ {timer_s}秒"
        h_surf = font.render(header, True, (235, 210, 170))
        screen.blit(h_surf, (20, 15))

        # Stat bars
        bar_x = 20
        bar_w = 220
        bar_h = 14
        y_start = 50
        colors = {"atk": (220, 80, 80), "def": (200, 160, 40), "spd": (80, 180, 80)}
        labels = {"atk": "灵力", "def": "根骨", "spd": "身法"}

        for i, key in enumerate(("atk", "def", "spd")):
            y = y_start + i * 30
            val = self.stats[key]
            tgt = self.targets[key]

            # Label
            label = font.render(
                f"{labels[key]}: {val}/{tgt}", True, (220, 200, 170)
            )
            screen.blit(label, (bar_x, y - 2))

            # Background bar
            bar_y = y + 18
            pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h))
            # Filled bar
            fill_w = min(bar_w, int(bar_w * val / max(tgt, 1)))
            # Overflow glow
            if val >= tgt * 1.3:
                color = (255, 200, 40)  # gold
            elif val >= tgt:
                color = colors[key]
            else:
                color = tuple(c // 2 for c in colors[key])
            pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, bar_h))
            # Target marker line
            marker_x = bar_x + int(bar_w * tgt / max(tgt * 1.5, 1))
            marker_x = min(marker_x, bar_x + bar_w)
            pygame.draw.line(screen, (255, 255, 255, 100),
                             (marker_x, bar_y - 2), (marker_x, bar_y + bar_h + 2), 1)

        # Combo display
        if self.combo_count >= 2:
            combo_names = {2: "道心初凝", 3: "万法归宗", 4: "天人合一"}
            combo_text = combo_names.get(self.combo_count, "天人合一")
            if self.combo_count > 4:
                combo_text = f"天人合一 x{self.combo_count}"
            c_surf = font.render(f"道心专一 · {combo_text}", True, (255, 210, 80))
            c_rect = c_surf.get_rect(center=(game.SCREEN_WIDTH // 2, game.SCREEN_HEIGHT - 60))
            screen.blit(c_surf, c_rect)

        # Score
        s_surf = font.render(f"渡劫评分: {self.level_score}", True, (200, 180, 150))
        screen.blit(s_surf, (20, game.SCREEN_HEIGHT - 35))
