import time
from dataclasses import dataclass

import hid


SONY_VENDOR_ID = 0x054C
DUALSHOCK_4_PRODUCT_ID = 0x05C4

STICK_CENTER = 128
STICK_DEADZONE = 15


@dataclass(frozen=True)
class ControllerEvent:
    event_type: str
    control: str
    value: int | float | None = None


class DualShock4:
    def __init__(self) -> None:
        self._device: hid.device | None = None
        self._previous_buttons: set[str] = set()
        self._previous_axes: dict[str, float] = {}

    @property
    def connected(self) -> bool:
        return self._device is not None

  def connect(self, timeout: float = 10.0) -> None:
    print("Suche DualShock 4 ...")

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        devices = hid.enumerate(
            SONY_VENDOR_ID,
            DUALSHOCK_4_PRODUCT_ID,
        )

        if devices:
            device = hid.device()
            device.open_path(devices[0]["path"])
            device.set_nonblocking(True)

            self._device = device
            return

        time.sleep(0.5)

    raise RuntimeError(
        "DualShock 4 wurde innerhalb von 10 Sekunden nicht gefunden. "
        "Bitte PS-Taste drücken oder Bluetooth neu verbinden."
    )

    def close(self) -> None:
        if self._device is not None:
            self._device.close()
            self._device = None

    def poll(self) -> list[ControllerEvent]:
        if self._device is None:
            raise RuntimeError("Controller ist nicht verbunden.")

        try:
            report = self._device.read(78)
        except OSError as error:
            self.close()
            raise RuntimeError(
                "Verbindung zum Controller wurde unterbrochen."
            ) from error

        if not report:
            time.sleep(0.005)
            return []

        if len(report) < 10 or report[0] != 0x01:
            return []

        events: list[ControllerEvent] = []

        current_buttons = self._decode_buttons(report)
        events.extend(self._create_button_events(current_buttons))

        current_axes = self._decode_axes(report)
        events.extend(self._create_axis_events(current_axes))

        return events

    def _decode_buttons(self, report: list[int]) -> set[str]:
        buttons: set[str] = set()

        buttons_1 = report[5]
        buttons_2 = report[6]
        buttons_3 = report[7]

        dpad_value = buttons_1 & 0x0F
        face_bits = buttons_1 & 0xF0

        dpad_directions = {
            0: "DPAD_UP",
            1: "DPAD_UP_RIGHT",
            2: "DPAD_RIGHT",
            3: "DPAD_DOWN_RIGHT",
            4: "DPAD_DOWN",
            5: "DPAD_DOWN_LEFT",
            6: "DPAD_LEFT",
            7: "DPAD_UP_LEFT",
        }

        if dpad_value in dpad_directions:
            buttons.add(dpad_directions[dpad_value])

        face_buttons = {
            0x10: "SQUARE",
            0x20: "CROSS",
            0x40: "CIRCLE",
            0x80: "TRIANGLE",
        }

        for bit, name in face_buttons.items():
            if face_bits & bit:
                buttons.add(name)

        secondary_buttons = {
            0x01: "L1",
            0x02: "R1",
            0x04: "L2_BUTTON",
            0x08: "R2_BUTTON",
            0x10: "SHARE",
            0x20: "OPTIONS",
            0x40: "L3",
            0x80: "R3",
        }

        for bit, name in secondary_buttons.items():
            if buttons_2 & bit:
                buttons.add(name)

        if buttons_3 & 0x01:
            buttons.add("PS")

        if buttons_3 & 0x02:
            buttons.add("TOUCHPAD_CLICK")

        return buttons

    def _decode_axes(self, report: list[int]) -> dict[str, float]:
        return {
            "LEFT_X": self._normalize_stick(report[1]),
            "LEFT_Y": self._normalize_stick(report[2]),
            "RIGHT_X": self._normalize_stick(report[3]),
            "RIGHT_Y": self._normalize_stick(report[4]),
            "L2": report[8] / 255,
            "R2": report[9] / 255,
        }

    def _normalize_stick(self, raw_value: int) -> float:
        difference = raw_value - STICK_CENTER

        if abs(difference) <= STICK_DEADZONE:
            return 0.0

        if difference < 0:
            return round(difference / STICK_CENTER, 3)

        return round(difference / 127, 3)

    def _create_button_events(
        self,
        current_buttons: set[str],
    ) -> list[ControllerEvent]:
        events: list[ControllerEvent] = []

        pressed = current_buttons - self._previous_buttons
        released = self._previous_buttons - current_buttons

        for button in sorted(pressed):
            events.append(
                ControllerEvent(
                    event_type="button_pressed",
                    control=button,
                    value=1,
                )
            )

        for button in sorted(released):
            events.append(
                ControllerEvent(
                    event_type="button_released",
                    control=button,
                    value=0,
                )
            )

        self._previous_buttons = current_buttons

        return events

    def _create_axis_events(
        self,
        current_axes: dict[str, float],
    ) -> list[ControllerEvent]:
        events: list[ControllerEvent] = []

        for axis_name, value in current_axes.items():
            previous_value = self._previous_axes.get(axis_name)

            if previous_value is None:
                self._previous_axes[axis_name] = value
                continue

            if abs(value - previous_value) < 0.05:
                continue

            events.append(
                ControllerEvent(
                    event_type="axis_changed",
                    control=axis_name,
                    value=value,
                )
            )

            self._previous_axes[axis_name] = value

        return events