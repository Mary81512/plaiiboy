from controller.input_manager import InputManager
from core.layers import LayerManager
from core.mapping import ActionMapper


def main() -> None:
    inputs = InputManager()
    layers = LayerManager()
    mapper = ActionMapper()

    try:
        inputs.connect()

        print("plaiiboy")
        print("Input Manager, Layer Manager und Action Mapper gestartet.")
        print(f"Aktiver Layer: {layers.active_layer.value}")
        print("Beenden mit Ctrl + C.\n")

        while True:
            controller_events = inputs.poll()

            for controller_event in controller_events:
                action_events = mapper.map_event(
                    event=controller_event,
                    layer=layers.active_layer,
                )

                for action_event in action_events:
                    print(
                        f"layer={layers.active_layer.value:<10} "
                        f"action={action_event.action.value:<18} "
                        f"value={action_event.value}"
                    )

    except KeyboardInterrupt:
        print("\nProgramm beendet.")

    finally:
        inputs.close()


if __name__ == "__main__":
    main()
