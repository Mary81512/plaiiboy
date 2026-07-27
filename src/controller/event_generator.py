import time

from controller.state import ControllerState, TouchPoint
from core.events import (
    Axis,
    Button,
    ControllerEvent,
    EventType,
    TouchGesture,
)


class EventGenerator:
    def __init__(
        self,
        hold_threshold: float = 0.5,
        double_press_threshold: float = 0.3,
        axis_trigger_threshold: float = 0.9,
        axis_release_threshold: float = 0.4,
        swipe_distance_threshold: int = 180,
        swipe_axis_dominance: float = 1.25,
    ) -> None:
        self._previous_state: ControllerState | None = None

        self._hold_threshold = hold_threshold
        self._double_press_threshold = double_press_threshold

        self._axis_trigger_threshold = axis_trigger_threshold
        self._axis_release_threshold = axis_release_threshold

        self._swipe_distance_threshold = swipe_distance_threshold
        self._swipe_axis_dominance = swipe_axis_dominance

        self._pressed_at: dict[Button, float] = {}
        self._last_press: dict[Button, float] = {}
        self._held_buttons: set[Button] = set()

        self._axis_latches: dict[Axis, int] = {}

        self._tracked_touch_id: int | None = None
        self._touch_start: TouchPoint | None = None
        self._touch_latest: TouchPoint | None = None

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

            for axis in state.axes:
                self._axis_latches[axis] = 0

            self._initialize_touch_tracking(state)

            return []

        events: list[ControllerEvent] = []

        previous = self._previous_state

        pressed = state.buttons - previous.buttons
        released = previous.buttons - state.buttons

        self._generate_pressed_events(
            pressed=pressed,
            now=now,
            events=events,
        )

        self._generate_released_events(
            released=released,
            now=now,
            events=events,
        )

        self._generate_held_events(
            buttons=state.buttons,
            now=now,
            events=events,
        )

        self._generate_axis_events(
            state=state,
            previous=previous,
            events=events,
        )

        self._generate_touch_events(
            state=state,
            previous=previous,
            events=events,
        )

        self._previous_state = state

        return events

    def _generate_pressed_events(
        self,
        pressed: frozenset[Button],
        now: float,
        events: list[ControllerEvent],
    ) -> None:
        for button in sorted(
            pressed,
            key=lambda item: item.value,
        ):
            previous_press = self._last_press.get(button)

            if (
                previous_press is not None
                and now - previous_press <= self._double_press_threshold
            ):
                events.append(
                    ControllerEvent(
                        event_type=(EventType.BUTTON_DOUBLE_PRESSED),
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

    def _generate_released_events(
        self,
        released: frozenset[Button],
        now: float,
        events: list[ControllerEvent],
    ) -> None:
        for button in sorted(
            released,
            key=lambda item: item.value,
        ):
            pressed_at = self._pressed_at.pop(
                button,
                None,
            )

            was_held = button in self._held_buttons

            self._held_buttons.discard(button)

            if pressed_at is not None and not was_held:
                duration = now - pressed_at

                events.append(
                    ControllerEvent(
                        event_type=(EventType.BUTTON_SHORT_PRESSED),
                        control=button,
                        value=duration,
                    )
                )

            events.append(
                ControllerEvent(
                    event_type=EventType.BUTTON_RELEASED,
                    control=button,
                    value=0.0,
                )
            )

    def _generate_held_events(
        self,
        buttons: frozenset[Button],
        now: float,
        events: list[ControllerEvent],
    ) -> None:
        for button in sorted(
            buttons,
            key=lambda item: item.value,
        ):
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

    def _generate_axis_events(
        self,
        state: ControllerState,
        previous: ControllerState,
        events: list[ControllerEvent],
    ) -> None:
        for axis, value in state.axes.items():
            previous_value = previous.axes.get(axis)

            if previous_value is not None and abs(value - previous_value) >= 0.05:
                events.append(
                    ControllerEvent(
                        event_type=EventType.AXIS_CHANGED,
                        control=axis,
                        value=value,
                    )
                )

            self._generate_axis_threshold_event(
                axis=axis,
                value=value,
                events=events,
            )

    def _generate_axis_threshold_event(
        self,
        axis: Axis,
        value: float,
        events: list[ControllerEvent],
    ) -> None:
        latch = self._axis_latches.get(axis, 0)

        if abs(value) <= self._axis_release_threshold:
            self._axis_latches[axis] = 0
            return

        if latch != 0:
            return

        if value <= -self._axis_trigger_threshold:
            self._axis_latches[axis] = -1

            events.append(
                ControllerEvent(
                    event_type=(EventType.AXIS_NEGATIVE_TRIGGERED),
                    control=axis,
                    value=-1.0,
                )
            )

            return

        if value >= self._axis_trigger_threshold:
            self._axis_latches[axis] = 1

            events.append(
                ControllerEvent(
                    event_type=(EventType.AXIS_POSITIVE_TRIGGERED),
                    control=axis,
                    value=1.0,
                )
            )

    def _initialize_touch_tracking(
        self,
        state: ControllerState,
    ) -> None:
        if not state.touches:
            return

        tracked_id = min(state.touches)
        point = state.touches[tracked_id]

        self._tracked_touch_id = tracked_id
        self._touch_start = point
        self._touch_latest = point

    def _generate_touch_events(
        self,
        state: ControllerState,
        previous: ControllerState,
        events: list[ControllerEvent],
    ) -> None:
        had_touches = bool(previous.touches)
        has_touches = bool(state.touches)

        if not had_touches and has_touches:
            self._initialize_touch_tracking(state)
            return

        if has_touches:
            self._update_tracked_touch(state)
            return

        if had_touches and not has_touches:
            self._finish_touch_gesture(events)

    def _update_tracked_touch(
        self,
        state: ControllerState,
    ) -> None:
        if self._tracked_touch_id is None:
            self._initialize_touch_tracking(state)
            return

        point = state.touches.get(self._tracked_touch_id)

        if point is not None:
            self._touch_latest = point

    def _finish_touch_gesture(
        self,
        events: list[ControllerEvent],
    ) -> None:
        start = self._touch_start
        end = self._touch_latest

        self._tracked_touch_id = None
        self._touch_start = None
        self._touch_latest = None

        if start is None or end is None:
            return

        delta_x = end.x - start.x
        delta_y = end.y - start.y

        absolute_x = abs(delta_x)
        absolute_y = abs(delta_y)

        gesture: TouchGesture | None = None
        magnitude = 0.0

        horizontal_swipe = (
            absolute_x >= self._swipe_distance_threshold
            and absolute_x >= absolute_y * self._swipe_axis_dominance
        )

        vertical_swipe = (
            absolute_y >= self._swipe_distance_threshold
            and absolute_y >= absolute_x * self._swipe_axis_dominance
        )

        if horizontal_swipe:
            gesture = (
                TouchGesture.SWIPE_RIGHT if delta_x > 0 else TouchGesture.SWIPE_LEFT
            )

            magnitude = min(
                absolute_x / 1919,
                1.0,
            )

        elif vertical_swipe:
            gesture = TouchGesture.SWIPE_DOWN if delta_y > 0 else TouchGesture.SWIPE_UP

            magnitude = min(
                absolute_y / 941,
                1.0,
            )

        if gesture is None:
            return

        events.append(
            ControllerEvent(
                event_type=EventType.TOUCHPAD_SWIPE,
                control=gesture,
                value=round(magnitude, 3),
            )
        )
