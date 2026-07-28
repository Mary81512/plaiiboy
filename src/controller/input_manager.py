from controller.dualshock import DualShock4
from controller.event_generator import EventGenerator
from controller.touch_gesture_recognizer import (
    TouchGestureRecognizer,
)
from core.events import ControllerEvent


class InputManager:
    def __init__(self) -> None:
        self._controller = DualShock4()

        self._event_generator = EventGenerator()
        self._touch_gesture_recognizer = TouchGestureRecognizer()

    def connect(self) -> None:
        self._event_generator.reset()
        self._touch_gesture_recognizer.reset()

        self._controller.connect()

    def set_lightbar(
        self,
        red: int,
        green: int,
        blue: int,
    ) -> None:
        self._controller.set_lightbar(
            red=red,
            green=green,
            blue=blue,
        )

    def rumble_pulses(
        self,
        pulse_count: int,
    ) -> None:
        self._controller.rumble_pulses(
            pulse_count=pulse_count,
        )

    def close(self) -> None:
        self._controller.close()

        self._event_generator.reset()
        self._touch_gesture_recognizer.reset()

    def poll(self) -> list[ControllerEvent]:
        state = self._controller.poll()

        if state is None:
            return []

        events = self._event_generator.generate(state)

        touch_events = self._touch_gesture_recognizer.generate(state)

        events.extend(touch_events)

        return events

    def rumble_track_end_warning(
        self,
    ) -> None:
        self._controller.rumble_track_end_warning()
