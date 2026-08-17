import time
import zlib

import hid

from controller.state import ControllerState, MotionState, TouchPoint
from controller_config import (
    BLUETOOTH_HARDWARE_CONTROL,
    BLUETOOTH_INPUT_REPORT_ID,
    BLUETOOTH_OUTPUT_CRC_SEED,
    BLUETOOTH_OUTPUT_REPORT_ID,
    BLUETOOTH_REPORT_SIZE,
    DUALSHOCK_4_PRODUCT_ID,
    SONY_VENDOR_ID,
    STICK_CENTER,
    STICK_DEADZONE,
    STICK_NEGATIVE_RANGE,
    STICK_POSITIVE_RANGE,
)
from core.events import Axis, Button


class ControllerConnectionError(RuntimeError):
    """Der Controller wurde während des Betriebs getrennt."""


class DualShock4:
    KEEP_ALIVE_INTERVAL = 30.0

    def __init__(self) -> None:
        self._device: hid.device | None = None

        self._lightbar_red = 0
        self._lightbar_green = 0
        self._lightbar_blue = 0

        self._small_motor = 0
        self._large_motor = 0

        self._last_output_report_at = 0.0

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
                self._enable_full_bluetooth_reports()

                print("DualShock 4 verbunden.")
                print("Bluetooth-Vollmodus aktiviert.")

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

    def poll(self) -> ControllerState | None:
        if self._device is None:
            raise RuntimeError("Controller ist nicht verbunden.")

        self._send_keep_alive_if_needed()

        try:
            report = self._device.read(BLUETOOTH_REPORT_SIZE)
        except OSError as error:
            self.close()

            raise ControllerConnectionError(
                "Verbindung zum Controller wurde unterbrochen."
            ) from error

        if not report:
            time.sleep(0.005)
            return None

        if (
            len(report) == BLUETOOTH_REPORT_SIZE
            and report[0] == BLUETOOTH_INPUT_REPORT_ID
        ):
            return self._decode_bluetooth_state(report)

        # Der Controller kann während des Umschaltens noch kurz einen
        # 10-Byte-Minimalreport liefern.
        if len(report) >= 10 and report[0] == 0x01:
            return self._decode_minimal_state(report)

        return None

    def _send_keep_alive_if_needed(self) -> None:
        now = time.monotonic()

        if now - self._last_output_report_at < self.KEEP_ALIVE_INTERVAL:
            return

        self._write_output_report()

    def _enable_full_bluetooth_reports(self) -> None:
        self._write_output_report()

    def set_lightbar(
        self,
        red: int,
        green: int,
        blue: int,
    ) -> None:
        self._lightbar_red = self._clamp_byte(red)
        self._lightbar_green = self._clamp_byte(green)
        self._lightbar_blue = self._clamp_byte(blue)

        self._write_output_report()

    def set_rumble(
        self,
        small_motor: int,
        large_motor: int,
    ) -> None:
        self._small_motor = self._clamp_byte(small_motor)
        self._large_motor = self._clamp_byte(large_motor)

        self._write_output_report()

    def rumble_pulses(
        self,
        pulse_count: int,
        delay: float = 0.12,
        duration: float = 0.10,
        strength: int = 285,
    ) -> None:
        if pulse_count <= 0:
            return

        time.sleep(delay)

        for pulse_index in range(pulse_count):
            self.set_rumble(
                small_motor=strength,
                large_motor=0,
            )

            time.sleep(duration)

            self.set_rumble(
                small_motor=0,
                large_motor=0,
            )

            if pulse_index < pulse_count - 1:
                time.sleep(delay)

    def rumble_track_end_warning(self) -> None:
        wave_count = 2

        for wave_index in range(wave_count):
            for pulse_index in range(2):
                self.set_rumble(
                    small_motor=255,
                    large_motor=80,
                )

                time.sleep(0.16)

                self.set_rumble(
                    small_motor=0,
                    large_motor=0,
                )

                if pulse_index < 1:
                    time.sleep(0.18)

            if wave_index < wave_count - 1:
                time.sleep(0.35)

    def _write_output_report(self) -> None:
        if self._device is None:
            raise RuntimeError("Controller ist nicht verbunden.")

        report = bytearray(BLUETOOTH_REPORT_SIZE)

        # Bluetooth-Ausgabebericht.
        report[0] = BLUETOOTH_OUTPUT_REPORT_ID
        report[1] = BLUETOOTH_HARDWARE_CONTROL
        report[2] = 0x00

        # Sowohl Motor- als auch LED-Daten sind gültig.
        report[3] = 0x03
        report[4] = 0x00
        report[5] = 0x00

        # Vibrationsmotoren.
        report[6] = self._small_motor
        report[7] = self._large_motor

        # Lichtleiste.
        report[8] = self._lightbar_red
        report[9] = self._lightbar_green
        report[10] = self._lightbar_blue

        crc_data = bytes([BLUETOOTH_OUTPUT_CRC_SEED]) + bytes(report[:-4])
        crc = zlib.crc32(crc_data) & 0xFFFFFFFF

        report[-4:] = crc.to_bytes(
            length=4,
            byteorder="little",
        )

        try:
            written = self._device.write(list(report))
        except OSError as error:
            self.close()

            raise ControllerConnectionError(
                "Der Bluetooth-Output-Report konnte nicht gesendet werden."
            ) from error

        if written <= 0:
            self.close()

            raise ControllerConnectionError(
                "Der Controller hat den Bluetooth-Output-Report nicht angenommen."
            )
        self._last_output_report_at = time.monotonic()

    def _clamp_byte(
        self,
        value: int,
    ) -> int:
        return max(
            0,
            min(
                255,
                int(value),
            ),
        )

    def _decode_bluetooth_state(
        self,
        report: list[int],
    ) -> ControllerState:
        # Im Bluetooth-Report beginnen die gemeinsamen Controllerdaten
        # nach Report-ID und Bluetooth-Header bei Byte 3.
        data_offset = 2

        return ControllerState(
            buttons=frozenset(
                self._decode_buttons(
                    report=report,
                    data_offset=data_offset,
                )
            ),
            axes=self._decode_axes(
                report=report,
                data_offset=data_offset,
            ),
            touches=self._decode_touches(report),
            motion=self._decode_motion(
                report=report,
                data_offset=data_offset,
            ),
        )

    def _decode_minimal_state(
        self,
        report: list[int],
    ) -> ControllerState:
        return ControllerState(
            buttons=frozenset(
                self._decode_buttons(
                    report=report,
                    data_offset=0,
                )
            ),
            axes=self._decode_axes(
                report=report,
                data_offset=0,
            ),
            touches={},
        )

    def _decode_buttons(
        self,
        report: list[int],
        data_offset: int,
    ) -> set[Button]:
        buttons: set[Button] = set()

        buttons_1 = report[5 + data_offset]
        buttons_2 = report[6 + data_offset]
        buttons_3 = report[7 + data_offset]

        dpad_value = buttons_1 & 0x0F
        face_bits = buttons_1 & 0xF0

        dpad_directions = {
            0: Button.DPAD_UP,
            1: Button.DPAD_UP_RIGHT,
            2: Button.DPAD_RIGHT,
            3: Button.DPAD_DOWN_RIGHT,
            4: Button.DPAD_DOWN,
            5: Button.DPAD_DOWN_LEFT,
            6: Button.DPAD_LEFT,
            7: Button.DPAD_UP_LEFT,
        }

        dpad_button = dpad_directions.get(dpad_value)

        if dpad_button is not None:
            buttons.add(dpad_button)

        face_buttons = {
            0x10: Button.SQUARE,
            0x20: Button.CROSS,
            0x40: Button.CIRCLE,
            0x80: Button.TRIANGLE,
        }

        for bit, button in face_buttons.items():
            if face_bits & bit:
                buttons.add(button)

        secondary_buttons = {
            0x01: Button.L1,
            0x02: Button.R1,
            0x04: Button.L2,
            0x08: Button.R2,
            0x10: Button.SHARE,
            0x20: Button.OPTIONS,
            0x40: Button.L3,
            0x80: Button.R3,
        }

        for bit, button in secondary_buttons.items():
            if buttons_2 & bit:
                buttons.add(button)

        if buttons_3 & 0x01:
            buttons.add(Button.PS)

        if buttons_3 & 0x02:
            buttons.add(Button.TOUCHPAD_CLICK)

        return buttons

    def _decode_axes(
        self,
        report: list[int],
        data_offset: int,
    ) -> dict[Axis, float]:
        return {
            Axis.LEFT_X: self._normalize_stick(report[1 + data_offset]),
            Axis.LEFT_Y: self._normalize_stick(report[2 + data_offset]),
            Axis.RIGHT_X: self._normalize_stick(report[3 + data_offset]),
            Axis.RIGHT_Y: self._normalize_stick(report[4 + data_offset]),
            Axis.L2: round(
                report[8 + data_offset] / 255,
                3,
            ),
            Axis.R2: round(
                report[9 + data_offset] / 255,
                3,
            ),
        }

    def _decode_motion(
        self,
        report: list[int],
        data_offset: int,
    ) -> MotionState:
        return MotionState(
            gyro_x=self._decode_signed_16(
                report,
                13 + data_offset,
            ),
            gyro_y=self._decode_signed_16(
                report,
                15 + data_offset,
            ),
            gyro_z=self._decode_signed_16(
                report,
                17 + data_offset,
            ),
            accel_x=self._decode_signed_16(
                report,
                19 + data_offset,
            ),
            accel_y=self._decode_signed_16(
                report,
                21 + data_offset,
            ),
            accel_z=self._decode_signed_16(
                report,
                23 + data_offset,
            ),
        )

    def _decode_signed_16(
        self,
        report: list[int],
        index: int,
    ) -> int:
        return int.from_bytes(
            bytes(report[index : index + 2]),
            byteorder="little",
            signed=True,
        )

    def _decode_touches(
        self,
        report: list[int],
    ) -> dict[int, TouchPoint]:
        touch_report_count = min(report[35], 4)

        if touch_report_count == 0:
            return {}

        # Ein Bluetooth-Report kann mehrere ältere Touchmessungen
        # enthalten. Für den aktuellen ControllerState brauchen wir
        # ausschließlich den neuesten Block.
        newest_block_index = touch_report_count - 1
        block_start = 36 + newest_block_index * 9

        touches: dict[int, TouchPoint] = {}

        for finger_index in range(2):
            point_index = block_start + 1 + finger_index * 4

            contact = report[point_index]

            active = (contact & 0x80) == 0

            if not active:
                continue

            finger_id = contact & 0x7F

            x_low = report[point_index + 1]
            xy_high = report[point_index + 2]
            y_high = report[point_index + 3]

            x = x_low | ((xy_high & 0x0F) << 8)
            y = ((xy_high & 0xF0) >> 4) | (y_high << 4)

            touches[finger_id] = TouchPoint(
                finger_id=finger_id,
                x=x,
                y=y,
            )

        return touches

    def _normalize_stick(
        self,
        raw_value: int,
    ) -> float:
        difference = raw_value - STICK_CENTER

        if abs(difference) <= STICK_DEADZONE:
            return 0.0

        if difference < 0:
            return round(
                difference / STICK_NEGATIVE_RANGE,
                3,
            )

        return round(
            difference / STICK_POSITIVE_RANGE,
            3,
        )
