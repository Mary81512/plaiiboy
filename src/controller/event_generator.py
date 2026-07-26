from controller.state import ControllerState
from core.events import ControllerEvent, EventType


class EventGenerator:
    def __init__(self) -> None:
        self._previous_state: ControllerState | None = None

    def generate(
        self,
        state: ControllerState,
    ) -> list[ControllerEvent]:

        if self._previous_state is None:
            self._previous_state = state
            return []

        events: list[ControllerEvent] = []

        previous = self._previous_state

        pressed = state.buttons - previous.buttons
        released = previous.buttons - state.buttons

        for button in sorted(pressed, key=lambda item: item.value):
            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_PRESSED,
                    control=button,
                    value=1.0,
                )
            )

        for button in sorted(released, key=lambda item: item.value):
            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_RELEASED,
                    control=button,
                    value=0.0,
                )
            )

        for axis, value in state.axes.items():
            previous_value = previous.axes.get(axis)

            if previous_value is None:
                continue

            if abs(value - previous_value) < 0.05:
                continue

            events.append(
                ControllerEvent(
                    event_type=EventType.AXIS_CHANGED,
                    control=axis,
                    value=value,
                )
            )

        self._previous_state = state

        return events
