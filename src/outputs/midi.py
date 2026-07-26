from dataclasses import dataclass

import mido

from core.actions import Action, ActionEvent
from outputs.base import Output


@dataclass(frozen=True)
class MidiNoteMapping:
    note: int
    channel: int = 0
    velocity: int = 127


TEST_MIDI_MAPPINGS: dict[Action, MidiNoteMapping] = {
    Action.PLAY_PAUSE: MidiNoteMapping(note=36),
    Action.CUE: MidiNoteMapping(note=37),
    Action.SYNC: MidiNoteMapping(note=38),
    Action.LOAD_TRACK: MidiNoteMapping(note=39),
}


class MidiOutput(Output):
    def __init__(
        self,
        port_name: str = "plaiiboy",
        mappings: dict[Action, MidiNoteMapping] | None = None,
    ) -> None:
        self._port_name = port_name
        self._mappings = (
            mappings.copy() if mappings is not None else TEST_MIDI_MAPPINGS.copy()
        )
        self._port: mido.ports.BaseOutput | None = None

    @property
    def connected(self) -> bool:
        return self._port is not None

    def connect(self) -> None:
        if self._port is not None:
            return

        self._port = mido.open_output(  # type: ignore[attr-defined]
            self._port_name,
            virtual=True,
        )

    def handle(self, event: ActionEvent) -> None:
        if self._port is None:
            raise RuntimeError("MIDI-Ausgang ist nicht verbunden.")

        mapping = self._mappings.get(event.action)

        if mapping is None:
            return

        message = mido.Message(
            "note_on",
            note=mapping.note,
            velocity=mapping.velocity,
            channel=mapping.channel,
        )

        self._port.send(message)

    def close(self) -> None:
        if self._port is not None:
            self._port.close()
            self._port = None
