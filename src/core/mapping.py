from core.actions import Action, ActionEvent
from core.events import Button, ControllerEvent, EventType
from core.layers import Layer

TEST_MAPPINGS: dict[Layer, dict[Button, Action]] = {
    Layer.DEFAULT: {
        Button.CROSS: Action.PLAY_PAUSE,
        Button.CIRCLE: Action.CUE,
        Button.SQUARE: Action.SYNC,
        Button.TRIANGLE: Action.LOAD_TRACK,
    }
}


class ActionMapper:
    def __init__(
        self,
        mappings: dict[Layer, dict[Button, Action]] | None = None,
    ) -> None:
        self._mappings = (
            mappings if mappings is not None else self._copy_test_mappings()
        )

    def map_event(
        self,
        event: ControllerEvent,
        layer: Layer,
    ) -> list[ActionEvent]:
        if event.event_type is not EventType.BUTTON_PRESSED:
            return []

        if not isinstance(event.control, Button):
            return []

        layer_mappings = self._mappings.get(layer)

        if layer_mappings is None:
            return []

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

    def _copy_test_mappings(self) -> dict[Layer, dict[Button, Action]]:
        return {
            layer: layer_mappings.copy()
            for layer, layer_mappings in TEST_MAPPINGS.items()
        }
