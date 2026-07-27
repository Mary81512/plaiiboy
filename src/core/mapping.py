from core.actions import Action, ActionEvent
from core.events import Axis, Button, ControllerEvent, EventType
from core.layers import Layer

ButtonMappingKey = tuple[Button, EventType]
AxisMappingKey = tuple[Axis, EventType]


BUTTON_MAPPINGS: dict[
    Layer,
    dict[ButtonMappingKey, Action],
] = {
    Layer.DEFAULT: {
        # Deck 1
        (Button.L1, EventType.BUTTON_PRESSED): Action.DECK_1_PLAY_TOGGLE,
        (Button.L2, EventType.BUTTON_PRESSED): Action.DECK_1_CUE,
        (Button.L2, EventType.BUTTON_RELEASED): Action.DECK_1_CUE,
        (Button.SHARE, EventType.BUTTON_SHORT_PRESSED): Action.DECK_1_SYNC,
        (Button.SHARE, EventType.BUTTON_HELD): Action.DECK_1_LOAD_TRACK,
        (Button.L3, EventType.BUTTON_PRESSED): Action.DECK_1_LOOP_TOGGLE,
        # Deck 2
        (Button.R1, EventType.BUTTON_PRESSED): Action.DECK_2_PLAY_TOGGLE,
        (Button.R2, EventType.BUTTON_PRESSED): Action.DECK_2_CUE,
        (Button.R2, EventType.BUTTON_RELEASED): Action.DECK_2_CUE,
        (Button.OPTIONS, EventType.BUTTON_SHORT_PRESSED): Action.DECK_2_SYNC,
        (Button.OPTIONS, EventType.BUTTON_HELD): Action.DECK_2_LOAD_TRACK,
        (Button.R3, EventType.BUTTON_PRESSED): Action.DECK_2_LOOP_TOGGLE,
        # Browser
        (Button.DPAD_UP, EventType.BUTTON_PRESSED): Action.BROWSER_UP,
        (Button.DPAD_DOWN, EventType.BUTTON_PRESSED): Action.BROWSER_DOWN,
        (Button.DPAD_LEFT, EventType.BUTTON_PRESSED): Action.BROWSER_LEVEL_UP,
        (Button.DPAD_RIGHT, EventType.BUTTON_PRESSED): Action.BROWSER_LEVEL_DOWN,
        # Aktives Bearbeitungsdeck
        (Button.TRIANGLE, EventType.BUTTON_PRESSED): Action.TOGGLE_ACTIVE_DECK,
        # Hotcues des aktiven Decks
        (Button.SQUARE, EventType.BUTTON_PRESSED): Action.ACTIVE_DECK_HOTCUE_PREVIOUS,
        (Button.CIRCLE, EventType.BUTTON_PRESSED): Action.ACTIVE_DECK_HOTCUE_NEXT,
        (Button.CROSS, EventType.BUTTON_PRESSED): Action.ACTIVE_DECK_HOTCUE_TOGGLE,
        # Touchpad-Klick
        (Button.TOUCHPAD_CLICK, EventType.BUTTON_PRESSED): Action.CYCLE_SEEK_SPEED,
    }
}


AXIS_MAPPINGS: dict[
    Layer,
    dict[AxisMappingKey, Action],
] = {
    Layer.DEFAULT: {
        # Linker Stick: Deck 1
        (
            Axis.LEFT_X,
            EventType.AXIS_NEGATIVE_TRIGGERED,
        ): Action.DECK_1_LOOP_SIZE_DECREASE,
        (
            Axis.LEFT_X,
            EventType.AXIS_POSITIVE_TRIGGERED,
        ): Action.DECK_1_LOOP_SIZE_INCREASE,
        # Beim DualShock ist oben normalerweise ein negativer Y-Wert.
        (Axis.LEFT_Y, EventType.AXIS_NEGATIVE_TRIGGERED): Action.DECK_1_BPM_INCREASE,
        (Axis.LEFT_Y, EventType.AXIS_POSITIVE_TRIGGERED): Action.DECK_1_BPM_DECREASE,
        # Rechter Stick: Deck 2
        (
            Axis.RIGHT_X,
            EventType.AXIS_NEGATIVE_TRIGGERED,
        ): Action.DECK_2_LOOP_SIZE_DECREASE,
        (
            Axis.RIGHT_X,
            EventType.AXIS_POSITIVE_TRIGGERED,
        ): Action.DECK_2_LOOP_SIZE_INCREASE,
        (Axis.RIGHT_Y, EventType.AXIS_NEGATIVE_TRIGGERED): Action.DECK_2_BPM_INCREASE,
        (Axis.RIGHT_Y, EventType.AXIS_POSITIVE_TRIGGERED): Action.DECK_2_BPM_DECREASE,
    }
}


class ActionMapper:
    def __init__(
        self,
        button_mappings: (dict[Layer, dict[ButtonMappingKey, Action]] | None) = None,
        axis_mappings: (dict[Layer, dict[AxisMappingKey, Action]] | None) = None,
    ) -> None:
        self._button_mappings = (
            button_mappings
            if button_mappings is not None
            else self._copy_button_mappings()
        )

        self._axis_mappings = (
            axis_mappings if axis_mappings is not None else self._copy_axis_mappings()
        )

    def map_event(
        self,
        event: ControllerEvent,
        layer: Layer,
    ) -> list[ActionEvent]:
        if isinstance(event.control, Button):
            return self._map_button_event(event, layer)

        if isinstance(event.control, Axis):
            return self._map_axis_event(event, layer)

        return []

    def _map_button_event(
        self,
        event: ControllerEvent,
        layer: Layer,
    ) -> list[ActionEvent]:
        if not isinstance(event.control, Button):
            return []

        layer_mappings = self._button_mappings.get(layer, {})

        action = layer_mappings.get(
            (
                event.control,
                event.event_type,
            )
        )

        if action is None:
            return []

        return [
            ActionEvent(
                action=action,
                value=event.value,
                source_event=event,
            )
        ]

    def _map_axis_event(
        self,
        event: ControllerEvent,
        layer: Layer,
    ) -> list[ActionEvent]:
        if not isinstance(event.control, Axis):
            return []

        layer_mappings = self._axis_mappings.get(layer, {})

        action = layer_mappings.get(
            (
                event.control,
                event.event_type,
            )
        )

        if action is None:
            return []

        return [
            ActionEvent(
                action=action,
                value=event.value,
                source_event=event,
            )
        ]

    def _copy_button_mappings(
        self,
    ) -> dict[Layer, dict[ButtonMappingKey, Action]]:
        return {layer: mappings.copy() for layer, mappings in BUTTON_MAPPINGS.items()}

    def _copy_axis_mappings(
        self,
    ) -> dict[Layer, dict[AxisMappingKey, Action]]:
        return {layer: mappings.copy() for layer, mappings in AXIS_MAPPINGS.items()}
