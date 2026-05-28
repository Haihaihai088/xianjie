"""Procedural card generation with xianxia theming and rarity escalation."""

import json
import random
from pathlib import Path

from src.entities.card import Card, CardRarity, CardStyle


class CardGenerator:
    """Generates themed cards with tunable rarity distribution.

    The ``rare_bonus`` parameter shifts rarity weights: each +5 means
    5% shifts from Common to Rare (Epic stays at 10%).
    """

    BASE_COMMON = 60
    BASE_RARE = 30
    BASE_EPIC = 10

    STAT_RANGES = {
        CardRarity.COMMON:  (-8, 15),
        CardRarity.RARE:    (-15, 25),
        CardRarity.EPIC:    (-20, 40),
    }

    SUM_RANGES = {
        CardRarity.COMMON:  (5, 15),
        CardRarity.RARE:    (-5, 20),
        CardRarity.EPIC:    (-10, 30),
    }

    def __init__(self, names_path="data/card_names.json"):
        self.names_path = Path(names_path)
        self.names = self._load_names()

    # ------------------------------------------------------------------
    # Name database
    # ------------------------------------------------------------------
    def _load_names(self):
        path = self.names_path
        if not path.exists():
            # fallback to project root relative
            path = Path(__file__).parent.parent.parent / "data" / "card_names.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _pick_adjective(self, style):
        key = {
            CardStyle.ATTACK: "attack",
            CardStyle.DEFENSE: "defense",
            CardStyle.SPEED: "speed",
            CardStyle.BALANCE: "balance",
            CardStyle.CURSE: "curse",
        }[style]
        return random.choice(self.names["style_tags"][key])

    def _pick_noun(self):
        all_nouns = []
        for category, words in self.names["nouns"].items():
            all_nouns.extend(words)
        return random.choice(all_nouns)

    # ------------------------------------------------------------------
    # Rarity distribution
    # ------------------------------------------------------------------
    def _rarity_weights(self, rare_bonus=0, is_boss=False):
        """Return dict[CardRarity, float] of weights.

        rare_bonus: cumulative +5% per cleared level (e.g. 0, 5, 10, ...)
        """
        rare = self.BASE_RARE + rare_bonus
        common = self.BASE_COMMON - rare_bonus
        epic = self.BASE_EPIC

        # Ensure no negative weights
        if common < 0:
            rare += common
            common = 0
        if rare > 100 - epic:
            rare = 100 - epic
            common = 0

        return {
            CardRarity.COMMON: common,
            CardRarity.RARE: rare,
            CardRarity.EPIC: epic,
        }

    def _roll_rarity(self, rare_bonus=0, is_boss=False):
        weights = self._rarity_weights(rare_bonus, is_boss)
        rarities = list(weights.keys())
        probs = list(weights.values())
        return random.choices(rarities, weights=probs, k=1)[0]

    # ------------------------------------------------------------------
    # Stat generation
    # ------------------------------------------------------------------
    def _roll_stats(self, rarity):
        lo, hi = self.STAT_RANGES[rarity]
        sum_lo, sum_hi = self.SUM_RANGES[rarity]

        for _ in range(100):  # rejection sampling
            atk = random.randint(lo, hi)
            df = random.randint(lo, hi)
            spd = random.randint(lo, hi)
            total = atk + df + spd
            if sum_lo <= total <= sum_hi:
                return atk, df, spd

        # fallback: force within range
        return self._force_stats(lo, hi, sum_lo, sum_hi)

    def _force_stats(self, lo, hi, sum_lo, sum_hi):
        target = random.randint(sum_lo, sum_hi)
        atk = random.randint(lo, hi)
        df = random.randint(lo, hi)
        spd = target - atk - df
        spd = max(lo, min(hi, spd))
        return atk, df, spd

    def _determine_style(self, atk, df, spd, rarity):
        """Classify card style based on which stat dominates."""
        # Curse cards: all three stats negative
        if atk < 0 and df < 0 and spd < 0:
            return CardStyle.CURSE

        vals = {"atk": atk, "def": df, "spd": spd}
        best = max(vals, key=vals.get)
        if best == "atk":
            return CardStyle.ATTACK
        elif best == "def":
            return CardStyle.DEFENSE
        elif best == "spd":
            return CardStyle.SPEED

        # close stats → balance
        if max(atk, df, spd) - min(atk, df, spd) <= 4:
            return CardStyle.BALANCE

        return CardStyle.ATTACK

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self, rare_bonus=0, is_boss=False, force_rarity=None):
        """Create a single random card.

        Parameters:
            rare_bonus (int): Cumulative rare% bonus (0-45).
            is_boss (bool): Whether this is a boss level.
            force_rarity (CardRarity|None): Force a specific rarity
                (used for "神仙卡" or guaranteed curse cards).

        Returns:
            Card
        """
        rarity = force_rarity if force_rarity else self._roll_rarity(rare_bonus, is_boss)
        atk, df, spd = self._roll_stats(rarity)
        style = self._determine_style(atk, df, spd, rarity)
        adj = self._pick_adjective(style)
        noun = self._pick_noun()
        return Card(adj, noun, rarity, style, atk, df, spd)

    def generate_pair(self, rare_bonus=0, is_boss=False):
        """Generate two cards (the standard draw)."""
        return (
            self.generate(rare_bonus, is_boss),
            self.generate(rare_bonus, is_boss),
        )

    def generate_god_card(self):
        """Generate a '神仙卡' — all stats heavily positive."""
        return self.generate(
            force_rarity=CardRarity.EPIC,
        )

    def generate_curse_card(self):
        """Generate a guaranteed curse card for boss levels."""
        for _ in range(200):
            card = self.generate()
            if card.is_curse:
                return card
        # force a curse card manually
        return Card(
            "心魔", "噬魂幡", CardRarity.RARE, CardStyle.CURSE,
            -10, -10, -10
        )
