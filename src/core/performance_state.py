from dataclasses import dataclass
from enum import Enum


class Deck(Enum):
    DECK_1 = 1
    DECK_2 = 2


@dataclass
class PerformanceState:
    active_deck: Deck = Deck.DECK_1
    seek_speed_index: int = 0

    SEEK_SPEEDS = (1, 4, 16)

    @property
    def seek_speed(self) -> int:
        return self.SEEK_SPEEDS[self.seek_speed_index]

    def toggle_active_deck(self) -> Deck:
        if self.active_deck is Deck.DECK_1:
            self.active_deck = Deck.DECK_2
        else:
            self.active_deck = Deck.DECK_1

        return self.active_deck

    def cycle_seek_speed(self) -> int:
        self.seek_speed_index = (self.seek_speed_index + 1) % len(self.SEEK_SPEEDS)

        return self.seek_speed
