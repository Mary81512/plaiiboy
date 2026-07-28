from controller.input_manager import InputManager
from core.action_processor import ActionProcessor
from core.actions import Action
from core.dispatcher import Dispatcher
from core.layers import LayerManager
from core.mapping import ActionMapper
from outputs.debug import DebugOutput
from outputs.midi import MidiOutput


def main() -> None:
    inputs = InputManager()
    layers = LayerManager()
    mapper = ActionMapper()
    action_processor = ActionProcessor()

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
        print(f"Aktives Bearbeitungsdeck: {action_processor.state.active_deck.value}")
        print(f"Touchpad-Suchmodus: {action_processor.state.seek_mode.label}")
        print("Virtueller MIDI-Port: plaiiboy")
        print("Beenden mit Ctrl + C.\n")

        while True:
            controller_events = inputs.poll()

            for controller_event in controller_events:
                print(
                    f"input={controller_event.event_type.value:<25} "
                    f"control={controller_event.control.value:<18} "
                    f"value={controller_event.value:.3f}"
                )

                mapped_events = mapper.map_event(
                    event=controller_event,
                    layer=layers.active_layer,
                )

                for mapped_event in mapped_events:
                    processed_events = action_processor.process(mapped_event)

                    for action_event in processed_events:
                        if action_event.action is Action.FEEDBACK_ACTIVE_DECK_1:
                            print(
                                "Aktives Bearbeitungsdeck: 1 "
                                "– später ein Vibrationsimpuls"
                            )

                        elif action_event.action is Action.FEEDBACK_ACTIVE_DECK_2:
                            print(
                                "Aktives Bearbeitungsdeck: 2 "
                                "– später zwei Vibrationsimpulse"
                            )

                        elif action_event.action is Action.CYCLE_SEEK_SPEED:
                            print(
                                "Touchpad-Suchmodus: "
                                f"{action_processor.state.seek_mode.label}"
                            )

                        dispatcher.dispatch(action_event)

    except KeyboardInterrupt:
        print("\nProgramm beendet.")

    finally:
        dispatcher.close()
        inputs.close()


if __name__ == "__main__":
    main()
