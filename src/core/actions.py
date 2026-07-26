from dataclasses import dataclass
from enum import Enum

from core.events import ControllerEvent


class Action(Enum):
    PLAY_PAUSE = "PLAY_PAUSE"
    CUE = "CUE"
    SYNC = "SYNC"
    LOAD_TRACK = "LOAD_TRACK"


@dataclass(frozen=True)
class ActionEvent:
    action: Action
    value: float
    source_event: ControllerEvent
