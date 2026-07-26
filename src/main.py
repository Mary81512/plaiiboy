from controller.input_manager import InputManager
from core.dispatcher import Dispatcher
from core.layers import LayerManager
from core.mapping import ActionMapper
from outputs.debug import DebugOutput
from outputs.midi import MidiOutput


def main() -> None:
    inputs = InputManager()
    layers = LayerManager()
    mapper = ActionMapper()

    midi_output = MidiOutput()

    dispatcher = Dispatcher()
    dispatcher.add_output(DebugOutput())
    dispatcher.add_output(midi_output)

    try:
        inputs.connect()
        midi_output.connect()

        print("plaiiboy")
        print("Framework gestartet.")
        print(f"Aktiver Layer: {layers.active_layer.value}")
        print("Virtueller MIDI-Port: plaiiboy")
        print("Beenden mit Ctrl + C.\n")

        while True:
            controller_events = inputs.poll()

            for controller_event in controller_events:
                action_events = mapper.map_event(
                    event=controller_event,
                    layer=layers.active_layer,
                )

                for action_event in action_events:
                    dispatcher.dispatch(action_event)

    except KeyboardInterrupt:
        print("\nProgramm beendet.")

    finally:
        dispatcher.close()
        inputs.close()


if __name__ == "__main__":
    main()
