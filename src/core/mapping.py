from core.actions import Action, ActionEvent
from core.events import (
    Axis,
    Button,
    ControllerEvent,
    EventType,
    TouchGesture,
)
from core.layers import Layer

MappingControl = Button | Axis | TouchGesture
MappingKey = tuple[MappingControl, EventType]


CONTROLLER_MAPPINGS: dict[
    Layer,
    dict[MappingKey, Action],
] = {
    Layer.LAYER_1: {
        # Deck 1
        (
            Button.L1,
            EventType.BUTTON_PRESSED,
        ): Action.DECK_1_PLAY_TOGGLE,
        (
            Button.L2,
            EventType.BUTTON_PRESSED,
        ): Action.DECK_1_CUE,
        (
            Button.L2,
            EventType.BUTTON_RELEASED,
        ): Action.DECK_1_CUE,
        (
            Button.SHARE,
            EventType.BUTTON_SHORT_PRESSED,
        ): Action.DECK_1_SYNC,
        (
            Button.SHARE,
            EventType.BUTTON_HELD,
        ): Action.DECK_1_LOAD_TRACK,
        (
            Button.L3,
            EventType.BUTTON_PRESSED,
        ): Action.DECK_1_LOOP_TOGGLE,
        # Deck 2
        (
            Button.R1,
            EventType.BUTTON_PRESSED,
        ): Action.DECK_2_PLAY_TOGGLE,
        (
            Button.R2,
            EventType.BUTTON_PRESSED,
        ): Action.DECK_2_CUE,
        (
            Button.R2,
            EventType.BUTTON_RELEASED,
        ): Action.DECK_2_CUE,
        (
            Button.OPTIONS,
            EventType.BUTTON_SHORT_PRESSED,
        ): Action.DECK_2_SYNC,
        (
            Button.OPTIONS,
            EventType.BUTTON_HELD,
        ): Action.DECK_2_LOAD_TRACK,
        (
            Button.R3,
            EventType.BUTTON_PRESSED,
        ): Action.DECK_2_LOOP_TOGGLE,
        # Browser
        (
            Button.DPAD_UP,
            EventType.BUTTON_PRESSED,
        ): Action.BROWSER_UP,
        (
            Button.DPAD_DOWN,
            EventType.BUTTON_PRESSED,
        ): Action.BROWSER_DOWN,
        (
            Button.DPAD_LEFT,
            EventType.BUTTON_PRESSED,
        ): Action.BROWSER_LEVEL_UP,
        (
            Button.DPAD_RIGHT,
            EventType.BUTTON_PRESSED,
        ): Action.BROWSER_LEVEL_DOWN,
        # Aktives Bearbeitungsdeck
        (
            Button.TRIANGLE,
            EventType.BUTTON_PRESSED,
        ): Action.TOGGLE_ACTIVE_DECK,
        # Hotcues
        (
            Button.SQUARE,
            EventType.BUTTON_PRESSED,
        ): Action.ACTIVE_DECK_HOTCUE_PREVIOUS,
        (
            Button.CIRCLE,
            EventType.BUTTON_PRESSED,
        ): Action.ACTIVE_DECK_HOTCUE_NEXT,
        (
            Button.CROSS,
            EventType.BUTTON_PRESSED,
        ): Action.ACTIVE_DECK_HOTCUE_TOGGLE,
        # Touchpad
        (
            Button.TOUCHPAD_CLICK,
            EventType.BUTTON_PRESSED,
        ): Action.CYCLE_SEEK_SPEED,
        (
            TouchGesture.SWIPE_LEFT,
            EventType.TOUCHPAD_SWIPE,
        ): Action.ACTIVE_DECK_SEEK_BACKWARD,
        (
            TouchGesture.SWIPE_RIGHT,
            EventType.TOUCHPAD_SWIPE,
        ): Action.ACTIVE_DECK_SEEK_FORWARD,
        # Linker Stick
        (
            Axis.LEFT_X,
            EventType.AXIS_NEGATIVE_TRIGGERED,
        ): Action.DECK_1_LOOP_SIZE_DECREASE,
        (
            Axis.LEFT_X,
            EventType.AXIS_POSITIVE_TRIGGERED,
        ): Action.DECK_1_LOOP_SIZE_INCREASE,
        (
            Axis.LEFT_Y,
            EventType.AXIS_NEGATIVE_TRIGGERED,
        ): Action.DECK_1_BPM_INCREASE,
        (
            Axis.LEFT_Y,
            EventType.AXIS_POSITIVE_TRIGGERED,
        ): Action.DECK_1_BPM_DECREASE,
        # Rechter Stick
        (
            Axis.RIGHT_X,
            EventType.AXIS_NEGATIVE_TRIGGERED,
        ): Action.DECK_2_LOOP_SIZE_DECREASE,
        (
            Axis.RIGHT_X,
            EventType.AXIS_POSITIVE_TRIGGERED,
        ): Action.DECK_2_LOOP_SIZE_INCREASE,
        (
            Axis.RIGHT_Y,
            EventType.AXIS_NEGATIVE_TRIGGERED,
        ): Action.DECK_2_BPM_INCREASE,
        (
            Axis.RIGHT_Y,
            EventType.AXIS_POSITIVE_TRIGGERED,
        ): Action.DECK_2_BPM_DECREASE,
    },
    Layer.LAYER_2: {
        (
            Button.L3,
            EventType.BUTTON_PRESSED,
        ): Action.CYCLE_DECK_1_EQ_BAND,
        (
            Button.R3,
            EventType.BUTTON_PRESSED,
        ): Action.CYCLE_DECK_2_EQ_BAND,
    },
}


class ActionMapper:
    def __init__(
        self,
        mappings: (dict[Layer, dict[MappingKey, Action]] | None) = None,
    ) -> None:
        self._mappings = (
            {layer: layer_mappings.copy() for layer, layer_mappings in mappings.items()}
            if mappings is not None
            else self._copy_default_mappings()
        )

    def map_event(
        self,
        event: ControllerEvent,
        layer: Layer,
    ) -> list[ActionEvent]:
        layer_mappings = self._mappings.get(
            layer,
            {},
        )

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

    def _copy_default_mappings(
        self,
    ) -> dict[Layer, dict[MappingKey, Action]]:
        return {
            layer: mappings.copy() for layer, mappings in CONTROLLER_MAPPINGS.items()
        }
