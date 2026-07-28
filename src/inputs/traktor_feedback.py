import mido


class TraktorFeedbackInput:
    DECK_A_SEEK_CONTROL = 90
    DECK_B_SEEK_CONTROL = 91

    def __init__(
        self,
        port_name: str = "plaiiboy-feedback Bus 1",
        warning_threshold: int = 118,
        reset_threshold: int = 105,
    ) -> None:
        self._port_name = port_name
        self._warning_threshold = warning_threshold
        self._reset_threshold = reset_threshold

        self._port: mido.ports.BaseInput | None = None

        self._deck_a_warned = False
        self._deck_b_warned = False

    def connect(self) -> None:
        self._port = mido.open_input(  # type: ignore[attr-defined]
            self._port_name,
        )

        print(f'[MIDI] Traktor-Feedback "{self._port_name}" verbunden.')

    def poll(self) -> list[str]:
        if self._port is None:
            raise RuntimeError("Traktor-Feedback-Eingang ist nicht verbunden.")

        warnings: list[str] = []

        for message in self._port.iter_pending():
            if message.type != "control_change":
                continue

            if message.channel != 0:
                continue

            if message.control == self.DECK_A_SEEK_CONTROL:
                if self._update_warning_state(
                    value=message.value,
                    already_warned=self._deck_a_warned,
                ):
                    warnings.append("deck_a")
                    self._deck_a_warned = True

                elif message.value <= self._reset_threshold:
                    self._deck_a_warned = False

            elif message.control == self.DECK_B_SEEK_CONTROL:
                if self._update_warning_state(
                    value=message.value,
                    already_warned=self._deck_b_warned,
                ):
                    warnings.append("deck_b")
                    self._deck_b_warned = True

                elif message.value <= self._reset_threshold:
                    self._deck_b_warned = False

        return warnings

    def _update_warning_state(
        self,
        value: int,
        already_warned: bool,
    ) -> bool:
        return value >= self._warning_threshold and not already_warned

    def close(self) -> None:
        if self._port is None:
            return

        self._port.close()
        self._port = None

        print("[MIDI] Traktor-Feedback geschlossen.")
