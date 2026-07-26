from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    BUTTON_PRESSED = "button_pressed"
    BUTTON_RELEASED = "button_released"
    BUTTON_HELD = "button_held"
    BUTTON_DOUBLE_PRESSED = "button_double_pressed"
    AXIS_CHANGED = "axis_changed"


class Button(Enum):
    SQUARE = "SQUARE"
    CROSS = "CROSS"
    CIRCLE = "CIRCLE"
    TRIANGLE = "TRIANGLE"

    DPAD_UP = "DPAD_UP"
    DPAD_UP_RIGHT = "DPAD_UP_RIGHT"
    DPAD_RIGHT = "DPAD_RIGHT"
    DPAD_DOWN_RIGHT = "DPAD_DOWN_RIGHT"
    DPAD_DOWN = "DPAD_DOWN"
    DPAD_DOWN_LEFT = "DPAD_DOWN_LEFT"
    DPAD_LEFT = "DPAD_LEFT"
    DPAD_UP_LEFT = "DPAD_UP_LEFT"

    L1 = "L1"
    R1 = "R1"
    L2 = "L2"
    R2 = "R2"

    SHARE = "SHARE"
    OPTIONS = "OPTIONS"
    L3 = "L3"
    R3 = "R3"
    PS = "PS"
    TOUCHPAD_CLICK = "TOUCHPAD_CLICK"


class Axis(Enum):
    LEFT_X = "LEFT_X"
    LEFT_Y = "LEFT_Y"
    RIGHT_X = "RIGHT_X"
    RIGHT_Y = "RIGHT_Y"
    L2 = "L2"
    R2 = "R2"


@dataclass(frozen=True)
class ControllerEvent:
    event_type: EventType
    control: Button | Axis
    value: float
