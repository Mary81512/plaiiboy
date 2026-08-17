from core.action_processor import ActionProcessor
from core.actions import Action, ActionEvent
from core.events import (
    Button,
    ControllerEvent,
    EventType,
    TouchGesture,
)
from core.performance_state import Deck


def create_action_event(
    action: Action,
    value: float = 1.0,
) -> ActionEvent:
    source_event = ControllerEvent(
        event_type=EventType.BUTTON_PRESSED,
        control=Button.CROSS,
        value=value,
    )

    return ActionEvent(
        action=action,
        value=value,
        source_event=source_event,
    )


def create_swipe_action_event(
    action: Action,
    value: float,
) -> ActionEvent:
    source_event = ControllerEvent(
        event_type=EventType.TOUCHPAD_SWIPE,
        control=TouchGesture.SWIPE_RIGHT,
        value=value,
    )

    return ActionEvent(
        action=action,
        value=value,
        source_event=source_event,
    )


def test_active_deck_starts_as_deck_1() -> None:
    processor = ActionProcessor()

    assert processor.state.active_deck is Deck.DECK_1


def test_toggle_active_deck_changes_state() -> None:
    processor = ActionProcessor()

    events = processor.process(create_action_event(Action.TOGGLE_ACTIVE_DECK))

    assert processor.state.active_deck is Deck.DECK_2
    assert len(events) == 1
    assert events[0].action is Action.FEEDBACK_ACTIVE_DECK_2


def test_active_hotcue_resolves_to_deck_1() -> None:
    processor = ActionProcessor()

    events = processor.process(create_action_event(Action.ACTIVE_DECK_HOTCUE_TOGGLE))

    assert len(events) == 1
    assert events[0].action is Action.DECK_1_HOTCUE_TOGGLE


def test_active_hotcue_resolves_to_deck_2() -> None:
    processor = ActionProcessor()

    processor.process(create_action_event(Action.TOGGLE_ACTIVE_DECK))

    events = processor.process(create_action_event(Action.ACTIVE_DECK_HOTCUE_TOGGLE))

    assert len(events) == 1
    assert events[0].action is Action.DECK_2_HOTCUE_TOGGLE


def test_seek_uses_active_deck() -> None:
    processor = ActionProcessor()

    events = processor.process(
        create_swipe_action_event(
            Action.ACTIVE_DECK_SEEK_FORWARD,
            value=0.8,
        )
    )

    assert events
    assert all(event.action is Action.DECK_1_SEEK_FINE_FORWARD for event in events)


def test_seek_mode_changes_mapped_action() -> None:
    processor = ActionProcessor()

    slow_events = processor.process(
        create_swipe_action_event(
            Action.ACTIVE_DECK_SEEK_FORWARD,
            value=1.0,
        )
    )

    processor.process(create_action_event(Action.CYCLE_SEEK_SPEED))

    faster_events = processor.process(
        create_swipe_action_event(
            Action.ACTIVE_DECK_SEEK_FORWARD,
            value=1.0,
        )
    )

    assert [event.action for event in slow_events] == [
        Action.DECK_1_SEEK_FINE_FORWARD,
    ]
    assert [event.action for event in faster_events] == [
        Action.DECK_1_SEEK_4_BARS_FORWARD,
    ]
