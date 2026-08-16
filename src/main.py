from time import monotonic

from controller.input_manager import InputManager
from core.action_processor import ActionProcessor
from core.actions import Action
from core.dispatcher import Dispatcher
from core.events import Axis, Button, EventType
from core.layers import Layer, LayerManager
from core.mapping import ActionMapper
from inputs.traktor_feedback import TraktorFeedbackInput
from outputs.debug import DebugOutput
from outputs.interface import InterfaceOutput
from outputs.midi import MidiOutput


def apply_layer_feedback(
    inputs: InputManager,
    layers: LayerManager,
) -> None:
    red, green, blue = layers.active_layer.lightbar_color

    inputs.set_lightbar(
        red=red,
        green=green,
        blue=blue,
    )

    print(f"Aktiver Layer: {layers.active_layer.number}")


def run_core(
    interface_output: InterfaceOutput | None = None,
) -> None:
    inputs = InputManager()
    layers = LayerManager()
    mapper = ActionMapper()
    action_processor = ActionProcessor()
    traktor_feedback = TraktorFeedbackInput()

    midi_output = MidiOutput()

    dispatcher = Dispatcher()
    dispatcher.add_output(DebugOutput())
    dispatcher.add_output(midi_output)

    if interface_output is not None:
        dispatcher.add_output(interface_output)

    try:
        traktor_feedback.connect()
        inputs.connect()
        midi_output.connect()

        apply_layer_feedback(
            inputs=inputs,
            layers=layers,
        )

        if interface_output is not None:
            interface_output.update_status(
                controller="Verbunden",
                midi="plaiiboy",
                layer=layers.active_layer.number,
                activeDeck=action_processor.state.active_deck.value,
                seekMode=action_processor.state.seek_mode.label,
                lastInput="—",
                lastAction="—",
            )

        print("plaiiboy")
        print("Framework gestartet.")
        print(f"Aktives Bearbeitungsdeck: {action_processor.state.active_deck.value}")
        print(f"Touchpad-Suchmodus: {action_processor.state.seek_mode.label}")
        print("Virtueller MIDI-Port: plaiiboy")
        print("Beenden mit Ctrl + C.\n")

        # Wird für die relative Mixer-Steuerung verwendet.
        last_mixer_update = monotonic()

        while True:
            track_end_warnings = traktor_feedback.poll()

            for warning_deck in track_end_warnings:
                print(f"Track-End-Warnung: {warning_deck}")
                inputs.rumble_track_end_warning()

            controller_events = inputs.poll()

            # -------------------------------------------------------------
            # Zeit seit dem letzten Schleifendurchlauf
            # -------------------------------------------------------------

            now = monotonic()
            delta_time = now - last_mixer_update
            last_mixer_update = now

            # -------------------------------------------------------------
            # Layer 2 – kontinuierliche Mixer-Steuerung
            #
            # Die Sticks werden hier direkt aus dem aktuellen
            # Controllerzustand gelesen.
            #
            # Dadurch können wir einen Stick halten und der Wert
            # verändert sich weiter, auch wenn kein neues AXIS_CHANGED
            # Event erzeugt wird.
            # -------------------------------------------------------------

            if layers.active_layer is Layer.LAYER_2 and inputs.latest_state is not None:
                axes = inputs.latest_state.axes

                touches = inputs.latest_state.touches

                mixer_events = action_processor.process_mixer_axes(
                    left_x=axes.get(
                        Axis.LEFT_X,
                        0.0,
                    ),
                    left_y=axes.get(
                        Axis.LEFT_Y,
                        0.0,
                    ),
                    right_x=axes.get(
                        Axis.RIGHT_X,
                        0.0,
                    ),
                    right_y=axes.get(
                        Axis.RIGHT_Y,
                        0.0,
                    ),
                    delta_time=delta_time,
                )

                for mixer_event in mixer_events:
                    dispatcher.dispatch(mixer_event)

                touchpad_volume_events = action_processor.process_touchpad_volumes(
                    touches=touches,
                )

                for volume_event in touchpad_volume_events:
                    dispatcher.dispatch(volume_event)

                mixer_fx_events = action_processor.process_mixer_fx_triggers(
                    l2=axes.get(
                        Axis.L2,
                        0.0,
                    ),
                    r2=axes.get(
                        Axis.R2,
                        0.0,
                    ),
                    delta_time=delta_time,
                )

                for mixer_fx_event in mixer_fx_events:
                    dispatcher.dispatch(mixer_fx_event)
            # -------------------------------------------------------------
            # Layer 3 – Single FX
            # -------------------------------------------------------------

            if layers.active_layer is Layer.LAYER_3 and inputs.latest_state is not None:
                axes = inputs.latest_state.axes

                fx_axis_events = action_processor.process_fx_axes(
                    left_y=axes.get(
                        Axis.LEFT_Y,
                        0.0,
                    ),
                    right_y=axes.get(
                        Axis.RIGHT_Y,
                        0.0,
                    ),
                    delta_time=delta_time,
                )

                for fx_event in fx_axis_events:
                    dispatcher.dispatch(fx_event)

                fx_trigger_events = action_processor.process_fx_triggers(
                    l2=axes.get(
                        Axis.L2,
                        0.0,
                    ),
                    r2=axes.get(
                        Axis.R2,
                        0.0,
                    ),
                    delta_time=delta_time,
                )

                for fx_event in fx_trigger_events:
                    dispatcher.dispatch(fx_event)
            # -------------------------------------------------------------
            # Interface – Controllerzustand
            # -------------------------------------------------------------

            if interface_output is not None and inputs.latest_state is not None:
                latest_state = inputs.latest_state
                motion = latest_state.motion

                status_update = {
                    "axes": {
                        axis.name: value for axis, value in latest_state.axes.items()
                    },
                    "buttons": [button.name for button in latest_state.buttons],
                }

                if motion is not None:
                    status_update["motion"] = {
                        "gyroX": motion.gyro_x,
                        "gyroY": motion.gyro_y,
                        "gyroZ": motion.gyro_z,
                        "accelX": motion.accel_x,
                        "accelY": motion.accel_y,
                        "accelZ": motion.accel_z,
                    }

                interface_output.update_status(**status_update)

            # -------------------------------------------------------------
            # Normale Controller-Events
            # -------------------------------------------------------------

            for controller_event in controller_events:
                control_name = getattr(
                    controller_event.control,
                    "name",
                    str(controller_event.control),
                )

                if interface_output is not None:
                    event_type_name = getattr(
                        controller_event.event_type,
                        "name",
                        str(controller_event.event_type),
                    )

                    interface_output.update_status(
                        lastInput=control_name,
                        controllerEvent={
                            "control": control_name,
                            "eventType": event_type_name,
                            "value": controller_event.value,
                        },
                    )

                print(
                    f"input={controller_event.event_type.value:<25} "
                    f"control={controller_event.control.value:<18} "
                    f"value={controller_event.value:.3f}"
                )

                # ---------------------------------------------------------
                # PS = globaler Layer-Wechsel
                # ---------------------------------------------------------

                if (
                    controller_event.control is Button.PS
                    and controller_event.event_type is EventType.BUTTON_PRESSED
                ):
                    layers.cycle()

                    apply_layer_feedback(
                        inputs=inputs,
                        layers=layers,
                    )

                    if interface_output is not None:
                        interface_output.update_status(
                            layer=layers.active_layer.number,
                        )

                    continue

                # ---------------------------------------------------------
                # Normales Mapping des aktiven Layers
                # ---------------------------------------------------------

                mapped_events = mapper.map_event(
                    event=controller_event,
                    layer=layers.active_layer,
                )

                for mapped_event in mapped_events:
                    processed_events = action_processor.process(mapped_event)

                    for action_event in processed_events:
                        if action_event.action is Action.FEEDBACK_ACTIVE_DECK_1:
                            print("Aktives Bearbeitungsdeck: 1")

                            inputs.rumble_pulses(
                                pulse_count=1,
                            )

                            if interface_output is not None:
                                interface_output.update_status(
                                    activeDeck=1,
                                )

                        elif action_event.action is Action.FEEDBACK_ACTIVE_DECK_2:
                            print("Aktives Bearbeitungsdeck: 2")

                            if interface_output is not None:
                                interface_output.update_status(
                                    activeDeck=2,
                                )

                        elif action_event.action is Action.CYCLE_SEEK_SPEED:
                            print(
                                "Touchpad-Suchmodus: "
                                f"{action_processor.state.seek_mode.label}"
                            )

                            if interface_output is not None:
                                interface_output.update_status(
                                    seekMode=(action_processor.state.seek_mode.label),
                                )

                        dispatcher.dispatch(action_event)

    except KeyboardInterrupt:
        print("\nProgramm beendet.")

    finally:
        dispatcher.close()
        inputs.close()
        traktor_feedback.close()


if __name__ == "__main__":
    run_core()
