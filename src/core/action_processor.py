from core.actions import Action, ActionEvent
from core.performance_state import Deck, PerformanceState


class ActionProcessor:
    def __init__(
        self,
        state: PerformanceState | None = None,
    ) -> None:
        self._state = state if state is not None else PerformanceState()

    @property
    def state(self) -> PerformanceState:
        return self._state

    def process(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        if event.action is Action.TOGGLE_ACTIVE_DECK:
            return self._toggle_active_deck(event)

        if event.action is Action.CYCLE_SEEK_SPEED:
            return self._cycle_seek_speed(event)

        resolved_action = self._resolve_active_deck_action(event.action)

        if resolved_action is None:
            return [event]

        return [
            ActionEvent(
                action=resolved_action,
                value=event.value,
                source_event=event.source_event,
            )
        ]

    def _toggle_active_deck(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        active_deck = self._state.toggle_active_deck()

        if active_deck is Deck.DECK_1:
            feedback_action = Action.FEEDBACK_ACTIVE_DECK_1
        else:
            feedback_action = Action.FEEDBACK_ACTIVE_DECK_2

        return [
            ActionEvent(
                action=feedback_action,
                value=float(active_deck.value),
                source_event=event.source_event,
            )
        ]

    def _cycle_seek_speed(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        seek_speed = self._state.cycle_seek_speed()

        return [
            ActionEvent(
                action=Action.CYCLE_SEEK_SPEED,
                value=float(seek_speed),
                source_event=event.source_event,
            )
        ]

    def _resolve_active_deck_action(
        self,
        action: Action,
    ) -> Action | None:
        if self._state.active_deck is Deck.DECK_1:
            deck_mappings = {
                Action.ACTIVE_DECK_HOTCUE_PREVIOUS: Action.DECK_1_HOTCUE_PREVIOUS,
                Action.ACTIVE_DECK_HOTCUE_NEXT: Action.DECK_1_HOTCUE_NEXT,
                Action.ACTIVE_DECK_HOTCUE_TOGGLE: Action.DECK_1_HOTCUE_TOGGLE,
            }
        else:
            deck_mappings = {
                Action.ACTIVE_DECK_HOTCUE_PREVIOUS: Action.DECK_2_HOTCUE_PREVIOUS,
                Action.ACTIVE_DECK_HOTCUE_NEXT: Action.DECK_2_HOTCUE_NEXT,
                Action.ACTIVE_DECK_HOTCUE_TOGGLE: Action.DECK_2_HOTCUE_TOGGLE,
            }

        return deck_mappings.get(action)
