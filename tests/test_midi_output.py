from core.actions import Action, ActionEvent
from core.events import Button, ControllerEvent, EventType
from outputs.midi import MidiNoteMapping, MidiNoteMode, MidiOutput


class FakePort:
    def __init__(self) -> None:
        self.messages: list[object] = []

    def send(self, message: object) -> None:
        self.messages.append(message)


def create_cue_event(event_type: EventType) -> ActionEvent:
    return ActionEvent(
        action=Action.DECK_1_CUE,
        value=1.0,
        source_event=ControllerEvent(
            event_type=event_type,
            control=Button.L2,
            value=1.0,
        ),
    )


def test_active_gate_note_is_released_after_controller_disconnect() -> None:
    output = MidiOutput(
        mappings={
            Action.DECK_1_CUE: MidiNoteMapping(
                note=37,
                mode=MidiNoteMode.GATE,
            )
        },
        debug=False,
    )
    port = FakePort()
    output._port = port  # type: ignore[assignment]

    output.handle(create_cue_event(EventType.BUTTON_PRESSED))
    output.release_active_gate_notes()
    output.release_active_gate_notes()

    assert [message.type for message in port.messages] == [  # type: ignore[attr-defined]
        "note_on",
        "note_off",
    ]
