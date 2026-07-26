from controller.dualshock import DualShock4
from core.events import ControllerEvent


class InputManager:
    def __init__(self) -> None:
        self._controller = DualShock4()

    def connect(self) -> None:
        self._controller.connect()

    def close(self) -> None:
        self._controller.close()

    def poll(self) -> list[ControllerEvent]:
        return self._controller.poll()
