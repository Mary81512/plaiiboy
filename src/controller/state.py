from dataclasses import dataclass

from core.events import Axis, Button


@dataclass(frozen=True)
class ControllerState:
    buttons: frozenset[Button]
    axes: dict[Axis, float]
