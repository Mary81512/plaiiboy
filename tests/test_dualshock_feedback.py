from controller.dualshock import DualShock4


class RecordingDualShock(DualShock4):
    def __init__(self) -> None:
        super().__init__()
        self.rumble_values: list[tuple[int, int]] = []

    def set_rumble(self, small_motor: int, large_motor: int) -> None:
        self.rumble_values.append((small_motor, large_motor))


def test_rumble_pulses_honors_pulse_count(monkeypatch) -> None:
    controller = RecordingDualShock()
    monkeypatch.setattr("controller.dualshock.time.sleep", lambda _delay: None)

    controller.rumble_pulses(
        pulse_count=2,
        delay=0.0,
        duration=0.0,
        strength=200,
    )

    assert controller.rumble_values == [
        (200, 0),
        (0, 0),
        (200, 0),
        (0, 0),
    ]
