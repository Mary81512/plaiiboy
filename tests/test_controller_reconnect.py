from time import monotonic

import pytest

from controller.dualshock import ControllerConnectionError, DualShock4
from core.layers import LayerManager
from main import run_controller_operation


class FakeInputs:
    def __init__(self) -> None:
        self.connect_calls = 0
        self.close_calls = 0
        self.lightbar_calls: list[tuple[int, int, int]] = []
        self.poll_calls = 0

    def connect(self) -> None:
        self.connect_calls += 1

    def close(self) -> None:
        self.close_calls += 1

    def set_lightbar(self, red: int, green: int, blue: int) -> None:
        self.lightbar_calls.append((red, green, blue))

    def poll(self) -> list[object]:
        self.poll_calls += 1

        if self.poll_calls == 1:
            raise ControllerConnectionError("Testabbruch")

        return []


class FakeMidiOutput:
    def __init__(self) -> None:
        self.release_calls = 0

    def release_active_gate_notes(self) -> None:
        self.release_calls += 1


class FakeInterfaceOutput:
    def __init__(self) -> None:
        self.status_updates: list[dict[str, object]] = []

    def update_status(self, **status: object) -> None:
        self.status_updates.append(status)


class BrokenHidDevice:
    def __init__(self) -> None:
        self.was_closed = False

    def read(self, _size: int) -> list[int]:
        raise OSError("read error")

    def close(self) -> None:
        self.was_closed = True


def test_hid_read_error_becomes_recoverable_connection_error() -> None:
    controller = DualShock4()
    device = BrokenHidDevice()
    controller._device = device  # type: ignore[assignment]
    controller._last_output_report_at = monotonic()

    with pytest.raises(ControllerConnectionError):
        controller.poll()

    assert device.was_closed
    assert not controller.connected


def test_controller_disconnect_reconnects_without_ending_core() -> None:
    inputs = FakeInputs()
    midi_output = FakeMidiOutput()
    interface_output = FakeInterfaceOutput()

    result = run_controller_operation(
        inputs.poll,
        inputs=inputs,  # type: ignore[arg-type]
        layers=LayerManager(),
        midi_output=midi_output,  # type: ignore[arg-type]
        interface_output=interface_output,  # type: ignore[arg-type]
    )

    assert result == []
    assert inputs.poll_calls == 2
    assert inputs.close_calls == 1
    assert inputs.connect_calls == 1
    assert inputs.lightbar_calls == [(255, 0, 0)]
    assert midi_output.release_calls == 1
    assert interface_output.status_updates == [
        {"controller": "Verbindung verloren – warte auf Controller"},
        {"controller": "Verbunden"},
    ]
