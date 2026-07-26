import time
import zlib

import hid


SONY_VENDOR_ID = 0x054C
DUALSHOCK_4_PRODUCT_ID = 0x05C4

FULL_REPORT_SIZE = 78


def create_enable_report() -> bytes:
    report = bytearray(FULL_REPORT_SIZE)

    # Bluetooth-Ausgabereport
    report[0] = 0x11

    # HID aktivieren + CRC aktivieren + 4-ms-Intervall
    report[1] = 0xC4

    # CRC über Seed 0xA2 und alle Bytes außer den letzten vier
    crc = zlib.crc32(bytes([0xA2]) + report[:-4])

    # CRC als vier Bytes in Little-Endian einsetzen
    report[-4:] = crc.to_bytes(4, byteorder="little")

    return bytes(report)


def main() -> None:
    devices = hid.enumerate(
        SONY_VENDOR_ID,
        DUALSHOCK_4_PRODUCT_ID,
    )

    if not devices:
        raise RuntimeError("DualShock 4 wurde nicht gefunden.")

    gamepad = hid.device()

    try:
        gamepad.open_path(devices[0]["path"])
        gamepad.set_nonblocking(True)

        print("DualShock 4 geöffnet.")

        enable_report = create_enable_report()
        written = gamepad.write(enable_report)

        print(f"Ausgabereport gesendet: {written} Bytes")
        print("Warte auf Eingabedaten …")
        print("Beenden mit Ctrl + C.\n")

        previous_position = None

while True:
    report = gamepad.read(FULL_REPORT_SIZE)

    if not report:
        time.sleep(0.005)
        continue

    if len(report) != 78 or report[0] != 0x11:
        continue

    # Im Bluetooth-Report beginnt der erste aktuelle Touch-Bericht
    # bei Byte 37. Byte 38 ist der Status des ersten Fingers.
    finger_status = report[38]

    # Höchstes Bit gesetzt = Finger nicht auf dem Touchpad
    finger_active = (finger_status & 0x80) == 0

    if not finger_active:
        if previous_position is not None:
            print("Finger losgelassen\n")
            previous_position = None
        continue

    x = report[39] | ((report[40] & 0x0F) << 8)
    y = ((report[40] & 0xF0) >> 4) | (report[41] << 4)

    position = (x, y)

    if position != previous_position:
        print(f"Finger: x={x:4d}, y={y:4d}")
        previous_position = position

    except KeyboardInterrupt:
        print("\nTest beendet.")

    finally:
        gamepad.close()


if __name__ == "__main__":
    main()