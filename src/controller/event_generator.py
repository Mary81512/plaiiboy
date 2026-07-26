import time

from controller.state import ControllerState
from core.events import Button, ControllerEvent, EventType


class EventGenerator:
    def __init__(
        self,
        hold_threshold: float = 0.5,
        double_press_threshold: float = 0.3,
    ) -> None:
        self._previous_state: ControllerState | None = None

        self._hold_threshold = hold_threshold
        self._double_press_threshold = double_press_threshold

        self._pressed_at: dict[Button, float] = {}
        self._last_press: dict[Button, float] = {}

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
                self._last_press[button] = now

            return []

        events: list[ControllerEvent] = []

        previous = self._previous_state

        pressed = state.buttons - previous.buttons
        released = previous.buttons - state.buttons

        for button in sorted(pressed, key=lambda b: b.value):
            previous_press = self._last_press.get(button)

            if (
                previous_press is not None
                and now - previous_press <= self._double_press_threshold
            ):
                events.append(
                    ControllerEvent(
                        event_type=EventType.BUTTON_DOUBLE_PRESSED,
                        control=button,
                        value=1.0,
                    )
                )

            self._last_press[button] = now
            self._pressed_at[button] = now
            self._held_buttons.discard(button)

            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_PRESSED,
                    control=button,
                    value=1.0,
                )
            )

        for button in sorted(released, key=lambda b: b.value):
            self._pressed_at.pop(button, None)
            self._held_buttons.discard(button)

            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_RELEASED,
                    control=button,
                    value=0.0,
                )
            )

        for button in sorted(state.buttons, key=lambda b: b.value):
            pressed_at = self._pressed_at.get(button)

            if pressed_at is None:
                continue

            if button in self._held_buttons:
                continue

            duration = now - pressed_at

            if duration < self._hold_threshold:
                continue

            self._held_buttons.add(button)

            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_HELD,
                    control=button,
                    value=duration,
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
