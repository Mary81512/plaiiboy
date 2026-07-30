from collections.abc import Callable
from pathlib import Path
from threading import Thread

import webview

from outputs.interface import InterfaceOutput


class InterfaceApi:
    def __init__(self, interface_output: InterfaceOutput) -> None:
        self._interface_output = interface_output

    def ready(self) -> dict[str, bool]:
        self._interface_output.mark_ready()
        return {"ready": True}


def run_interface(
    core_target: Callable[[InterfaceOutput], None] | None = None,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    interface_file = project_root / "ui" / "index.html"

    if not interface_file.exists():
        raise FileNotFoundError(
            f"Interface-Datei wurde nicht gefunden: {interface_file}"
        )

    interface_output = InterfaceOutput()
    api = InterfaceApi(interface_output)

    window = webview.create_window(
        title="plaiiboy",
        url="../ui/index.html",
        js_api=api,
        width=1500,
        height=950,
        min_size=(1100, 750),
    )

    if window is None:
        raise RuntimeError("Fenster konnte nicht erstellt werden.")

    interface_output.attach_window(window)

    if core_target is not None:
        core_thread = Thread(
            target=core_target,
            args=(interface_output,),
            name="plaiiboy-core",
            daemon=True,
        )
        core_thread.start()

    webview.start(debug=True, http_server=True)


if __name__ == "__main__":
    run_interface()
