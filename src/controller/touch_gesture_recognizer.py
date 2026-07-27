from config import (
    SWIPE_AXIS_DOMINANCE,
    SWIPE_DISTANCE_THRESHOLD,
    TOUCHPAD_MAX_X,
    TOUCHPAD_MAX_Y,
)
from controller.state import ControllerState, TouchPoint
from core.events import ControllerEvent, EventType, TouchGesture


class TouchGestureRecognizer:
    def __init__(
        self,
        swipe_distance_threshold: int = SWIPE_DISTANCE_THRESHOLD,
        swipe_axis_dominance: float = SWIPE_AXIS_DOMINANCE,
    ) -> None:
        self._swipe_distance_threshold = swipe_distance_threshold
        self._swipe_axis_dominance = swipe_axis_dominance

        self._had_touches = False

        self._tracked_touch_id: int | None = None
        self._touch_start: TouchPoint | None = None
        self._touch_latest: TouchPoint | None = None

    def generate(
        self,
        state: ControllerState,
    ) -> list[ControllerEvent]:
        has_touches = bool(state.touches)
        events: list[ControllerEvent] = []

        if not self._had_touches and has_touches:
            self._start_gesture(state)

        elif self._had_touches and has_touches:
            self._update_gesture(state)

        elif self._had_touches and not has_touches:
            event = self._finish_gesture()

            if event is not None:
                events.append(event)

        self._had_touches = has_touches

        return events

    def reset(self) -> None:
        self._had_touches = False

        self._tracked_touch_id = None
        self._touch_start = None
        self._touch_latest = None

    def _start_gesture(
        self,
        state: ControllerState,
    ) -> None:
        if not state.touches:
            return

        tracked_touch_id = min(state.touches)
        point = state.touches[tracked_touch_id]

        self._tracked_touch_id = tracked_touch_id
        self._touch_start = point
        self._touch_latest = point

    def _update_gesture(
        self,
        state: ControllerState,
    ) -> None:
        if self._tracked_touch_id is None:
            self._start_gesture(state)
            return

        point = state.touches.get(self._tracked_touch_id)

        if point is not None:
            self._touch_latest = point

    def _finish_gesture(
        self,
    ) -> ControllerEvent | None:
        start = self._touch_start
        end = self._touch_latest

        self._tracked_touch_id = None
        self._touch_start = None
        self._touch_latest = None

        if start is None or end is None:
            return None

        delta_x = end.x - start.x
        delta_y = end.y - start.y

        absolute_x = abs(delta_x)
        absolute_y = abs(delta_y)

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
                absolute_x / TOUCHPAD_MAX_X,
                1.0,
            )

            return ControllerEvent(
                event_type=EventType.TOUCHPAD_SWIPE,
                control=gesture,
                value=round(magnitude, 3),
            )

        if vertical_swipe:
            gesture = TouchGesture.SWIPE_DOWN if delta_y > 0 else TouchGesture.SWIPE_UP

            magnitude = min(
                absolute_y / TOUCHPAD_MAX_Y,
                1.0,
            )

            return ControllerEvent(
                event_type=EventType.TOUCHPAD_SWIPE,
                control=gesture,
                value=round(magnitude, 3),
            )

        return None
