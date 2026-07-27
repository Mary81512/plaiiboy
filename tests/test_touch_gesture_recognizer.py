from controller.state import ControllerState, TouchPoint
from controller.touch_gesture_recognizer import (
    TouchGestureRecognizer,
)
from core.events import EventType, TouchGesture


def create_state(
    touches: dict[int, TouchPoint],
) -> ControllerState:
    return ControllerState(
        buttons=frozenset(),
        axes={},
        touches=touches,
    )


def test_swipe_right_is_recognized() -> None:
    recognizer = TouchGestureRecognizer()

    start = create_state(
        {
            3: TouchPoint(
                finger_id=3,
                x=200,
                y=400,
            )
        }
    )

    end = create_state(
        {
            3: TouchPoint(
                finger_id=3,
                x=900,
                y=410,
            )
        }
    )

    released = create_state({})

    assert recognizer.generate(start) == []
    assert recognizer.generate(end) == []

    events = recognizer.generate(released)

    assert len(events) == 1
    assert events[0].event_type is EventType.TOUCHPAD_SWIPE
    assert events[0].control is TouchGesture.SWIPE_RIGHT
    assert events[0].value > 0.0


def test_swipe_left_is_recognized() -> None:
    recognizer = TouchGestureRecognizer()

    recognizer.generate(
        create_state(
            {
                4: TouchPoint(
                    finger_id=4,
                    x=1500,
                    y=500,
                )
            }
        )
    )

    recognizer.generate(
        create_state(
            {
                4: TouchPoint(
                    finger_id=4,
                    x=700,
                    y=510,
                )
            }
        )
    )

    events = recognizer.generate(create_state({}))

    assert len(events) == 1
    assert events[0].control is TouchGesture.SWIPE_LEFT


def test_short_touch_does_not_create_swipe() -> None:
    recognizer = TouchGestureRecognizer()

    recognizer.generate(
        create_state(
            {
                1: TouchPoint(
                    finger_id=1,
                    x=500,
                    y=500,
                )
            }
        )
    )

    recognizer.generate(
        create_state(
            {
                1: TouchPoint(
                    finger_id=1,
                    x=550,
                    y=520,
                )
            }
        )
    )

    events = recognizer.generate(create_state({}))

    assert events == []


def test_two_fingers_create_only_one_swipe() -> None:
    recognizer = TouchGestureRecognizer()

    recognizer.generate(
        create_state(
            {
                3: TouchPoint(
                    finger_id=3,
                    x=200,
                    y=250,
                ),
                4: TouchPoint(
                    finger_id=4,
                    x=700,
                    y=750,
                ),
            }
        )
    )

    recognizer.generate(
        create_state(
            {
                3: TouchPoint(
                    finger_id=3,
                    x=900,
                    y=250,
                ),
                4: TouchPoint(
                    finger_id=4,
                    x=1400,
                    y=750,
                ),
            }
        )
    )

    events = recognizer.generate(create_state({}))

    assert len(events) == 1
    assert events[0].control is TouchGesture.SWIPE_RIGHT


def test_reset_discards_unfinished_gesture() -> None:
    recognizer = TouchGestureRecognizer()

    recognizer.generate(
        create_state(
            {
                2: TouchPoint(
                    finger_id=2,
                    x=100,
                    y=300,
                )
            }
        )
    )

    recognizer.reset()

    events = recognizer.generate(create_state({}))

    assert events == []
