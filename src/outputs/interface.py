import json
from threading import Lock
from typing import Any

import webview

from core.actions import ActionEvent
from outputs.base import Output


class InterfaceOutput(Output):
    """
    Überträgt Statusänderungen aus dem Python-Core an die Weboberfläche.
    """

    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self._ready = False
        self._pending_status: dict[str, Any] = {}
        self._lock = Lock()

    def attach_window(self, window: webview.Window) -> None:
        with self._lock:
            self._window = window

    def mark_ready(self) -> None:
        with self._lock:
            self._ready = True
            pending_status = self._pending_status.copy()
            self._pending_status.clear()

        if pending_status:
            self.update_status(**pending_status)

    def update_status(self, **status: Any) -> None:
        with self._lock:
            if not self._ready or self._window is None:
                self._pending_status.update(status)
                return

            window = self._window

        payload = json.dumps(status)

        try:
            window.evaluate_js(f"window.plaiiboy.updateStatus({payload});")
        except Exception as error:  # noqa: BLE001
            print(f"[INTERFACE] Status konnte nicht übertragen werden: {error}")

    def handle(self, event: ActionEvent) -> None:
        source_event = event.source_event

        control_name = getattr(
            source_event.control,
            "name",
            str(source_event.control),
        )

        self.update_status(
            lastInput=control_name,
            lastAction=event.action.name,
        )

    def close(self) -> None:
        with self._lock:
            self._ready = False
            self._window = None
