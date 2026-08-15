from collections.abc import Callable

from core.actions import Action, ActionEvent
from core.events import Axis, ControllerEvent, EventType
from core.performance_state import (
    BrowserFocus,
    Deck,
    EQBand,
    PerformanceState,
    SeekMode,
)

ActionHandler = Callable[
    [ActionEvent],
    list[ActionEvent],
]


class ActionProcessor:
    MIXER_DEADZONE = 0.20

    # Änderung pro Sekunde bei vollem Stickausschlag.
    VOLUME_SPEED = 0.60
    EQ_SPEED = 0.60
    MIXER_FX_SPEED = 0.50

    # Verhindert extrem große Sprünge, falls der Main-Loop
    # einmal kurz hängen sollte.
    MAX_DELTA_TIME = 0.05

    def __init__(
        self,
        state: PerformanceState | None = None,
    ) -> None:
        self._state = state if state is not None else PerformanceState()

        self._handlers: dict[
            Action,
            ActionHandler,
        ] = {
            Action.TOGGLE_ACTIVE_DECK: self._toggle_active_deck,
            Action.CYCLE_SEEK_SPEED: self._cycle_seek_speed,
            # Layer 2
            Action.CYCLE_DECK_1_EQ_BAND: self._cycle_deck_1_eq_band,
            Action.CYCLE_DECK_2_EQ_BAND: self._cycle_deck_2_eq_band,
            # Seek
            Action.ACTIVE_DECK_SEEK_BACKWARD: self._seek_backward,
            Action.ACTIVE_DECK_SEEK_FORWARD: self._seek_forward,
            # Browser
            Action.BROWSER_UP: self._browser_up,
            Action.BROWSER_DOWN: self._browser_down,
            Action.BROWSER_LEVEL_UP: self._browser_level_up,
            Action.BROWSER_LEVEL_DOWN: self._browser_level_down,
            Action.TOGGLE_MIXER_FX_A_DIRECTION: (self._toggle_mixer_fx_a_direction),
            Action.TOGGLE_MIXER_FX_B_DIRECTION: (self._toggle_mixer_fx_b_direction),
        }

    @property
    def state(self) -> PerformanceState:
        return self._state

    # -------------------------------------------------------------------------
    # Normale Action-Verarbeitung
    # -------------------------------------------------------------------------

    def process(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        handler = self._handlers.get(event.action)

        if handler is not None:
            return handler(event)

        resolved_action = self._resolve_active_deck_action(event.action)

        if resolved_action is None:
            return [event]

        return [
            self._replace_action(
                event=event,
                action=resolved_action,
            )
        ]

    # -------------------------------------------------------------------------
    # Layer 2 – kontinuierliche Mixer-Sticks
    # -------------------------------------------------------------------------

    def process_mixer_axes(
        self,
        left_x: float,
        left_y: float,
        right_x: float,
        right_y: float,
        delta_time: float,
    ) -> list[ActionEvent]:
        """
        Relative Mixer-Steuerung für Layer 2.

        Linker Stick:
            Y -> Deck 1 Volume
            X -> ausgewähltes Deck-1-EQ-Band

        Rechter Stick:
            Y -> Deck 2 Volume
            X -> ausgewähltes Deck-2-EQ-Band

        Die stärkere Achse eines Sticks gewinnt.
        Dadurch verändert eine leichte diagonale Bewegung nicht
        gleichzeitig Volume und EQ.
        """

        delta_time = max(
            0.0,
            min(
                delta_time,
                self.MAX_DELTA_TIME,
            ),
        )

        if delta_time == 0.0:
            return []

        events: list[ActionEvent] = []

        events.extend(
            self._process_deck_stick(
                deck=Deck.DECK_1,
                x=left_x,
                y=left_y,
                delta_time=delta_time,
            )
        )

        events.extend(
            self._process_deck_stick(
                deck=Deck.DECK_2,
                x=right_x,
                y=right_y,
                delta_time=delta_time,
            )
        )

        return events

    def process_mixer_fx_triggers(
        self,
        l2: float,
        r2: float,
        delta_time: float,
    ) -> list[ActionEvent]:
        delta_time = max(
            0.0,
            min(
                delta_time,
                self.MAX_DELTA_TIME,
            ),
        )

        if delta_time == 0.0:
            return []

        events: list[ActionEvent] = []

        if l2 > 0.02:
            delta = (
                l2 * self.MIXER_FX_SPEED * delta_time * self._state.mixer_fx_a_direction
            )

            old_value = self._state.mixer_fx_a_amount
            new_value = self._clamp(old_value + delta)

            if new_value != old_value:
                self._state.mixer_fx_a_amount = new_value

                events.append(
                    self._create_axis_action(
                        action=Action.MIXER_FX_A_AMOUNT,
                        axis=Axis.L2,
                        action_value=new_value,
                        stick_value=l2,
                    )
                )

        if r2 > 0.02:
            delta = (
                r2 * self.MIXER_FX_SPEED * delta_time * self._state.mixer_fx_b_direction
            )

            old_value = self._state.mixer_fx_b_amount
            new_value = self._clamp(old_value + delta)

            if new_value != old_value:
                self._state.mixer_fx_b_amount = new_value

                events.append(
                    self._create_axis_action(
                        action=Action.MIXER_FX_B_AMOUNT,
                        axis=Axis.R2,
                        action_value=new_value,
                        stick_value=r2,
                    )
                )

        return events

    def _toggle_mixer_fx_a_direction(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        direction = self._state.toggle_mixer_fx_a_direction()

        label = "hoch" if direction > 0 else "runter"
        print(f"Mixer FX A Richtung: {label}")

        return []

    def _toggle_mixer_fx_b_direction(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        direction = self._state.toggle_mixer_fx_b_direction()

        label = "hoch" if direction > 0 else "runter"
        print(f"Mixer FX B Richtung: {label}")

        return []

    def _process_deck_stick(
        self,
        deck: Deck,
        x: float,
        y: float,
        delta_time: float,
    ) -> list[ActionEvent]:
        x_active = abs(x) >= self.MIXER_DEADZONE
        y_active = abs(y) >= self.MIXER_DEADZONE

        if not x_active and not y_active:
            return []

        # Nur die dominante Achse verwenden.
        # Das verhindert Cross-Axis-Jitter.
        if x_active and (not y_active or abs(x) >= abs(y)):
            return self._process_eq_axis(
                deck=deck,
                value=x,
                delta_time=delta_time,
            )

        return self._process_volume_axis(
            deck=deck,
            value=y,
            delta_time=delta_time,
        )

    # -------------------------------------------------------------------------
    # Layer 2 – Volume
    # -------------------------------------------------------------------------

    def _process_volume_axis(
        self,
        deck: Deck,
        value: float,
        delta_time: float,
    ) -> list[ActionEvent]:
        # DualShock:
        # oben  = negativ
        # unten = positiv
        #
        # Deshalb Minuszeichen:
        # oben  -> Volume steigt
        # unten -> Volume sinkt
        delta = -value * self.VOLUME_SPEED * delta_time

        if deck is Deck.DECK_1:
            old_value = self._state.deck_1_volume

            new_value = self._clamp(old_value + delta)

            if new_value == old_value:
                return []

            self._state.deck_1_volume = new_value

            action = Action.DECK_1_VOLUME
            axis = Axis.LEFT_Y

        else:
            old_value = self._state.deck_2_volume

            new_value = self._clamp(old_value + delta)

            if new_value == old_value:
                return []

            self._state.deck_2_volume = new_value

            action = Action.DECK_2_VOLUME
            axis = Axis.RIGHT_Y

        return [
            self._create_axis_action(
                action=action,
                axis=axis,
                action_value=new_value,
                stick_value=value,
            )
        ]

    # -------------------------------------------------------------------------
    # Layer 2 – EQ
    # -------------------------------------------------------------------------

    def _process_eq_axis(
        self,
        deck: Deck,
        value: float,
        delta_time: float,
    ) -> list[ActionEvent]:
        # links  -> kleiner
        # rechts -> größer
        delta = value * self.EQ_SPEED * delta_time

        if deck is Deck.DECK_1:
            band = self._state.deck_1_eq_band
            axis = Axis.LEFT_X

            if band is EQBand.HIGH:
                old_value = self._state.deck_1_eq_high
                new_value = self._clamp(old_value + delta)
                self._state.deck_1_eq_high = new_value
                action = Action.DECK_1_EQ_HIGH

            elif band is EQBand.MID:
                old_value = self._state.deck_1_eq_mid
                new_value = self._clamp(old_value + delta)
                self._state.deck_1_eq_mid = new_value
                action = Action.DECK_1_EQ_MID

            else:
                old_value = self._state.deck_1_eq_low
                new_value = self._clamp(old_value + delta)
                self._state.deck_1_eq_low = new_value
                action = Action.DECK_1_EQ_LOW

        else:
            band = self._state.deck_2_eq_band
            axis = Axis.RIGHT_X

            if band is EQBand.HIGH:
                old_value = self._state.deck_2_eq_high
                new_value = self._clamp(old_value + delta)
                self._state.deck_2_eq_high = new_value
                action = Action.DECK_2_EQ_HIGH

            elif band is EQBand.MID:
                old_value = self._state.deck_2_eq_mid
                new_value = self._clamp(old_value + delta)
                self._state.deck_2_eq_mid = new_value
                action = Action.DECK_2_EQ_MID

            else:
                old_value = self._state.deck_2_eq_low
                new_value = self._clamp(old_value + delta)
                self._state.deck_2_eq_low = new_value
                action = Action.DECK_2_EQ_LOW

        if new_value == old_value:
            return []

        return [
            self._create_axis_action(
                action=action,
                axis=axis,
                action_value=new_value,
                stick_value=value,
            )
        ]

    # -------------------------------------------------------------------------
    # Layer 2 – EQ-Band auswählen
    # -------------------------------------------------------------------------

    def _cycle_deck_1_eq_band(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        band = self._state.cycle_deck_1_eq_band()

        print(f"Deck 1 EQ-Band: {band.label}")

        return []

    def _cycle_deck_2_eq_band(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        band = self._state.cycle_deck_2_eq_band()

        print(f"Deck 2 EQ-Band: {band.label}")

        return []

    # -------------------------------------------------------------------------
    # Active Deck
    # -------------------------------------------------------------------------

    def _toggle_active_deck(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        active_deck = self._state.toggle_active_deck()

        feedback_action = (
            Action.FEEDBACK_ACTIVE_DECK_1
            if active_deck is Deck.DECK_1
            else Action.FEEDBACK_ACTIVE_DECK_2
        )

        return [
            ActionEvent(
                action=feedback_action,
                value=float(active_deck.value),
                source_event=event.source_event,
            )
        ]

    # -------------------------------------------------------------------------
    # Seek Mode
    # -------------------------------------------------------------------------

    def _cycle_seek_speed(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        seek_mode = self._state.cycle_seek_mode()

        return [
            ActionEvent(
                action=Action.CYCLE_SEEK_SPEED,
                value=float(seek_mode.value),
                source_event=event.source_event,
            )
        ]

    # -------------------------------------------------------------------------
    # Browser
    # -------------------------------------------------------------------------

    def _browser_up(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        if self._state.browser_focus is BrowserFocus.LIST:
            action = Action.BROWSER_LIST_UP
        else:
            self._state.set_browser_focus(BrowserFocus.TREE)
            action = Action.BROWSER_TREE_UP

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _browser_down(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        if self._state.browser_focus is BrowserFocus.LIST:
            action = Action.BROWSER_LIST_DOWN
        else:
            self._state.set_browser_focus(BrowserFocus.TREE)
            action = Action.BROWSER_TREE_DOWN

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _browser_level_down(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        if self._state.browser_focus is BrowserFocus.LIST:
            return []

        if self._state.browser_focus is BrowserFocus.TREE_EXPANDED:
            self._state.set_browser_focus(BrowserFocus.LIST)
            return []

        self._state.set_browser_focus(BrowserFocus.TREE_EXPANDED)

        return [
            self._replace_action(
                event=event,
                action=Action.BROWSER_TREE_EXPAND,
            )
        ]

    def _browser_level_up(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        if self._state.browser_focus is BrowserFocus.LIST:
            self._state.set_browser_focus(BrowserFocus.TREE_EXPANDED)
            return []

        self._state.set_browser_focus(BrowserFocus.TREE)

        return [
            self._replace_action(
                event=event,
                action=Action.BROWSER_TREE_COLLAPSE,
            )
        ]

    # -------------------------------------------------------------------------
    # Seek
    # -------------------------------------------------------------------------

    def _seek_backward(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = self._resolve_seek_action(
            backward=True,
        )

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _seek_forward(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = self._resolve_seek_action(
            backward=False,
        )

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _resolve_seek_action(
        self,
        backward: bool,
    ) -> Action:
        if self._state.active_deck is Deck.DECK_1:
            mappings = {
                SeekMode.FINE: (
                    Action.DECK_1_SEEK_FINE_BACKWARD
                    if backward
                    else Action.DECK_1_SEEK_FINE_FORWARD
                ),
                SeekMode.FOUR_BARS: (
                    Action.DECK_1_SEEK_4_BARS_BACKWARD
                    if backward
                    else Action.DECK_1_SEEK_4_BARS_FORWARD
                ),
                SeekMode.EIGHT_BARS: (
                    Action.DECK_1_SEEK_8_BARS_BACKWARD
                    if backward
                    else Action.DECK_1_SEEK_8_BARS_FORWARD
                ),
            }

        else:
            mappings = {
                SeekMode.FINE: (
                    Action.DECK_2_SEEK_FINE_BACKWARD
                    if backward
                    else Action.DECK_2_SEEK_FINE_FORWARD
                ),
                SeekMode.FOUR_BARS: (
                    Action.DECK_2_SEEK_4_BARS_BACKWARD
                    if backward
                    else Action.DECK_2_SEEK_4_BARS_FORWARD
                ),
                SeekMode.EIGHT_BARS: (
                    Action.DECK_2_SEEK_8_BARS_BACKWARD
                    if backward
                    else Action.DECK_2_SEEK_8_BARS_FORWARD
                ),
            }

        return mappings[self._state.seek_mode]

    # -------------------------------------------------------------------------
    # Aktives Deck – Hotcues
    # -------------------------------------------------------------------------

    def _resolve_active_deck_action(
        self,
        action: Action,
    ) -> Action | None:
        if self._state.active_deck is Deck.DECK_1:
            mappings = {
                Action.ACTIVE_DECK_HOTCUE_PREVIOUS: Action.DECK_1_HOTCUE_PREVIOUS,
                Action.ACTIVE_DECK_HOTCUE_NEXT: Action.DECK_1_HOTCUE_NEXT,
                Action.ACTIVE_DECK_HOTCUE_TOGGLE: Action.DECK_1_HOTCUE_TOGGLE,
            }

        else:
            mappings = {
                Action.ACTIVE_DECK_HOTCUE_PREVIOUS: Action.DECK_2_HOTCUE_PREVIOUS,
                Action.ACTIVE_DECK_HOTCUE_NEXT: Action.DECK_2_HOTCUE_NEXT,
                Action.ACTIVE_DECK_HOTCUE_TOGGLE: Action.DECK_2_HOTCUE_TOGGLE,
            }

        return mappings.get(action)

    # -------------------------------------------------------------------------
    # Helper
    # -------------------------------------------------------------------------

    def _create_axis_action(
        self,
        action: Action,
        axis: Axis,
        action_value: float,
        stick_value: float,
    ) -> ActionEvent:
        source_event = ControllerEvent(
            event_type=EventType.AXIS_CHANGED,
            control=axis,
            value=stick_value,
        )

        return ActionEvent(
            action=action,
            value=action_value,
            source_event=source_event,
        )

    def _replace_action(
        self,
        event: ActionEvent,
        action: Action,
    ) -> ActionEvent:
        return ActionEvent(
            action=action,
            value=event.value,
            source_event=event.source_event,
        )

    def _clamp(
        self,
        value: float,
    ) -> float:
        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )
