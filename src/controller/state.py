from dataclasses import dataclass

from core.events import Axis, Button


@dataclass(frozen=True)
class TouchPoint:
    finger_id: int
    x: int
    y: int


@dataclass(frozen=True)
class ControllerState:
    buttons: frozenset[Button]
    axes: dict[Axis, float]
    touches: dict[int, TouchPoint]
