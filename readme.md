# 天劫 · Heavenly Tribulation

仙逸门末代弟子渡九重天劫，以卡牌抉择淬炼已身，羽化登仙。

A Chinese xianxia card game built with Pygame. Survive 10 layers of heavenly tribulation by choosing cards that boost your stats, build combos, and overcome the celestial trial.

---

## Quick Start

### Prerequisites
- Python 3.10+
- `pip install pygame`

```bash
pip install -r requirements.txt
python main.py
```

Or double-click `run_game.bat` (Windows).

### How to Play

1. **Main Menu** — Choose `开始渡劫` (new game) or `继续游戏` (continue from save)
2. **Card Selection** — Pick one of two cards each round. Cards have 3 stats:
   - `灵力` (ATK) — red bar
   - `根骨` (DEF) — gold bar
   - `身法` (SPD) — green bar
3. **Reach the Targets** — Fill all 3 stat bars to the target line before time runs out
4. **Combos** — Picking the same card style consecutively builds combo bonuses
5. **Ratings** — After clearing a level, you get an S/A/B/C rating and a talent title based on speed

### Controls

| Key | Action |
|-----|--------|
| `↑` `↓` `←` `→` | Navigate menus |
| `Enter` / `Space` | Confirm selection |
| `ESC` | Pause (in battle) / Back (in menus) |
| Mouse click | Select cards and menu items |

---

## Game Structure

```
HeavenlyTribulation/
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── run_game.bat             # Windows launcher
├── diagnose.bat             # Environment checker
├── readme.md                # You are here
├── .gitignore
├── ai_constraints.md        # AI collaboration rules
├── src/
│   ├── core/                # Game loop & state machine
│   │   └── game_loop.py
│   ├── entities/            # Game entities
│   │   └── card.py
│   ├── systems/             # Core gameplay
│   │   ├── card_generator.py
│   │   └── playing_state.py
│   ├── ui/                  # UI states
│   │   ├── menu.py          # Main menu & level select
│   │   ├── stubs.py         # Story, level clear, ending, game over
│   │   └── story_render.py  # Typewriter text effect
│   └── utils/               # Utilities
│       ├── audio.py         # Procedural sound effects
│       ├── font_helper.py   # CJK font loading
│       └── juice.py         # Visual effects (particles, shake)
├── data/                    # Game data (JSON)
│   ├── levels.json          # 10 level configurations
│   ├── story.json           # Narrative text
│   └── card_names.json      # Procedural card name database
├── ui/                      # UI assets
│   ├── menu_bg.png          # Main menu background
│   ├── battle_bg.png        # Battle background
│   ├── ending_bg.png        # Ending background
│   ├── main_menu_prototype.html  # HTML reference design
│   └── battle_prototype.html     # HTML reference design
├── docs/                    # Documentation
│   ├── ai_prompts.md        # AI image generation prompts
│   └── file_organization.md
├── saves/                   # Save files (auto-created)
└── tests/                   # Tests
```

---

## Levels

| # | Name | Type | ATK | DEF | SPD | Time |
|---|------|------|-----|-----|-----|------|
| 1 | 风劫 (Wind) | Normal | 20 | 20 | 20 | 12s |
| 2 | 火劫 (Fire) | Normal | 28 | 25 | 22 | 12s |
| 3 | 雷劫 (Thunder) | Normal | 36 | 32 | 28 | 10s |
| 4 | 冰劫 (Ice) | Normal | 42 | 38 | 40 | 10s |
| 5 | 五行劫 (Elements) | Boss | 60 | 25 | 50 | 8s |
| 6 | 阴阳劫 (Yin-Yang) | Normal | 55 | 52 | 48 | 8s |
| 7 | 时空劫 (Spacetime) | Normal | 65 | 58 | 60 | 7s |
| 8 | 寂灭劫 (Void) | Normal | 72 | 68 | 62 | 7s |
| 9 | 轮回劫 (Samsara) | Normal | 85 | 75 | 72 | 6s |
| 10 | 心魔劫 (Inner Demon) | Boss | 100 | 55 | 85 | 6s |

---

## Scoring

- **Base**: 1000 points per cleared level
- **Time Bonus**: remaining seconds × 50
- **Combo Bonus**: combo count × 200
- **Crit Bonus**: +150 per critical hit
- **Streak Multiplier**: up to 1.5× for fast consecutive picks

### Talent Titles (per-level, based on clear time)

| Time | Title | Color |
|------|-------|-------|
| ≤22s | 天道级 (e.g. 御风登仙) | Gold |
| ≤35s | 天资级 (e.g. 风驰苍穹) | Dark gold |
| ≤55s | 卓越级 (e.g. 踏风而行) | Cyan |
| >55s | 吐槽级 (e.g. 逆风挣扎) | Dark red |

### Immortal Titles (final, based on total score)

| Score | Title |
|-------|-------|
| ≥25000 | 大罗金仙 |
| ≥18000 | 太乙真仙 |
| ≥12000 | 天仙 |
| <12000 | 散仙 |

---

## Credits

Built with Python, Pygame, and AI-assisted coding.

All UI backgrounds generated via AI image tools. All sound effects procedurally synthesized.
