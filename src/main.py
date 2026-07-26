from controller.input_manager import InputManager


def main() -> None:
    inputs = InputManager()

    try:
        inputs.connect()

        print("plaiiboy")
        print("Input Manager gestartet.")
        print("Beenden mit Ctrl + C.\n")

        while True:
            for event in inputs.poll():
                print(
                    f"{event.event_type.value:<16}"
                    f"{event.control.value:<18}"
                    f"{event.value}"
                )

    except KeyboardInterrupt:
        print("\nProgramm beendet.")

    finally:
        inputs.close()


if __name__ == "__main__":
    main()
