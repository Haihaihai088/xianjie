"""Card entity — represents an "机缘" (opportunity) the player can absorb."""

from enum import Enum, auto


class CardStyle(Enum):
    """The affinity of a card — determines combo chains."""
    ATTACK = auto()    # 灵力向
    DEFENSE = auto()   # 根骨向
    SPEED = auto()     # 身法向
    BALANCE = auto()   # 均衡向
    CURSE = auto()     # 心魔/诅咒


class CardRarity(Enum):
    COMMON = "普通"
    RARE = "稀有"
    EPIC = "史诗"

    @property
    def display_color(self):
        return {
            CardRarity.COMMON: (220, 220, 220),    # white
            CardRarity.RARE: (80, 180, 220),        # cyan-blue
            CardRarity.EPIC: (200, 160, 60),        # gold-purple
        }[self]


class Card:
    __slots__ = (
        "name", "adjective", "noun", "rarity", "style",
        "atk_mod", "def_mod", "spd_mod",
    )

    def __init__(self, adjective, noun, rarity, style, atk, df, spd):
        self.adjective = adjective
        self.noun = noun
        self.name = f"{adjective} · {noun}"
        self.rarity = rarity      # CardRarity
        self.style = style        # CardStyle
        self.atk_mod = atk        # int
        self.def_mod = df         # int
        self.spd_mod = spd        # int

    @property
    def is_curse(self):
        return self.style == CardStyle.CURSE

    @property
    def rarity_name(self):
        return self.rarity.value

    @property
    def rarity_color(self):
        return self.rarity.display_color

    def summary(self):
        """One-line description for debug."""
        return (
            f"{self.name} [{self.rarity_name}] "
            f"灵{self.atk_mod:+d} 骨{self.def_mod:+d} 身{self.spd_mod:+d}"
        )
