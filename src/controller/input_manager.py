from controller.dualshock import DualShock4
from controller.event_generator import EventGenerator
from core.events import ControllerEvent


class InputManager:
    def __init__(self) -> None:
        self._controller = DualShock4()
        self._event_generator = EventGenerator()

    def connect(self) -> None:
        self._controller.connect()

    def close(self) -> None:
        self._controller.close()

    def poll(self) -> list[ControllerEvent]:
        state = self._controller.poll()

        if state is None:
            return []

        return self._event_generator.generate(state)
