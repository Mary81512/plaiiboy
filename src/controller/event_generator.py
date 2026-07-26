import time

from controller.state import ControllerState
from core.events import Button, ControllerEvent, EventType


class EventGenerator:
    def __init__(self, hold_threshold: float = 0.5) -> None:
        self._previous_state: ControllerState | None = None
        self._hold_threshold = hold_threshold
        self._pressed_at: dict[Button, float] = {}
        self._held_buttons: set[Button] = set()

    def generate(
        self,
        state: ControllerState,
    ) -> list[ControllerEvent]:
        now = time.monotonic()

        if self._previous_state is None:
            self._previous_state = state

            for button in state.buttons:
                self._pressed_at[button] = now

            return []

        events: list[ControllerEvent] = []
        previous = self._previous_state

        pressed = state.buttons - previous.buttons
        released = previous.buttons - state.buttons

        for button in sorted(pressed, key=lambda item: item.value):
            self._pressed_at[button] = now
            self._held_buttons.discard(button)

            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_PRESSED,
                    control=button,
                    value=1.0,
                )
            )

        for button in sorted(released, key=lambda item: item.value):
            self._pressed_at.pop(button, None)
            self._held_buttons.discard(button)

            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_RELEASED,
                    control=button,
                    value=0.0,
                )
            )

        for button in sorted(state.buttons, key=lambda item: item.value):
            pressed_at = self._pressed_at.get(button)

            if pressed_at is None:
                self._pressed_at[button] = now
                continue

            if button in self._held_buttons:
                continue

            held_duration = now - pressed_at

            if held_duration < self._hold_threshold:
                continue

            self._held_buttons.add(button)

            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_HELD,
                    control=button,
                    value=held_duration,
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
