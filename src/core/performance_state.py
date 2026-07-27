from dataclasses import dataclass
from enum import Enum

from controller_config import SEEK_SPEEDS


class Deck(Enum):
    DECK_1 = 1
    DECK_2 = 2


class BrowserFocus(Enum):
    TREE = 1
    LIST = 2


@dataclass
class PerformanceState:
    active_deck: Deck = Deck.DECK_1
    seek_speed_index: int = 0
    browser_focus: BrowserFocus = BrowserFocus.TREE

    @property
    def seek_speed(self) -> int:
        return SEEK_SPEEDS[self.seek_speed_index]

    def toggle_active_deck(self) -> Deck:
        if self.active_deck is Deck.DECK_1:
            self.active_deck = Deck.DECK_2
        else:
            self.active_deck = Deck.DECK_1

        return self.active_deck

    def cycle_seek_speed(self) -> int:
        self.seek_speed_index = (self.seek_speed_index + 1) % len(SEEK_SPEEDS)

        return self.seek_speed

    def set_browser_focus(
        self,
        focus: BrowserFocus,
    ) -> BrowserFocus:
        self.browser_focus = focus
        return self.browser_focus
