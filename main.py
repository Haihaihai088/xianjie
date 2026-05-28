"""天劫 — Heavenly Tribulation
仙逸门末代弟子渡九重天劫，羽化登仙。
"""

import pygame
import sys
from src.core.game_loop import GameLoop, GameState
from src.systems.playing_state import PlayingState
from src.ui.menu import MenuState, LevelSelectState
from src.ui.stubs import (
    IntroState, LevelIntroState, LevelClearState,
    ChapterBreakState, GameOverState, EndingState,
)


def main():
    pygame.init()
    pygame.display.set_caption("天劫 — Heavenly Tribulation")

    game = GameLoop()

    # Register all state handlers
    game.register_handler(GameState.INTRO, IntroState())
    game.register_handler(GameState.MENU, MenuState())
    game.register_handler(GameState.LEVEL_SELECT, LevelSelectState())
    game.register_handler(GameState.LEVEL_INTRO, LevelIntroState())
    game.register_handler(GameState.PLAYING, PlayingState())
    game.register_handler(GameState.LEVEL_CLEAR, LevelClearState())
    game.register_handler(GameState.CHAPTER_BREAK, ChapterBreakState())
    game.register_handler(GameState.GAME_OVER, GameOverState())
    game.register_handler(GameState.ENDING, EndingState())

    # Start at menu (use switch_state so enter() is called)
    game.switch_state(GameState.MENU)

    game.run()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
