from core.actions import Action, ActionEvent
from core.events import Axis, Button, ControllerEvent, EventType
from core.layers import Layer

ButtonMappingKey = tuple[Button, EventType]


TEST_BUTTON_MAPPINGS: dict[
    Layer,
    dict[ButtonMappingKey, Action],
] = {
    Layer.DEFAULT: {
        (Button.CROSS, EventType.BUTTON_PRESSED): Action.PLAY_PAUSE,
        (Button.CROSS, EventType.BUTTON_RELEASED): Action.PLAY_PAUSE,
        (Button.CIRCLE, EventType.BUTTON_PRESSED): Action.CUE,
        (Button.CIRCLE, EventType.BUTTON_RELEASED): Action.CUE,
        (Button.SQUARE, EventType.BUTTON_PRESSED): Action.SYNC,
        (Button.SQUARE, EventType.BUTTON_RELEASED): Action.SYNC,
        (Button.TRIANGLE, EventType.BUTTON_PRESSED): Action.LOAD_TRACK,
        (Button.TRIANGLE, EventType.BUTTON_RELEASED): Action.LOAD_TRACK,
    }
}


TEST_AXIS_MAPPINGS: dict[Layer, dict[Axis, Action]] = {
    Layer.DEFAULT: {
        Axis.LEFT_X: Action.LEFT_STICK_X,
        Axis.LEFT_Y: Action.LEFT_STICK_Y,
        Axis.L2: Action.LEFT_TRIGGER,
        Axis.R2: Action.RIGHT_TRIGGER,
    }
}


class ActionMapper:
    def __init__(
        self,
        button_mappings: (dict[Layer, dict[ButtonMappingKey, Action]] | None) = None,
        axis_mappings: dict[Layer, dict[Axis, Action]] | None = None,
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
        if event.event_type not in {
            EventType.BUTTON_PRESSED,
            EventType.BUTTON_RELEASED,
            EventType.BUTTON_HELD,
            EventType.BUTTON_DOUBLE_PRESSED,
        }:
            return []

        if not isinstance(event.control, Button):
            return []

        layer_mappings = self._button_mappings.get(layer, {})

        mapping_key = (
            event.control,
            event.event_type,
        )

        action = layer_mappings.get(mapping_key)

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
        if event.event_type is not EventType.AXIS_CHANGED:
            return []

        if not isinstance(event.control, Axis):
            return []

        layer_mappings = self._axis_mappings.get(layer, {})
        action = layer_mappings.get(event.control)

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
        return {
            layer: mappings.copy() for layer, mappings in TEST_BUTTON_MAPPINGS.items()
        }

    def _copy_axis_mappings(
        self,
    ) -> dict[Layer, dict[Axis, Action]]:
        return {
            layer: mappings.copy() for layer, mappings in TEST_AXIS_MAPPINGS.items()
        }
