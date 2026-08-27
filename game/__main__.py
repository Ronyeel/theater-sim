"""
CinePlex Dreams — Entry Point
Run: .venv/Scripts/python -m game
"""
import sys
import random
import pygame
from game.settings import SCREEN_W, SCREEN_H, FPS, GAME_TITLE, RANDOM_SEED
from game.screens.main_menu import MainMenu
from game.screens.exterior_screen import ExteriorScreen
from game.screens.game_screen import GameScreen

TITLE    = "title"
EXTERIOR = "exterior"
GAME     = "game"


class App:
    def __init__(self, surface):
        self.surface = surface
        self._current = TITLE
        self._screens = {}
        self._build()

    def _build(self):
        self._screens[TITLE]    = MainMenu(self._go(EXTERIOR))
        self._screens[EXTERIOR] = ExteriorScreen(self._go(GAME))
        self._screens[GAME]     = GameScreen(self._go(TITLE))

    def _go(self, name):
        def switch():
            self._current = name
            if name == EXTERIOR:
                self._screens[EXTERIOR] = ExteriorScreen(self._go(GAME))
            elif name == GAME:
                self._screens[GAME] = GameScreen(self._go(TITLE))
        return switch

    @property
    def current(self):
        return self._screens[self._current]

    def handle_event(self, evt):
        self.current.handle_event(evt)

    def update(self, dt):
        self.current.update(dt)

    def draw(self):
        self.current.draw(self.surface)


def main():
    random.seed(RANDOM_SEED)
    pygame.init()
    pygame.display.set_caption(GAME_TITLE)

    # Icon
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(icon, (255, 210, 80), (4, 4, 24, 24), border_radius=4)
    pygame.draw.rect(icon, (255, 80, 180), (8, 8, 16, 16), 2, border_radius=2)
    pygame.display.set_icon(icon)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()
    app    = App(screen)

    while True:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            app.handle_event(event)

        app.update(dt)
        app.draw()
        pygame.display.flip()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl+C is a normal way to stop a game launched from PowerShell.
        # Exit without treating it as a runtime error or printing a traceback.
        pygame.quit()
