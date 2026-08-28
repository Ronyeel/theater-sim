
import os
import sys
import random
import pygame

from game.settings import (
    SCREEN_W, SCREEN_H, FPS, GAME_TITLE, RANDOM_SEED,
    DEFAULT_CASHIERS, DEFAULT_USHERS, DEFAULT_SERVERS,
    DEFAULT_RUNTIME, DEFAULT_ARRIVAL_INTERVAL, DEFAULT_FOOD_PROB,
    UI_DIR,
)
from game.backend_bridge import TheaterSimulationBridge
from game.screens import (
    MainMenu, SetupScreen, GameScreen, ResultsScreen
)

STATE_TITLE   = "title"
STATE_SETUP   = "setup"
STATE_GAME    = "game"
STATE_RESULTS = "results"


class App:

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self._current_state = STATE_TITLE
        self.bridge = TheaterSimulationBridge(
            num_cashiers=DEFAULT_CASHIERS,
            num_servers=DEFAULT_SERVERS,
            num_ushers=DEFAULT_USHERS,
            arrival_interval=DEFAULT_ARRIVAL_INTERVAL,
            food_probability=DEFAULT_FOOD_PROB,
            runtime=DEFAULT_RUNTIME,
            speed=1,
            seed=RANDOM_SEED,
        )
        self._screens = {}
        self._init_screens()

    def _init_screens(self) -> None:
        self._screens[STATE_TITLE] = MainMenu(
            go_start=self._switch(STATE_GAME),
            go_setup=self._switch(STATE_SETUP),
        )
        self._screens[STATE_SETUP] = SetupScreen(
            bridge=self.bridge,
            go_game=self._switch(STATE_GAME),
            go_back=self._switch(STATE_TITLE),
        )
        self._screens[STATE_GAME] = GameScreen(
            go_title=self._switch(STATE_TITLE),
            go_results=self._switch(STATE_RESULTS),
            bridge=self.bridge,
        )
        self._screens[STATE_RESULTS] = ResultsScreen(
            bridge=self.bridge,
            go_game=self._switch(STATE_GAME),
            go_setup=self._switch(STATE_SETUP),
            go_title=self._switch(STATE_TITLE),
            quit_game=self.quit,
        )

    def _switch(self, target_state: str):
        def transition():
            if target_state == STATE_GAME:
                self._screens[STATE_GAME] = GameScreen(
                    go_title=self._switch(STATE_TITLE),
                    go_results=self._switch(STATE_RESULTS),
                    bridge=self.bridge,
                )
            elif target_state == STATE_RESULTS:
                self._screens[STATE_RESULTS] = ResultsScreen(
                    bridge=self.bridge,
                    go_game=self._switch(STATE_GAME),
                    go_setup=self._switch(STATE_SETUP),
                    go_title=self._switch(STATE_TITLE),
                    quit_game=self.quit,
                )
            self._current_state = target_state
        return transition


    @property
    def current(self):
        return self._screens[self._current_state]

    def handle_event(self, evt: pygame.event.Event) -> None:
        if evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE:
            if self._current_state == STATE_TITLE:
                self.quit()
                return
            elif self._current_state in (STATE_SETUP, STATE_RESULTS):
                self._current_state = STATE_TITLE
                return
        self.current.handle_event(evt)

    def update(self, dt: float) -> None:
        self.current.update(dt)

    def draw(self) -> None:
        self.current.draw(self.surface)

    def quit(self) -> None:
        pygame.quit()
        sys.exit(0)


def main() -> None:
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)
    pygame.init()
    pygame.display.set_caption(GAME_TITLE)

    _icon_path = os.path.join(UI_DIR, "game_icon.png")
    if os.path.exists(_icon_path):
        icon = pygame.image.load(_icon_path)
    else:
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(icon, (255, 210, 80), (4, 4, 24, 24), border_radius=4)
        pygame.draw.rect(icon, (255, 80, 180), (8, 8, 16, 16), 2, border_radius=2)
    pygame.display.set_icon(icon)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    app = App(screen)

    while True:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app.quit()
            app.handle_event(event)

        app.update(dt)
        app.draw()
        pygame.display.flip()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
