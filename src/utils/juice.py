"""Juice effects: flying numbers, screen shake, particles.

Low-cost, high-impact visual feedback for card selection, stat changes,
combos, and level transitions.
"""

import math
import random
import pygame
from src.utils.font_helper import get_font


# ------------------------------------------------------------------
# Flying number — +N / -N that rises and fades
# ------------------------------------------------------------------
class FlyingText:
    __slots__ = ("x", "y", "text", "color", "life", "max_life",
                 "vel_y", "size_mult")

    def __init__(self, x, y, text, color, size_mult=1.0, life=0.8):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = life
        self.max_life = life
        self.vel_y = -60   # pixels per second upward
        self.size_mult = size_mult

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.life -= dt
        self.y += self.vel_y * dt
        # Slow down near end
        self.vel_y *= 0.98

    def render(self, screen, font):
        alpha = int(255 * (self.life / self.max_life))
        base_size = int(22 * self.size_mult)
        draw_font = get_font( base_size)
        surf = draw_font.render(self.text, True, self.color)
        surf.set_alpha(max(0, min(255, alpha)))
        rect = surf.get_rect(center=(self.x, self.y))
        screen.blit(surf, rect)


# ------------------------------------------------------------------
# Screen shake — brief horizontal oscillation
# ------------------------------------------------------------------
class ScreenShake:
    __slots__ = ("intensity", "duration", "elapsed", "offset_x", "offset_y")

    def __init__(self, intensity=5, duration=0.2):
        self.intensity = intensity
        self.duration = duration
        self.elapsed = 0.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    @property
    def active(self):
        return self.elapsed < self.duration

    def update(self, dt):
        if not self.active:
            self.offset_x = 0
            self.offset_y = 0
            return
        self.elapsed += dt
        decay = 1.0 - (self.elapsed / self.duration)
        self.offset_x = random.uniform(-1, 1) * self.intensity * decay
        self.offset_y = random.uniform(-1, 1) * self.intensity * decay * 0.5

    def apply(self, screen):
        """Returns a (dx, dy) for the caller to apply as a screen offset."""
        return self.offset_x, self.offset_y


# ------------------------------------------------------------------
# Particle — simple spark for celebrations
# ------------------------------------------------------------------
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color, speed=80):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(speed * 0.5, speed)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd - random.uniform(20, 60)
        self.life = random.uniform(0.4, 1.0)
        self.max_life = self.life
        self.color = color
        self.size = random.randint(2, 5)

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 120 * dt  # gravity

    def render(self, screen):
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(self.size * (self.life / self.max_life)))
        c = (*self.color, alpha)
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, c, (size, size), size)
        screen.blit(surf, (self.x - size, self.y - size))


# ------------------------------------------------------------------
# Juice manager — collects and orchestrates all effects
# ------------------------------------------------------------------
class JuiceManager:
    """Manages active visual effects, updated and rendered each frame."""

    def __init__(self):
        self.flying_texts = []
        self.shake = ScreenShake(0, 0)
        self.particles = []

    def clear(self):
        self.flying_texts.clear()
        self.particles.clear()
        self.shake = ScreenShake(0, 0)

    def add_fly_text(self, x, y, text, color, size_mult=1.0, life=0.8):
        self.flying_texts.append(FlyingText(x, y, text, color, size_mult, life))

    def trigger_shake(self, intensity=5, duration=0.2):
        self.shake = ScreenShake(intensity, duration)

    def spawn_particles(self, x, y, color, count=15, speed=80):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed))

    def update(self, dt):
        self.shake.update(dt)

        for ft in self.flying_texts[:]:
            ft.update(dt)
            if not ft.alive:
                self.flying_texts.remove(ft)

        for p in self.particles[:]:
            p.update(dt)
            if not p.alive:
                self.particles.remove(p)

    def render(self, screen, font=None):
        if font is None:
            font = get_font( 22)

        for ft in self.flying_texts:
            ft.render(screen, font)

        for p in self.particles:
            p.render(screen)

    def get_shake_offset(self):
        return self.shake.apply(None)
