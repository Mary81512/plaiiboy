from dataclasses import dataclass

from core.events import Axis, Button


@dataclass(frozen=True)
class TouchPoint:
    finger_id: int
    x: int
    y: int


@dataclass(frozen=True)
class MotionState:
    gyro_x: int
    gyro_y: int
    gyro_z: int

    accel_x: int
    accel_y: int
    accel_z: int


@dataclass(frozen=True)
class ControllerState:
    buttons: frozenset[Button]
    axes: dict[Axis, float]
    touches: dict[int, TouchPoint]
    motion: MotionState | None = None
