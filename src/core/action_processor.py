from collections.abc import Callable

from core.actions import Action, ActionEvent
from core.events import Axis, ControllerEvent, EventType
from core.performance_state import (
    BrowserFocus,
    Deck,
    EQBand,
    FXParameter,
    PerformanceState,
    SeekMode,
)

ActionHandler = Callable[
    [ActionEvent],
    list[ActionEvent],
]


class ActionProcessor:
    MIXER_DEADZONE = 0.20

    TOUCHPAD_WIDTH = 1920
    TOUCHPAD_HEIGHT = 942

    # Änderung pro Sekunde bei vollem Stickausschlag.
    VOLUME_SPEED = 0.60
    EQ_SPEED = 0.60
    MIXER_FX_SPEED = 0.50
    FX_PARAM_SPEED = 0.60
    FX_DRY_WET_SPEED = 0.50

    # Verhindert extrem große Sprünge, falls der Main-Loop
    # einmal kurz hängen sollte.
    MAX_DELTA_TIME = 0.05

    def __init__(
        self,
        state: PerformanceState | None = None,
    ) -> None:
        self._state = state if state is not None else PerformanceState()
        # Letzte Touchpad-Position pro Finger.
        # Damit wird das Touchpad relativ wie ein Scroll-Fader benutzt.
        self._touchpad_previous: dict[int, tuple[Deck, int]] = {}
        self._fx_trigger_accumulator = 0.0

        self._handlers: dict[
            Action,
            ActionHandler,
        ] = {
            Action.TOGGLE_ACTIVE_DECK: self._toggle_active_deck,
            Action.CYCLE_SEEK_SPEED: self._cycle_seek_speed,
            Action.DECK_1_EQ_BAND_UP: self._deck_1_eq_band_up,
            Action.DECK_1_EQ_BAND_DOWN: self._deck_1_eq_band_down,
            Action.DECK_2_EQ_BAND_UP: self._deck_2_eq_band_up,
            Action.DECK_2_EQ_BAND_DOWN: self._deck_2_eq_band_down,
            Action.TOGGLE_DECK_1_EQ_BAND: self._toggle_deck_1_eq_band,
            Action.TOGGLE_DECK_2_EQ_BAND: self._toggle_deck_2_eq_band,
            # Seek
            Action.ACTIVE_DECK_SEEK_BACKWARD: self._seek_backward,
            Action.ACTIVE_DECK_SEEK_FORWARD: self._seek_forward,
            # Browser
            Action.BROWSER_UP: self._browser_up,
            Action.BROWSER_DOWN: self._browser_down,
            Action.BROWSER_LEVEL_UP: self._browser_level_up,
            Action.BROWSER_LEVEL_DOWN: self._browser_level_down,
            Action.SELECT_MIXER_FX_DECK_A: (self._select_mixer_fx_deck_a),
            Action.SELECT_MIXER_FX_DECK_B: (self._select_mixer_fx_deck_b),
            # Layer 3 – Single FX
            Action.SELECT_FX_UNIT_1: self._select_fx_unit_1,
            Action.SELECT_FX_UNIT_2: self._select_fx_unit_2,
            Action.FX_SELECTED_EFFECT_PREVIOUS: (self._fx_selected_effect_previous),
            Action.FX_SELECTED_EFFECT_NEXT: (self._fx_selected_effect_next),
            Action.FX_UNIT_1_PARAM_PREVIOUS: (self._fx_unit_1_param_previous),
            Action.FX_UNIT_1_PARAM_NEXT: (self._fx_unit_1_param_next),
            Action.FX_UNIT_2_PARAM_PREVIOUS: (self._fx_unit_2_param_previous),
            Action.FX_UNIT_2_PARAM_NEXT: (self._fx_unit_2_param_next),
            Action.FX_UNIT_1_TOGGLE_SELECTED_PARAM: (
                self._fx_unit_1_toggle_selected_param
            ),
            Action.FX_UNIT_2_TOGGLE_SELECTED_PARAM: (
                self._fx_unit_2_toggle_selected_param
            ),
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

        # Layer 2:
        # Die Stick-X-Achsen steuern weiterhin den ausgewählten EQ.
        # Stick-Y bleibt ab jetzt frei für die spätere 4-Band-Auswahl.

        if abs(left_x) >= self.MIXER_DEADZONE:
            events.extend(
                self._process_eq_axis(
                    deck=Deck.DECK_1,
                    value=left_x,
                    delta_time=delta_time,
                )
            )

        if abs(right_x) >= self.MIXER_DEADZONE:
            events.extend(
                self._process_eq_axis(
                    deck=Deck.DECK_2,
                    value=right_x,
                    delta_time=delta_time,
                )
            )

        return events

    def process_touchpad_volumes(
        self,
        touches,
    ) -> list[ActionEvent]:
        """
        Layer 2 – relative Touchpad-Fader.

        Linke Hälfte  -> Deck A Volume
        Rechte Hälfte -> Deck B Volume

        Aufsetzen verändert nichts.
        Erst die Bewegung des Fingers erzeugt relative MIDI-Schritte.
        """

        events: list[ActionEvent] = []

        active_finger_ids = set(touches.keys())

        # Finger, die nicht mehr auf dem Touchpad liegen, vergessen.
        for finger_id in list(self._touchpad_previous):
            if finger_id not in active_finger_ids:
                del self._touchpad_previous[finger_id]

        half_width = self.TOUCHPAD_WIDTH / 2

        for finger_id, touch in touches.items():
            deck = Deck.DECK_1 if touch.x < half_width else Deck.DECK_2

            previous = self._touchpad_previous.get(finger_id)

            # Aktuelle Position immer für den nächsten Frame speichern.
            self._touchpad_previous[finger_id] = (
                deck,
                touch.y,
            )

            # Neu aufgesetzter Finger:
            # noch KEINE Lautstärkeänderung.
            if previous is None:
                continue

            previous_deck, previous_y = previous

            # Wenn der Finger über die Mitte auf das andere Deck
            # gewechselt ist, dort ebenfalls erst neu "ansetzen".
            if previous_deck is not deck:
                continue

            delta_y = touch.y - previous_y

            # Sehr kleine Sensorbewegungen ignorieren.
            if abs(delta_y) < 2:
                continue

            # Touchpad:
            # nach oben   -> positiver Wert -> Volume höher
            # nach unten  -> negativer Wert -> Volume niedriger
            relative_value = -(delta_y / self.TOUCHPAD_HEIGHT)

            if deck is Deck.DECK_1:
                action = Action.DECK_1_VOLUME
                axis = Axis.LEFT_Y
            else:
                action = Action.DECK_2_VOLUME
                axis = Axis.RIGHT_Y

            events.append(
                self._create_axis_action(
                    action=action,
                    axis=axis,
                    action_value=relative_value,
                    stick_value=relative_value,
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

        # L2 = weniger
        # R2 = mehr
        relative_value = (r2 - l2) * self.MIXER_FX_SPEED * delta_time

        if abs(relative_value) < 0.000001:
            return []

        selected_deck = self._state.selected_mixer_fx_deck

        if selected_deck is Deck.DECK_1:
            action = Action.MIXER_FX_A_AMOUNT
        else:
            action = Action.MIXER_FX_B_AMOUNT

        axis = Axis.R2 if relative_value > 0 else Axis.L2

        return [
            self._create_axis_action(
                action=action,
                axis=axis,
                action_value=relative_value,
                stick_value=abs(r2 - l2),
            )
        ]

    # -------------------------------------------------------------------------
    # Layer 3 – Single FX kontinuierlich
    # -------------------------------------------------------------------------

    def process_fx_axes(
        self,
        left_y: float,
        right_y: float,
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

        # DualShock:
        # Stick hoch = negativer Wert.
        # Wir drehen deshalb das Vorzeichen um:
        # hoch   -> Parameter größer
        # runter -> Parameter kleiner

        left_value = -self._apply_deadzone(left_y)

        if left_value != 0.0:
            mappings = {
                FXParameter.PARAM_1: Action.FX_UNIT_1_PARAM_1,
                FXParameter.PARAM_2: Action.FX_UNIT_1_PARAM_2,
                FXParameter.PARAM_3: Action.FX_UNIT_1_PARAM_3,
            }

            relative_value = left_value * self.FX_PARAM_SPEED * delta_time

            events.append(
                self._create_axis_action(
                    action=mappings[self._state.fx_unit_1_parameter],
                    axis=Axis.LEFT_Y,
                    action_value=relative_value,
                    stick_value=left_y,
                )
            )

        right_value = -self._apply_deadzone(right_y)

        if right_value != 0.0:
            mappings = {
                FXParameter.PARAM_1: Action.FX_UNIT_2_PARAM_1,
                FXParameter.PARAM_2: Action.FX_UNIT_2_PARAM_2,
                FXParameter.PARAM_3: Action.FX_UNIT_2_PARAM_3,
            }

            relative_value = right_value * self.FX_PARAM_SPEED * delta_time

            events.append(
                self._create_axis_action(
                    action=mappings[self._state.fx_unit_2_parameter],
                    axis=Axis.RIGHT_Y,
                    action_value=relative_value,
                    stick_value=right_y,
                )
            )

        return events

    def process_fx_triggers(
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

        # L2 = weniger
        # R2 = mehr
        #
        # Trigger sind analog 0.0 bis 1.0.
        # Je weiter gedrückt, desto schneller soll sich Dry/Wet bewegen.
        trigger_value = r2 - l2

        # Kleine Restwerte ignorieren.
        if abs(trigger_value) < 0.01:
            return []

        self._fx_trigger_accumulator += (
            trigger_value * self.FX_DRY_WET_SPEED * delta_time * 60.0
        )

        # Noch nicht genug Bewegung für einen MIDI-Schritt gesammelt.
        if abs(self._fx_trigger_accumulator) < 1.0:
            return []

        steps = int(abs(self._fx_trigger_accumulator))

        steps = min(
            steps,
            63,
        )

        if self._fx_trigger_accumulator > 0:
            relative_value = steps / 63.0
            self._fx_trigger_accumulator -= steps
            axis = Axis.R2

        else:
            relative_value = -(steps / 63.0)
            self._fx_trigger_accumulator += steps
            axis = Axis.L2

        action = (
            Action.FX_UNIT_1_DRY_WET
            if self._state.selected_fx_unit == 1
            else Action.FX_UNIT_2_DRY_WET
        )

        return [
            self._create_axis_action(
                action=action,
                axis=axis,
                action_value=relative_value,
                stick_value=abs(trigger_value),
            )
        ]

    def _select_fx_unit_1(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        self._state.select_fx_unit(1)
        print("FX Steuerung: Unit 1")
        return []

    def _select_fx_unit_2(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        self._state.select_fx_unit(2)
        print("FX Steuerung: Unit 2")
        return []

    def _fx_selected_effect_previous(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = (
            Action.FX_UNIT_1_EFFECT_PREVIOUS
            if self._state.selected_fx_unit == 1
            else Action.FX_UNIT_2_EFFECT_PREVIOUS
        )

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _fx_selected_effect_next(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = (
            Action.FX_UNIT_1_EFFECT_NEXT
            if self._state.selected_fx_unit == 1
            else Action.FX_UNIT_2_EFFECT_NEXT
        )

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _fx_unit_1_param_previous(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        parameter = self._state.move_fx_unit_1_parameter(-1)

        print(f"FX Unit 1: {parameter.label}")

        return []

    def _fx_unit_1_param_next(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        parameter = self._state.move_fx_unit_1_parameter(1)

        print(f"FX Unit 1: {parameter.label}")

        return []

    def _fx_unit_2_param_previous(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        parameter = self._state.move_fx_unit_2_parameter(-1)

        print(f"FX Unit 2: {parameter.label}")

        return []

    def _fx_unit_2_param_next(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        parameter = self._state.move_fx_unit_2_parameter(1)

        print(f"FX Unit 2: {parameter.label}")

        return []

    def _fx_unit_1_toggle_selected_param(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        mappings = {
            FXParameter.PARAM_1: Action.FX_UNIT_1_BUTTON_1,
            FXParameter.PARAM_2: Action.FX_UNIT_1_BUTTON_2,
            FXParameter.PARAM_3: Action.FX_UNIT_1_BUTTON_3,
        }

        return [
            self._replace_action(
                event=event,
                action=mappings[self._state.fx_unit_1_parameter],
            )
        ]

    def _fx_unit_2_toggle_selected_param(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        mappings = {
            FXParameter.PARAM_1: Action.FX_UNIT_2_BUTTON_1,
            FXParameter.PARAM_2: Action.FX_UNIT_2_BUTTON_2,
            FXParameter.PARAM_3: Action.FX_UNIT_2_BUTTON_3,
        }

        return [
            self._replace_action(
                event=event,
                action=mappings[self._state.fx_unit_2_parameter],
            )
        ]

    def _select_mixer_fx_deck_a(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        self._state.select_mixer_fx_deck(
            Deck.DECK_1,
        )

        print("Mixer FX Steuerung: Deck A")
        return []

    def _select_mixer_fx_deck_b(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        self._state.select_mixer_fx_deck(
            Deck.DECK_2,
        )

        print("Mixer FX Steuerung: Deck B")
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
        adjusted_value = self._apply_deadzone(value)

        relative_value = adjusted_value * self.EQ_SPEED * delta_time

        if abs(relative_value) < 0.000001:
            return []

        if deck is Deck.DECK_1:
            band = self._state.deck_1_eq_band
            axis = Axis.LEFT_X

            mappings = {
                EQBand.HIGH: Action.DECK_1_EQ_HIGH,
                EQBand.MID_HIGH: Action.DECK_1_EQ_MID_HIGH,
                EQBand.MID_LOW: Action.DECK_1_EQ_MID_LOW,
                EQBand.LOW: Action.DECK_1_EQ_LOW,
            }

        else:
            band = self._state.deck_2_eq_band
            axis = Axis.RIGHT_X

            mappings = {
                EQBand.HIGH: Action.DECK_2_EQ_HIGH,
                EQBand.MID_HIGH: Action.DECK_2_EQ_MID_HIGH,
                EQBand.MID_LOW: Action.DECK_2_EQ_MID_LOW,
                EQBand.LOW: Action.DECK_2_EQ_LOW,
            }

        return [
            self._create_axis_action(
                action=mappings[band],
                axis=axis,
                action_value=relative_value,
                stick_value=value,
            )
        ]

    # -------------------------------------------------------------------------
    # Layer 2 – EQ-Band auswählen
    # -------------------------------------------------------------------------

    def _deck_1_eq_band_up(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        band = self._state.move_deck_1_eq_band(-1)
        print(f"Deck 1 EQ-Band: {band.label}")
        return []

    def _deck_1_eq_band_down(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        band = self._state.move_deck_1_eq_band(1)
        print(f"Deck 1 EQ-Band: {band.label}")
        return []

    def _deck_2_eq_band_up(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        band = self._state.move_deck_2_eq_band(-1)
        print(f"Deck 2 EQ-Band: {band.label}")
        return []

    def _deck_2_eq_band_down(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        band = self._state.move_deck_2_eq_band(1)
        print(f"Deck 2 EQ-Band: {band.label}")
        return []

    def _toggle_deck_1_eq_band(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        mappings = {
            EQBand.HIGH: Action.DECK_1_EQ_HIGH_TOGGLE,
            EQBand.MID_HIGH: Action.DECK_1_EQ_MID_HIGH_TOGGLE,
            EQBand.MID_LOW: Action.DECK_1_EQ_MID_LOW_TOGGLE,
            EQBand.LOW: Action.DECK_1_EQ_LOW_TOGGLE,
        }

        return [
            self._replace_action(
                event=event,
                action=mappings[self._state.deck_1_eq_band],
            )
        ]

    def _toggle_deck_2_eq_band(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        mappings = {
            EQBand.HIGH: Action.DECK_2_EQ_HIGH_TOGGLE,
            EQBand.MID_HIGH: Action.DECK_2_EQ_MID_HIGH_TOGGLE,
            EQBand.MID_LOW: Action.DECK_2_EQ_MID_LOW_TOGGLE,
            EQBand.LOW: Action.DECK_2_EQ_LOW_TOGGLE,
        }

        return [
            self._replace_action(
                event=event,
                action=mappings[self._state.deck_2_eq_band],
            )
        ]

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

    def _apply_deadzone(
        self,
        value: float,
    ) -> float:
        magnitude = abs(value)

        if magnitude < self.MIXER_DEADZONE:
            return 0.0

        normalized = (magnitude - self.MIXER_DEADZONE) / (1.0 - self.MIXER_DEADZONE)

        return normalized if value > 0 else -normalized

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
