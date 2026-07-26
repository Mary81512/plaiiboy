from controller.dualshock import DualShock4


def main() -> None:
    controller = DualShock4()

    try:
        controller.connect()

        print("plaiiboy")
        print("DualShock 4 verbunden.")
        print("Beenden mit Ctrl + C.\n")

        while True:
            events = controller.poll()

            for event in events:
                print(
                    f"{event.event_type:<16} "
                    f"{event.control:<18} "
                    f"{event.value}"
                )

    except KeyboardInterrupt:
        print("\nProgramm beendet.")

    finally:
        controller.close()


if __name__ == "__main__":
    main()