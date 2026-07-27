import time
import zlib

import hid

SONY_VENDOR_ID = 0x054C
DUALSHOCK_4_PRODUCT_ID = 0x05C4

REPORT_SIZE = 78
CONNECT_TIMEOUT = 10.0
TEST_DURATION = 30.0

DS4_BT_REPORT_ID = 0x11
DS4_OUTPUT_CRC_SEED = 0xA2
DS4_HW_CONTROL = 0x80 | 0x40 | 0x04


def connect_controller() -> hid.device:
    print("Suche DualShock 4 ...")

    deadline = time.monotonic() + CONNECT_TIMEOUT

    while time.monotonic() < deadline:
        devices = hid.enumerate(
            SONY_VENDOR_ID,
            DUALSHOCK_4_PRODUCT_ID,
        )

        if devices:
            selected_device = devices[0]

            product_name = (
                selected_device.get("product_string")
                or "DUALSHOCK 4 Wireless Controller"
            )

            print(f"Gefunden: {product_name}")

            device = hid.device()
            device.open_path(selected_device["path"])
            device.set_nonblocking(True)

            return device

        time.sleep(0.5)

    raise RuntimeError("DualShock 4 wurde innerhalb von 10 Sekunden nicht gefunden.")


def create_full_report_request() -> list[int]:
    report = bytearray(REPORT_SIZE)

    report[0] = DS4_BT_REPORT_ID
    report[1] = DS4_HW_CONTROL
    report[2] = 0x00

    crc_data = bytes([DS4_OUTPUT_CRC_SEED]) + bytes(report[:-4])
    crc = zlib.crc32(crc_data) & 0xFFFFFFFF

    report[-4:] = crc.to_bytes(
        length=4,
        byteorder="little",
    )

    return list(report)


def decode_touch_point(
    report: list[int],
    point_index: int,
) -> tuple[bool, int, int, int]:
    contact = report[point_index]
    x_low = report[point_index + 1]
    xy_high = report[point_index + 2]
    y_high = report[point_index + 3]

    active = (contact & 0x80) == 0
    finger_id = contact & 0x7F

    x = x_low | ((xy_high & 0x0F) << 8)
    y = ((xy_high & 0xF0) >> 4) | (y_high << 4)

    return active, finger_id, x, y


def print_touch_data(report: list[int]) -> bool:
    if len(report) != REPORT_SIZE:
        return False

    if report[0] != DS4_BT_REPORT_ID:
        return False

    touch_report_count = min(report[35], 4)

    if touch_report_count == 0:
        return False

    printed_touch = False

    for touch_report_index in range(touch_report_count):
        block_start = 36 + touch_report_index * 9
        timestamp = report[block_start]

        for finger_index in range(2):
            point_index = block_start + 1 + finger_index * 4

            active, finger_id, x, y = decode_touch_point(
                report,
                point_index,
            )

            if not active:
                continue

            print(
                f"Touchblock={touch_report_index + 1} "
                f"Zeit={timestamp:3d} "
                f"Finger={finger_index + 1} "
                f"ID={finger_id:2d} "
                f"X={x:4d} "
                f"Y={y:3d}"
            )

            printed_touch = True

    return printed_touch


def main() -> None:
    device: hid.device | None = None

    try:
        device = connect_controller()
        assert device is not None

        output_report = create_full_report_request()

        print("Aktiviere vollständige Bluetooth-Reports ...")

        try:
            written = device.write(output_report)
        except OSError as error:
            raise RuntimeError(
                "Der Bluetooth-Output-Report konnte nicht gesendet werden."
            ) from error

        print(f"Gesendete Bytes: {written}")

        if written <= 0:
            raise RuntimeError("Es wurden keine Daten übertragen.")

        print()
        print("Touchpad-Test läuft.")
        print("Bitte langsam links/rechts und hoch/runter wischen.")
        print("Es werden nur aktive Berührungen angezeigt.")
        print("Beenden mit Ctrl + C.\n")

        deadline = time.monotonic() + TEST_DURATION

        received_full_reports = 0
        received_touch_reports = 0

        while time.monotonic() < deadline:
            try:
                report = device.read(REPORT_SIZE)
            except OSError as error:
                raise RuntimeError("Beim Lesen trat ein HID-Fehler auf.") from error

            if not report:
                time.sleep(0.005)
                continue

            report = list(report)

            if len(report) == REPORT_SIZE and report[0] == DS4_BT_REPORT_ID:
                received_full_reports += 1

                if print_touch_data(report):
                    received_touch_reports += 1

        print("\nTestzeit beendet.")
        print(f"Vollständige Reports: {received_full_reports}")
        print(f"Reports mit aktiver Berührung: {received_touch_reports}")

    except KeyboardInterrupt:
        print("\nTest manuell beendet.")

    except RuntimeError as error:
        print(f"\nFehler: {error}")

        if error.__cause__ is not None:
            print(
                "Ursprünglicher Fehler: "
                f"{type(error.__cause__).__name__}: "
                f"{error.__cause__}"
            )

    finally:
        if device is not None:
            device.close()

        print("Controller-Verbindung geschlossen.")


if __name__ == "__main__":
    main()
