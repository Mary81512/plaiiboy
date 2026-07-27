from controller.event_generator import EventGenerator
from controller.state import ControllerState
from core.events import Axis, Button, EventType


def create_state(
    buttons: frozenset[Button] = frozenset(),
    axes: dict[Axis, float] | None = None,
) -> ControllerState:
    return ControllerState(
        buttons=buttons,
        axes=axes if axes is not None else {},
        touches={},
    )


def test_button_press_and_release() -> None:
    generator = EventGenerator()

    generator.generate(create_state())

    pressed_events = generator.generate(
        create_state(
            buttons=frozenset({Button.CROSS}),
        )
    )

    assert any(
        event.event_type is EventType.BUTTON_PRESSED and event.control is Button.CROSS
        for event in pressed_events
    )

    released_events = generator.generate(create_state())

    assert any(
        event.event_type is EventType.BUTTON_RELEASED and event.control is Button.CROSS
        for event in released_events
    )

    assert any(
        event.event_type is EventType.BUTTON_SHORT_PRESSED
        and event.control is Button.CROSS
        for event in released_events
    )


def test_axis_positive_threshold_triggers_once() -> None:
    generator = EventGenerator()

    neutral_axes = {
        Axis.LEFT_X: 0.0,
    }

    generator.generate(create_state(axes=neutral_axes))

    first_events = generator.generate(
        create_state(
            axes={
                Axis.LEFT_X: 1.0,
            }
        )
    )

    second_events = generator.generate(
        create_state(
            axes={
                Axis.LEFT_X: 1.0,
            }
        )
    )

    assert any(
        event.event_type is EventType.AXIS_POSITIVE_TRIGGERED for event in first_events
    )

    assert not any(
        event.event_type is EventType.AXIS_POSITIVE_TRIGGERED for event in second_events
    )


def test_axis_latch_resets_after_return_to_center() -> None:
    generator = EventGenerator()

    generator.generate(
        create_state(
            axes={
                Axis.LEFT_X: 0.0,
            }
        )
    )

    generator.generate(
        create_state(
            axes={
                Axis.LEFT_X: 1.0,
            }
        )
    )

    generator.generate(
        create_state(
            axes={
                Axis.LEFT_X: 0.0,
            }
        )
    )

    events = generator.generate(
        create_state(
            axes={
                Axis.LEFT_X: 1.0,
            }
        )
    )

    assert any(
        event.event_type is EventType.AXIS_POSITIVE_TRIGGERED for event in events
    )


def test_reset_discards_previous_state() -> None:
    generator = EventGenerator()

    generator.generate(create_state())

    generator.generate(
        create_state(
            buttons=frozenset({Button.CIRCLE}),
        )
    )

    generator.reset()

    events = generator.generate(
        create_state(
            buttons=frozenset({Button.CIRCLE}),
        )
    )

    assert events == []
