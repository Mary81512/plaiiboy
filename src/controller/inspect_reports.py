import time
from collections import Counter

import hid

SONY_VENDOR_ID = 0x054C
DUALSHOCK_4_PRODUCT_ID = 0x05C4

READ_SIZE = 78
CONNECT_TIMEOUT = 10.0
SUMMARY_INTERVAL = 2.0
PRINT_INTERVAL = 0.08
MAX_CHANGED_INDICES = 30
RAW_PREVIEW_LENGTH = 40


def format_hex(values: list[int]) -> str:
    return " ".join(f"{value:02X}" for value in values)


def get_changed_indices(
    previous: list[int] | None,
    current: list[int],
) -> list[int]:
    if previous is None:
        return list(range(len(current)))

    shared_length = min(len(previous), len(current))

    changed = [
        index for index in range(shared_length) if previous[index] != current[index]
    ]

    if len(previous) != len(current):
        changed.extend(range(shared_length, len(current)))

    return changed


def format_changes(
    previous: list[int] | None,
    current: list[int],
    changed_indices: list[int],
) -> str:
    if not changed_indices:
        return "keine"

    parts: list[str] = []

    for index in changed_indices[:MAX_CHANGED_INDICES]:
        old_value = (
            previous[index] if previous is not None and index < len(previous) else None
        )
        new_value = current[index]

        if old_value is None:
            parts.append(f"{index}:-->{new_value:02X}")
        else:
            parts.append(f"{index}:{old_value:02X}>{new_value:02X}")

    remaining = len(changed_indices) - MAX_CHANGED_INDICES

    if remaining > 0:
        parts.append(f"... +{remaining} weitere")

    return ", ".join(parts)


def print_summary(
    total_reports: int,
    report_types: Counter[tuple[int, int]],
) -> None:
    print("\n--- Zwischenstand ---")
    print(f"Empfangene Reports insgesamt: {total_reports}")

    if not report_types:
        print("Noch keine Reports empfangen.")
    else:
        for (report_id, report_length), count in sorted(report_types.items()):
            print(f"ID=0x{report_id:02X} Länge={report_length:<3} Anzahl={count}")

    print("---------------------\n")


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

            print(f"Gefunden: {selected_device.get('product_string') or 'DualShock 4'}")
            print(
                f"Hersteller: "
                f"{selected_device.get('manufacturer_string') or 'unbekannt'}"
            )
            print(f"Interface: {selected_device.get('interface_number', 'unbekannt')}")

            device = hid.device()
            device.open_path(selected_device["path"])
            device.set_nonblocking(True)

            return device

        time.sleep(0.5)

    raise RuntimeError(
        "DualShock 4 wurde innerhalb von 10 Sekunden nicht gefunden. "
        "Bitte PS-Taste drücken oder Bluetooth neu verbinden."
    )


def main() -> None:
    device: hid.device | None = None

    report_types: Counter[tuple[int, int]] = Counter()
    previous_reports: dict[tuple[int, int], list[int]] = {}

    total_reports = 0
    last_summary_time = time.monotonic()
    last_print_time = 0.0

    try:
        device = connect_controller()
        assert device is not None

        print("\nPassive Report-Diagnose gestartet.")
        print("Es werden keine Daten an den Controller gesendet.")
        print()
        print("Bitte nacheinander testen:")
        print("1. Controller einige Sekunden liegen lassen")
        print("2. Eine normale Taste drücken")
        print("3. Touchpad klicken")
        print("4. Mit einem Finger über das Touchpad wischen")
        print("5. Optional mit zwei Fingern wischen")
        print()
        print("Beenden mit Ctrl + C.\n")

        while True:
            try:
                report = device.read(READ_SIZE)
            except OSError as error:
                raise RuntimeError(
                    "Beim passiven Lesen ist ein HID-Lesefehler "
                    "aufgetreten. Es wurde kein Output-Report gesendet."
                ) from error

            current_time = time.monotonic()

            if not report:
                if current_time - last_summary_time >= SUMMARY_INTERVAL:
                    print_summary(total_reports, report_types)
                    last_summary_time = current_time

                time.sleep(0.005)
                continue

            report = list(report)
            total_reports += 1

            report_id = report[0] if report else -1
            report_length = len(report)
            report_key = (report_id, report_length)

            report_types[report_key] += 1

            previous_report = previous_reports.get(report_key)
            changed_indices = get_changed_indices(
                previous_report,
                report,
            )

            is_new_report_type = previous_report is None
            enough_time_since_print = current_time - last_print_time >= PRINT_INTERVAL

            if is_new_report_type or (changed_indices and enough_time_since_print):
                print(
                    f"Report #{total_reports} | "
                    f"ID=0x{report_id:02X} | "
                    f"Länge={report_length}"
                )

                print(
                    "Geänderte Bytes: "
                    + format_changes(
                        previous_report,
                        report,
                        changed_indices,
                    )
                )

                preview = report[:RAW_PREVIEW_LENGTH]

                print(f"Rohdaten 0-{len(preview) - 1}: {format_hex(preview)}")

                if report_length > RAW_PREVIEW_LENGTH:
                    print(f"... {report_length - RAW_PREVIEW_LENGTH} weitere Bytes")

                print()

                last_print_time = current_time

            previous_reports[report_key] = report.copy()

            if current_time - last_summary_time >= SUMMARY_INTERVAL:
                print_summary(total_reports, report_types)
                last_summary_time = current_time

    except KeyboardInterrupt:
        print("\nDiagnose beendet.")

    except RuntimeError as error:
        print(f"\nFehler: {error}")

    finally:
        print_summary(total_reports, report_types)

        if device is not None:
            device.close()

        print("Controller-Verbindung geschlossen.")


if __name__ == "__main__":
    main()
