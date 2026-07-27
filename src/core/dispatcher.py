from core.actions import ActionEvent
from outputs.base import Output


class Dispatcher:
    """
    Verteilt verarbeitete ActionEvents an alle registrierten Outputs.

    Bei aktiviertem Debug-Modus wird jedes ActionEvent vor der
    Weiterleitung im Terminal ausgegeben.
    """

    def __init__(
        self,
        debug: bool = True,
    ) -> None:
        self._outputs: list[Output] = []
        self._debug = debug

    def add_output(
        self,
        output: Output,
    ) -> None:
        self._outputs.append(output)

    def dispatch(
        self,
        event: ActionEvent,
    ) -> None:
        if self._debug:
            self._print_event(event)

        for output in self._outputs:
            output.handle(event)

    def _print_event(
        self,
        event: ActionEvent,
    ) -> None:
        source = event.source_event

        source_control = getattr(
            source.control,
            "name",
            str(source.control),
        )

        print(
            "[DISPATCH] "
            f"{event.action.name} "
            f"| value={event.value:.3f} "
            f"| source={source.event_type.name} "
            f"| control={source_control}"
        )

    def close(self) -> None:
        for output in self._outputs:
            output.close()
