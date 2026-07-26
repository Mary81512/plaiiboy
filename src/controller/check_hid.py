import time

import hid


SONY_VENDOR_ID = 0x054C
DUALSHOCK_4_PRODUCT_ID = 0x05C4

STICK_CENTER = 128
STICK_DEADZONE = 15


FACE_BUTTONS = {
    0x10: "Quadrat",
    0x20: "X",
    0x40: "Kreis",
    0x80: "Dreieck",
}

SECONDARY_BUTTONS = {
    0x01: "L1",
    0x02: "R1",
    0x04: "L2",
    0x08: "R2",
    0x10: "Share",
    0x20: "Options",
    0x40: "L3",
    0x80: "R3",
}

DPAD_DIRECTIONS = {
    0: "Oben",
    1: "Oben rechts",
    2: "Rechts",
    3: "Unten rechts",
    4: "Unten",
    5: "Unten links",
    6: "Links",
    7: "Oben links",
    8: None,
}


def stick_direction(value: int, negative: str, positive: str) -> str | None:
    difference = value - STICK_CENTER

    if abs(difference) <= STICK_DEADZONE:
        return None

    return negative if difference < 0 else positive


def decode_report(report: list[int]) -> set[str]:
    if len(report) < 10:
        return set()

    inputs: set[str] = set()

    left_x = report[1]
    left_y = report[2]
    right_x = report[3]
    right_y = report[4]

    buttons_1 = report[5]
    buttons_2 = report[6]
    buttons_3 = report[7]

    dpad_value = buttons_1 & 0x0F
    face_bits = buttons_1 & 0xF0

    dpad_direction = DPAD_DIRECTIONS.get(dpad_value)
    if dpad_direction:
        inputs.add(f"Steuerkreuz {dpad_direction}")

    for bit, name in FACE_BUTTONS.items():
        if face_bits & bit:
            inputs.add(name)

    for bit, name in SECONDARY_BUTTONS.items():
        if buttons_2 & bit:
            inputs.add(name)

    if buttons_3 & 0x01:
        inputs.add("PS")

    if buttons_3 & 0x02:
        inputs.add("Touchpad-Klick")

    stick_inputs = (
        stick_direction(left_x, "Linker Stick links", "Linker Stick rechts"),
        stick_direction(left_y, "Linker Stick oben", "Linker Stick unten"),
        stick_direction(right_x, "Rechter Stick links", "Rechter Stick rechts"),
        stick_direction(right_y, "Rechter Stick oben", "Rechter Stick unten"),
    )

    for stick_input in stick_inputs:
        if stick_input:
            inputs.add(stick_input)

    if report[8] > 20:
        inputs.add(f"L2 analog: {report[8]}")

    if report[9] > 20:
        inputs.add(f"R2 analog: {report[9]}")

    return inputs


def main() -> None:
    devices = hid.enumerate(
        SONY_VENDOR_ID,
        DUALSHOCK_4_PRODUCT_ID,
    )

    if not devices:
        raise RuntimeError("DualShock 4 wurde nicht gefunden.")

    gamepad = hid.device()
    previous_inputs: set[str] = set()

    try:
        gamepad.open_path(devices[0]["path"])
        gamepad.set_nonblocking(True)

        print("DualShock 4 geöffnet.")
        print("Drücke Tasten oder bewege die Sticks.")
        print("Beenden mit Ctrl + C.\n")

        while True:
            report = gamepad.read(78)

            if not report:
                time.sleep(0.005)
                continue

            current_inputs = decode_report(report)

            pressed = current_inputs - previous_inputs
            released = previous_inputs - current_inputs

            for input_name in sorted(pressed):
                print(f"GEDRÜCKT:   {input_name}")

            for input_name in sorted(released):
                print(f"LOSGELASSEN: {input_name}")

            previous_inputs = current_inputs

    except KeyboardInterrupt:
        print("\nTest beendet.")

    finally:
        gamepad.close()


if __name__ == "__main__":
    main()