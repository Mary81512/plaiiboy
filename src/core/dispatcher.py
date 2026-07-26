from core.actions import ActionEvent
from outputs.base import Output


class Dispatcher:
    def __init__(self) -> None:
        self._outputs: list[Output] = []

    def add_output(self, output: Output) -> None:
        self._outputs.append(output)

    def dispatch(self, event: ActionEvent) -> None:
        for output in self._outputs:
            output.handle(event)
