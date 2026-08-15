from dataclasses import dataclass
from enum import Enum
from time import sleep

import mido

from core.actions import Action, ActionEvent
from core.events import EventType
from outputs.base import Output


class MidiNoteMode(Enum):
    PULSE = "pulse"
    GATE = "gate"


@dataclass(frozen=True)
class MidiNoteMapping:
    note: int
    channel: int = 0
    velocity: int = 127
    mode: MidiNoteMode = MidiNoteMode.PULSE
    pulse_duration: float = 0.0


@dataclass(frozen=True)
class MidiControlChangeMapping:
    control: int
    channel: int = 0
    bipolar: bool = False


MidiMapping = MidiNoteMapping | MidiControlChangeMapping


MIDI_MAPPINGS: dict[Action, MidiMapping] = {
    # ---------------------------------------------------------------------
    # Layer 1 – Deck 1
    # ---------------------------------------------------------------------
    Action.DECK_1_PLAY_TOGGLE: MidiNoteMapping(
        note=36,
    ),
    Action.DECK_1_CUE: MidiNoteMapping(
        note=37,
        mode=MidiNoteMode.GATE,
    ),
    Action.DECK_1_SYNC: MidiNoteMapping(
        note=38,
    ),
    Action.DECK_1_LOAD_TRACK: MidiNoteMapping(
        note=39,
    ),
    Action.DECK_1_LOOP_SIZE_DECREASE: MidiNoteMapping(
        note=40,
    ),
    Action.DECK_1_LOOP_SIZE_INCREASE: MidiNoteMapping(
        note=41,
    ),
    Action.DECK_1_LOOP_TOGGLE: MidiNoteMapping(
        note=42,
        mode=MidiNoteMode.GATE,
    ),
    Action.DECK_1_BPM_INCREASE: MidiNoteMapping(
        note=43,
    ),
    Action.DECK_1_BPM_DECREASE: MidiNoteMapping(
        note=44,
    ),
    Action.DECK_1_HOTCUE_PREVIOUS: MidiNoteMapping(
        note=45,
    ),
    Action.DECK_1_HOTCUE_NEXT: MidiNoteMapping(
        note=46,
    ),
    Action.DECK_1_HOTCUE_TOGGLE: MidiNoteMapping(
        note=47,
    ),
    # ---------------------------------------------------------------------
    # Layer 1 – Deck 2
    # ---------------------------------------------------------------------
    Action.DECK_2_PLAY_TOGGLE: MidiNoteMapping(
        note=48,
    ),
    Action.DECK_2_CUE: MidiNoteMapping(
        note=49,
        mode=MidiNoteMode.GATE,
    ),
    Action.DECK_2_SYNC: MidiNoteMapping(
        note=50,
    ),
    Action.DECK_2_LOAD_TRACK: MidiNoteMapping(
        note=51,
    ),
    Action.DECK_2_LOOP_SIZE_DECREASE: MidiNoteMapping(
        note=52,
    ),
    Action.DECK_2_LOOP_SIZE_INCREASE: MidiNoteMapping(
        note=53,
    ),
    Action.DECK_2_LOOP_TOGGLE: MidiNoteMapping(
        note=54,
        mode=MidiNoteMode.GATE,
    ),
    Action.DECK_2_BPM_INCREASE: MidiNoteMapping(
        note=55,
    ),
    Action.DECK_2_BPM_DECREASE: MidiNoteMapping(
        note=56,
    ),
    Action.DECK_2_HOTCUE_PREVIOUS: MidiNoteMapping(
        note=57,
    ),
    Action.DECK_2_HOTCUE_NEXT: MidiNoteMapping(
        note=58,
    ),
    Action.DECK_2_HOTCUE_TOGGLE: MidiNoteMapping(
        note=59,
    ),
    # ---------------------------------------------------------------------
    # Browser Tree
    # ---------------------------------------------------------------------
    Action.BROWSER_TREE_UP: MidiNoteMapping(
        note=60,
    ),
    Action.BROWSER_TREE_DOWN: MidiNoteMapping(
        note=61,
    ),
    Action.BROWSER_TREE_COLLAPSE: MidiNoteMapping(
        note=62,
    ),
    Action.BROWSER_TREE_EXPAND: MidiNoteMapping(
        note=63,
    ),
    # ---------------------------------------------------------------------
    # Browser List
    # ---------------------------------------------------------------------
    Action.BROWSER_LIST_UP: MidiNoteMapping(
        note=68,
    ),
    Action.BROWSER_LIST_DOWN: MidiNoteMapping(
        note=69,
    ),
    # ---------------------------------------------------------------------
    # Touchpad – Deck 1
    # ---------------------------------------------------------------------
    Action.DECK_1_SEEK_FINE_BACKWARD: MidiNoteMapping(
        note=70,
        pulse_duration=0.05,
    ),
    Action.DECK_1_SEEK_FINE_FORWARD: MidiNoteMapping(
        note=71,
        pulse_duration=0.05,
    ),
    Action.DECK_1_SEEK_4_BARS_BACKWARD: MidiNoteMapping(
        note=72,
        pulse_duration=0.05,
    ),
    Action.DECK_1_SEEK_4_BARS_FORWARD: MidiNoteMapping(
        note=73,
        pulse_duration=0.05,
    ),
    Action.DECK_1_SEEK_8_BARS_BACKWARD: MidiNoteMapping(
        note=74,
        pulse_duration=0.05,
    ),
    Action.DECK_1_SEEK_8_BARS_FORWARD: MidiNoteMapping(
        note=75,
        pulse_duration=0.05,
    ),
    # ---------------------------------------------------------------------
    # Touchpad – Deck 2
    # ---------------------------------------------------------------------
    Action.DECK_2_SEEK_FINE_BACKWARD: MidiNoteMapping(
        note=76,
        pulse_duration=0.05,
    ),
    Action.DECK_2_SEEK_FINE_FORWARD: MidiNoteMapping(
        note=77,
        pulse_duration=0.05,
    ),
    Action.DECK_2_SEEK_4_BARS_BACKWARD: MidiNoteMapping(
        note=78,
        pulse_duration=0.05,
    ),
    Action.DECK_2_SEEK_4_BARS_FORWARD: MidiNoteMapping(
        note=79,
        pulse_duration=0.05,
    ),
    Action.DECK_2_SEEK_8_BARS_BACKWARD: MidiNoteMapping(
        note=80,
        pulse_duration=0.05,
    ),
    Action.DECK_2_SEEK_8_BARS_FORWARD: MidiNoteMapping(
        note=81,
        pulse_duration=0.05,
    ),
    # ---------------------------------------------------------------------
    # Layer 2 – Mixer / Volume
    #
    # Die Werte kommen aus ActionProcessor bereits als 0.0 bis 1.0.
    # Deshalb hier KEIN bipolar=True.
    # ---------------------------------------------------------------------
    Action.DECK_1_VOLUME: MidiControlChangeMapping(
        control=20,
    ),
    Action.DECK_2_VOLUME: MidiControlChangeMapping(
        control=21,
    ),
    # ---------------------------------------------------------------------
    # Layer 2 – Deck 1 EQ
    # ---------------------------------------------------------------------
    Action.DECK_1_EQ_HIGH: MidiControlChangeMapping(
        control=22,
    ),
    Action.DECK_1_EQ_MID: MidiControlChangeMapping(
        control=23,
    ),
    Action.DECK_1_EQ_LOW: MidiControlChangeMapping(
        control=24,
    ),
    # ---------------------------------------------------------------------
    # Layer 2 – Deck 2 EQ
    # ---------------------------------------------------------------------
    Action.DECK_2_EQ_HIGH: MidiControlChangeMapping(
        control=25,
    ),
    Action.DECK_2_EQ_MID: MidiControlChangeMapping(
        control=26,
    ),
    Action.DECK_2_EQ_LOW: MidiControlChangeMapping(
        control=27,
    ),
    # ---------------------------------------------------------------------
    # Layer 2 – Mixer FX Deck A
    # ---------------------------------------------------------------------
    Action.MIXER_FX_A_AMOUNT_DECREASE: MidiNoteMapping(
        note=82,
    ),
    Action.MIXER_FX_A_AMOUNT_INCREASE: MidiNoteMapping(
        note=83,
    ),
    Action.MIXER_FX_A_PREVIOUS: MidiNoteMapping(
        note=84,
    ),
    Action.MIXER_FX_A_NEXT: MidiNoteMapping(
        note=85,
    ),
    Action.MIXER_FX_A_LOAD: MidiNoteMapping(
        note=86,
    ),
    Action.MIXER_FX_A_TOGGLE: MidiNoteMapping(
        note=87,
    ),
    # ---------------------------------------------------------------------
    # Layer 2 – Mixer FX Deck B
    # ---------------------------------------------------------------------
    Action.MIXER_FX_B_AMOUNT_DECREASE: MidiNoteMapping(
        note=88,
    ),
    Action.MIXER_FX_B_AMOUNT_INCREASE: MidiNoteMapping(
        note=89,
    ),
    Action.MIXER_FX_B_PREVIOUS: MidiNoteMapping(
        note=90,
    ),
    Action.MIXER_FX_B_NEXT: MidiNoteMapping(
        note=91,
    ),
    Action.MIXER_FX_B_LOAD: MidiNoteMapping(
        note=92,
    ),
    Action.MIXER_FX_B_TOGGLE: MidiNoteMapping(
        note=93,
    ),
    Action.MIXER_FX_A_AMOUNT: MidiControlChangeMapping(
        control=28,
    ),
    Action.MIXER_FX_B_AMOUNT: MidiControlChangeMapping(
        control=29,
    ),
}


class MidiOutput(Output):
    """
    Übersetzt ActionEvents in MIDI-Nachrichten.

    Im Debug-Modus wird jede tatsächlich versendete
    MIDI-Nachricht im Terminal angezeigt.
    """

    def __init__(
        self,
        port_name: str = "plaiiboy",
        mappings: dict[Action, MidiMapping] | None = None,
        debug: bool = True,
    ) -> None:
        self._port_name = port_name

        self._mappings = (
            mappings.copy() if mappings is not None else MIDI_MAPPINGS.copy()
        )

        self._debug = debug
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

        if self._debug:
            print(f'[MIDI] Virtueller Ausgang "{self._port_name}" verbunden.')

    def handle(
        self,
        event: ActionEvent,
    ) -> None:
        if self._port is None:
            raise RuntimeError("MIDI-Ausgang ist nicht verbunden.")

        mapping = self._mappings.get(event.action)

        if mapping is None:
            if self._debug:
                print(f"[MIDI SKIP] Kein Mapping für {event.action.name}")

            return

        if isinstance(
            mapping,
            MidiNoteMapping,
        ):
            self._send_note(
                event,
                mapping,
            )
            return

        self._send_control_change(
            event,
            mapping,
        )

    def _send_note(
        self,
        event: ActionEvent,
        mapping: MidiNoteMapping,
    ) -> None:
        if mapping.mode is MidiNoteMode.GATE:
            self._send_gate_note(
                event,
                mapping,
            )
            return

        self._send_pulse_note(mapping)

    def _send_gate_note(
        self,
        event: ActionEvent,
        mapping: MidiNoteMapping,
    ) -> None:
        event_type = event.source_event.event_type

        if event_type is EventType.BUTTON_PRESSED:
            message = mido.Message(  # type: ignore[attr-defined]
                "note_on",
                note=mapping.note,
                velocity=mapping.velocity,
                channel=mapping.channel,
            )

        elif event_type is EventType.BUTTON_RELEASED:
            message = mido.Message(  # type: ignore[attr-defined]
                "note_off",
                note=mapping.note,
                velocity=0,
                channel=mapping.channel,
            )

        else:
            if self._debug:
                print(
                    "[MIDI SKIP] "
                    f"Gate-Note {mapping.note} "
                    f"ignoriert Eventtyp "
                    f"{event_type.name}"
                )

            return

        self._send_message(message)

    def _send_pulse_note(
        self,
        mapping: MidiNoteMapping,
    ) -> None:
        note_on = mido.Message(  # type: ignore[attr-defined]
            "note_on",
            note=mapping.note,
            velocity=mapping.velocity,
            channel=mapping.channel,
        )

        note_off = mido.Message(  # type: ignore[attr-defined]
            "note_off",
            note=mapping.note,
            velocity=0,
            channel=mapping.channel,
        )

        self._send_message(note_on)

        if mapping.pulse_duration > 0:
            sleep(mapping.pulse_duration)

        self._send_message(note_off)

    def _send_control_change(
        self,
        event: ActionEvent,
        mapping: MidiControlChangeMapping,
    ) -> None:
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

        self._send_message(message)

    def _send_message(
        self,
        message: mido.Message,
    ) -> None:
        if self._port is None:
            raise RuntimeError("MIDI-Ausgang ist nicht verbunden.")

        self._port.send(message)

        if self._debug:
            self._print_message(message)

    def _print_message(
        self,
        message: mido.Message,
    ) -> None:
        """
        Nutzt die eigene Textdarstellung von mido.Message.

        Mido erzeugt Attribute wie note, velocity, control und value
        dynamisch abhängig vom Nachrichtentyp.
        """

        print(f"[MIDI OUT] {message}")

    def _to_midi_value(
        self,
        value: float,
        bipolar: bool,
    ) -> int:
        if bipolar:
            normalized = (value + 1.0) / 2.0
        else:
            normalized = value

        normalized = max(
            0.0,
            min(
                1.0,
                normalized,
            ),
        )

        return round(normalized * 127)

    def close(self) -> None:
        if self._port is None:
            return

        self._port.close()
        self._port = None

        if self._debug:
            print(f'[MIDI] Virtueller Ausgang "{self._port_name}" geschlossen.')
