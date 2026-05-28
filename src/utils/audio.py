"""Procedural sound effects using pygame — no external audio files needed.

Generates simple waveforms via numpy/pygame.sndarray for:
  - card_select: soft click
  - card_flip: whoosh
  - curse_card: low buzz
  - critical: sharp ping
  - combo: ascending tone
  - level_clear: fanfare chime
  - timeout_warning: rapid tick
  - menu_nav: light blip
"""

import math
import struct
import io
import wave


def _generate_wave_bytes(frequency, duration_ms, sample_rate=22050,
                         wave_type="sine", volume=0.3, fade_ms=10):
    """Generate raw WAV bytes for a simple tone."""
    num_samples = int(sample_rate * duration_ms / 1000.0)
    fade_samples = int(sample_rate * fade_ms / 1000.0)

    data = []
    for i in range(num_samples):
        t = i / sample_rate
        if wave_type == "sine":
            sample = math.sin(2 * math.pi * frequency * t)
        elif wave_type == "square":
            sample = 1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0
        elif wave_type == "triangle":
            sample = 2.0 * abs(2.0 * (t * frequency - math.floor(t * frequency + 0.5))) - 1.0
        elif wave_type == "sawtooth":
            sample = 2.0 * (t * frequency - math.floor(t * frequency + 0.5))
        elif wave_type == "noise":
            import random
            sample = random.uniform(-1.0, 1.0) * 0.3
        else:
            sample = math.sin(2 * math.pi * frequency * t)

        # Apply fade-in / fade-out
        if i < fade_samples:
            sample *= i / fade_samples
        elif i >= num_samples - fade_samples:
            sample *= (num_samples - i) / fade_samples

        sample = int(sample * volume * 32767)
        sample = max(-32768, min(32767, sample))
        data.append(struct.pack("<h", sample))

    return b"".join(data)


def _make_wav_bytes(samples_bytes, sample_rate=22050, nchannels=1, sampwidth=2):
    """Wrap raw samples in WAV format."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(samples_bytes)
    return buf.getvalue()


def _make_sound(freq, duration_ms, wave_type="sine", volume=0.3):
    """Create a pygame Sound from generated waveform."""
    import pygame
    samples = _generate_wave_bytes(freq, duration_ms, wave_type=wave_type, volume=volume)
    wav = _make_wav_bytes(samples)
    return pygame.mixer.Sound(buffer=wav)


def _chord_sound(freqs, duration_ms, wave_type="sine", volume=0.25):
    """Create a chord from multiple frequencies."""
    import pygame
    all_samples = []
    for freq in freqs:
        samples = _generate_wave_bytes(freq, duration_ms, wave_type=wave_type, volume=volume / len(freqs))
        all_samples.append(samples)

    # Mix by averaging (simple approach)
    mixed = bytearray(len(all_samples[0]))
    for i in range(0, len(mixed), 2):
        total = 0
        for s in all_samples:
            val = struct.unpack_from("<h", s, i)[0]
            total += val
        total = max(-32768, min(32767, total))
        struct.pack_into("<h", mixed, i, total)

    wav = _make_wav_bytes(bytes(mixed))
    return pygame.mixer.Sound(buffer=wav)


class GameAudio:
    """Central audio manager for all game sound effects."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        self._init()

    def _init(self):
        try:
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception:
            self.enabled = False
            return

        # Card select: soft thud
        self.sounds["select"] = _make_sound(180, 80, "sine", 0.25)

        # Card flip: whoosh (rising)
        self.sounds["flip"] = _make_sound(300, 120, "sine", 0.2)

        # Curse card: low rumble
        self.sounds["curse"] = _make_sound(60, 200, "square", 0.15)

        # Critical hit: bright ping
        self.sounds["crit"] = _chord_sound([800, 1200], 150, "sine", 0.3)

        # Combo (2/3/4+)
        self.sounds["combo2"] = _make_sound(440, 100, "sine", 0.2)
        self.sounds["combo3"] = _chord_sound([440, 554], 150, "sine", 0.25)
        self.sounds["combo4"] = _chord_sound([440, 554, 660], 200, "sine", 0.3)

        # Level clear: arpeggio
        self.sounds["level_clear"] = _chord_sound([523, 659, 784, 1047], 400, "sine", 0.3)

        # Timeout warning: rapid tick
        self.sounds["tick"] = _make_sound(1000, 30, "square", 0.1)

        # Menu navigation: light blip
        self.sounds["menu"] = _make_sound(600, 40, "sine", 0.15)

        # Button confirm
        self.sounds["confirm"] = _make_sound(800, 60, "sine", 0.2)

    def play(self, name):
        if not self.enabled or name not in self.sounds:
            return
        try:
            self.sounds[name].play()
        except Exception:
            pass

    def play_select(self, card):
        """Play appropriate sound for the selected card."""
        if card.is_curse:
            self.play("curse")
        else:
            self.play("select")

    def play_combo(self, level):
        key = f"combo{min(level, 4)}"
        self.play(key)


# Module-level singleton
_audio = None


def get_audio():
    global _audio
    if _audio is None:
        _audio = GameAudio()
    return _audio
