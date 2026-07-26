from dataclasses import dataclass

import mido

from core.actions import Action, ActionEvent
from core.events import EventType
from outputs.base import Output


@dataclass(frozen=True)
class MidiNoteMapping:
    note: int
    channel: int = 0
    velocity: int = 127


@dataclass(frozen=True)
class MidiControlChangeMapping:
    control: int
    channel: int = 0
    bipolar: bool = False


MidiMapping = MidiNoteMapping | MidiControlChangeMapping


TEST_MIDI_MAPPINGS: dict[Action, MidiMapping] = {
    Action.PLAY_PAUSE: MidiNoteMapping(note=36),
    Action.CUE: MidiNoteMapping(note=37),
    Action.SYNC: MidiNoteMapping(note=38),
    Action.LOAD_TRACK: MidiNoteMapping(note=39),
    Action.LEFT_STICK_X: MidiControlChangeMapping(
        control=20,
        bipolar=True,
    ),
    Action.LEFT_STICK_Y: MidiControlChangeMapping(
        control=21,
        bipolar=True,
    ),
    Action.LEFT_TRIGGER: MidiControlChangeMapping(
        control=22,
    ),
    Action.RIGHT_TRIGGER: MidiControlChangeMapping(
        control=23,
    ),
}


class MidiOutput(Output):
    def __init__(
        self,
        port_name: str = "plaiiboy",
        mappings: dict[Action, MidiMapping] | None = None,
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

        if isinstance(mapping, MidiNoteMapping):
            self._send_note(event, mapping)
            return

        if isinstance(mapping, MidiControlChangeMapping):
            self._send_control_change(event, mapping)

    def _send_note(
        self,
        event: ActionEvent,
        mapping: MidiNoteMapping,
    ) -> None:
        if self._port is None:
            return

        if event.source_event.event_type is EventType.BUTTON_PRESSED:
            message_type = "note_on"
            velocity = mapping.velocity

        elif event.source_event.event_type is EventType.BUTTON_RELEASED:
            message_type = "note_off"
            velocity = 0

        else:
            return

        message = mido.Message(  # type: ignore[attr-defined]
            message_type,
            note=mapping.note,
            velocity=velocity,
            channel=mapping.channel,
        )

        self._port.send(message)

    def _send_control_change(
        self,
        event: ActionEvent,
        mapping: MidiControlChangeMapping,
    ) -> None:
        if self._port is None:
            return

        midi_value = self._to_midi_value(
            event.value,
            bipolar=mapping.bipolar,
        )

        message = mido.Message(  # type: ignore[attr-defined]
            "control_change",
            control=mapping.control,
            value=midi_value,
            channel=mapping.channel,
        )

        self._port.send(message)

    def _to_midi_value(
        self,
        value: float,
        bipolar: bool,
    ) -> int:
        if bipolar:
            normalized = (value + 1.0) / 2.0
        else:
            normalized = value

        normalized = max(0.0, min(1.0, normalized))

        return round(normalized * 127)

    def close(self) -> None:
        if self._port is not None:
            self._port.close()
            self._port = None
