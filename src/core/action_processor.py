from collections.abc import Callable

from core.actions import Action, ActionEvent
from core.performance_state import BrowserFocus, Deck, PerformanceState

ActionHandler = Callable[
    [ActionEvent],
    list[ActionEvent],
]


class ActionProcessor:
    def __init__(
        self,
        state: PerformanceState | None = None,
    ) -> None:
        self._state = state if state is not None else PerformanceState()

        self._handlers: dict[
            Action,
            ActionHandler,
        ] = {
            Action.TOGGLE_ACTIVE_DECK: self._toggle_active_deck,
            Action.CYCLE_SEEK_SPEED: self._cycle_seek_speed,
            Action.ACTIVE_DECK_SEEK_BACKWARD: self._seek_backward,
            Action.ACTIVE_DECK_SEEK_FORWARD: self._seek_forward,
            Action.BROWSER_UP: self._browser_up,
            Action.BROWSER_DOWN: self._browser_down,
            Action.BROWSER_LEVEL_UP: self._browser_level_up,
            Action.BROWSER_LEVEL_DOWN: self._browser_level_down,
        }

    @property
    def state(self) -> PerformanceState:
        return self._state

    def process(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        handler = self._handlers.get(event.action)

        if handler is not None:
            return handler(event)

        resolved_action = self._resolve_active_deck_action(event.action)

        if resolved_action is None:
            return [event]

        return [
            self._replace_action(
                event=event,
                action=resolved_action,
            )
        ]

    def _toggle_active_deck(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        active_deck = self._state.toggle_active_deck()

        feedback_action = (
            Action.FEEDBACK_ACTIVE_DECK_1
            if active_deck is Deck.DECK_1
            else Action.FEEDBACK_ACTIVE_DECK_2
        )

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

    def _browser_up(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = (
            Action.BROWSER_TREE_UP
            if self._state.browser_focus is BrowserFocus.TREE
            else Action.BROWSER_LIST_UP
        )

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _browser_down(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = (
            Action.BROWSER_TREE_DOWN
            if self._state.browser_focus is BrowserFocus.TREE
            else Action.BROWSER_LIST_DOWN
        )

        return [
            self._replace_action(
                event=event,
                action=action,
            )
        ]

    def _browser_level_down(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        if self._state.browser_focus is BrowserFocus.LIST:
            return []

        self._state.set_browser_focus(BrowserFocus.LIST)

        return [
            self._replace_action(
                event=event,
                action=Action.BROWSER_TREE_EXPAND,
            )
        ]

    def _browser_level_up(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        if self._state.browser_focus is BrowserFocus.LIST:
            self._state.set_browser_focus(BrowserFocus.TREE)
            return []

        return [
            self._replace_action(
                event=event,
                action=Action.BROWSER_TREE_COLLAPSE,
            )
        ]

    def _seek_backward(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = (
            Action.DECK_1_SEEK_BACKWARD
            if self._state.active_deck is Deck.DECK_1
            else Action.DECK_2_SEEK_BACKWARD
        )

        return self._create_seek_pulses(
            event=event,
            action=action,
        )

    def _seek_forward(
        self,
        event: ActionEvent,
    ) -> list[ActionEvent]:
        action = (
            Action.DECK_1_SEEK_FORWARD
            if self._state.active_deck is Deck.DECK_1
            else Action.DECK_2_SEEK_FORWARD
        )

        return self._create_seek_pulses(
            event=event,
            action=action,
        )

    def _create_seek_pulses(
        self,
        event: ActionEvent,
        action: Action,
    ) -> list[ActionEvent]:
        pulse_count = max(
            1,
            round(event.value * self._state.seek_speed),
        )

        return [
            ActionEvent(
                action=action,
                value=1.0,
                source_event=event.source_event,
            )
            for _ in range(pulse_count)
        ]

    def _resolve_active_deck_action(
        self,
        action: Action,
    ) -> Action | None:
        if self._state.active_deck is Deck.DECK_1:
            mappings = {
                Action.ACTIVE_DECK_HOTCUE_PREVIOUS: Action.DECK_1_HOTCUE_PREVIOUS,
                Action.ACTIVE_DECK_HOTCUE_NEXT: Action.DECK_1_HOTCUE_NEXT,
                Action.ACTIVE_DECK_HOTCUE_TOGGLE: Action.DECK_1_HOTCUE_TOGGLE,
            }
        else:
            mappings = {
                Action.ACTIVE_DECK_HOTCUE_PREVIOUS: Action.DECK_2_HOTCUE_PREVIOUS,
                Action.ACTIVE_DECK_HOTCUE_NEXT: Action.DECK_2_HOTCUE_NEXT,
                Action.ACTIVE_DECK_HOTCUE_TOGGLE: Action.DECK_2_HOTCUE_TOGGLE,
            }

        return mappings.get(action)

    def _replace_action(
        self,
        event: ActionEvent,
        action: Action,
    ) -> ActionEvent:
        return ActionEvent(
            action=action,
            value=event.value,
            source_event=event.source_event,
        )
