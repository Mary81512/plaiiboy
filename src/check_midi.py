import time

import mido


def find_plaiiboy_port() -> str:
    input_names = mido.get_input_names()  # type: ignore[attr-defined]

    print("Verfügbare MIDI-Eingänge:")

    for name in input_names:
        print(f"  - {name}")

    for name in input_names:
        if "plaiiboy" in name.lower():
            return name

    raise RuntimeError(
        "Der MIDI-Port 'plaiiboy' wurde nicht gefunden. "
        "Läuft src/main.py in einem zweiten Terminal?"
    )


def main() -> None:
    port_name = find_plaiiboy_port()

    print(f"\nVerbinde mit: {port_name}")
    print("Warte auf MIDI-Nachrichten.")
    print("Beenden mit Ctrl + C.\n")

    midi_input = mido.open_input(port_name)  # type: ignore[attr-defined]

    try:
        while True:
            for message in midi_input.iter_pending():
                print(message)

            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\nMIDI-Monitor beendet.")

    finally:
        midi_input.close()


if __name__ == "__main__":
    main()
