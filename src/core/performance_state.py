from dataclasses import dataclass
from enum import Enum


class Deck(Enum):
    DECK_1 = 1
    DECK_2 = 2


class BrowserFocus(Enum):
    TREE = 1
    TREE_EXPANDED = 2
    LIST = 3


class SeekMode(Enum):
    FINE = 1
    FOUR_BARS = 2
    EIGHT_BARS = 3

    @property
    def label(self) -> str:
        labels = {
            SeekMode.FINE: "Fine / Jog",
            SeekMode.FOUR_BARS: "4 Takte",
            SeekMode.EIGHT_BARS: "8 Takte",
        }

        return labels[self]


@dataclass
class PerformanceState:
    active_deck: Deck = Deck.DECK_1
    browser_focus: BrowserFocus = BrowserFocus.TREE
    seek_mode: SeekMode = SeekMode.FINE

    def toggle_active_deck(self) -> Deck:
        if self.active_deck is Deck.DECK_1:
            self.active_deck = Deck.DECK_2
        else:
            self.active_deck = Deck.DECK_1

        return self.active_deck

    def cycle_seek_mode(self) -> SeekMode:
        modes = list(SeekMode)
        current_index = modes.index(self.seek_mode)
        next_index = (current_index + 1) % len(modes)

        self.seek_mode = modes[next_index]

        return self.seek_mode

    def set_browser_focus(
        self,
        focus: BrowserFocus,
    ) -> BrowserFocus:
        self.browser_focus = focus
        return self.browser_focus
