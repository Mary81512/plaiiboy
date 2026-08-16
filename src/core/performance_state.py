from dataclasses import dataclass
from enum import Enum


class Deck(Enum):
    DECK_1 = 1
    DECK_2 = 2


class EQBand(Enum):
    HIGH = 1
    MID_HIGH = 2
    MID_LOW = 3
    LOW = 4

    @property
    def label(self) -> str:
        labels = {
            EQBand.HIGH: "High",
            EQBand.MID_HIGH: "Mid High",
            EQBand.MID_LOW: "Mid Low",
            EQBand.LOW: "Low",
        }

        return labels[self]


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
            SeekMode.FINE: "8 Takte",
            SeekMode.FOUR_BARS: "4 Takte",
            SeekMode.EIGHT_BARS: "1 Takt",
        }

        return labels[self]


@dataclass
class PerformanceState:
    active_deck: Deck = Deck.DECK_1
    browser_focus: BrowserFocus = BrowserFocus.TREE
    seek_mode: SeekMode = SeekMode.FINE

    deck_1_eq_band: EQBand = EQBand.HIGH
    deck_2_eq_band: EQBand = EQBand.HIGH

    deck_1_volume: float = 0.5
    deck_2_volume: float = 0.5

    deck_1_eq_high: float = 0.5
    deck_1_eq_mid_high: float = 0.5
    deck_1_eq_mid_low: float = 0.5
    deck_1_eq_low: float = 0.5

    deck_2_eq_high: float = 0.5
    deck_2_eq_mid_high: float = 0.5
    deck_2_eq_mid_low: float = 0.5
    deck_2_eq_low: float = 0.5

    mixer_fx_a_amount: float = 0.5
    mixer_fx_b_amount: float = 0.5

    selected_mixer_fx_deck: Deck = Deck.DECK_1

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

    def move_deck_1_eq_band(self, direction: int) -> EQBand:
        bands = list(EQBand)
        current_index = bands.index(self.deck_1_eq_band)

        new_index = max(
            0,
            min(
                len(bands) - 1,
                current_index + direction,
            ),
        )

        self.deck_1_eq_band = bands[new_index]
        return self.deck_1_eq_band

    def move_deck_2_eq_band(self, direction: int) -> EQBand:
        bands = list(EQBand)
        current_index = bands.index(self.deck_2_eq_band)

        new_index = max(
            0,
            min(
                len(bands) - 1,
                current_index + direction,
            ),
        )

        self.deck_2_eq_band = bands[new_index]
        return self.deck_2_eq_band

    def select_mixer_fx_deck(
        self,
        deck: Deck,
    ) -> Deck:
        self.selected_mixer_fx_deck = deck
        return self.selected_mixer_fx_deck
