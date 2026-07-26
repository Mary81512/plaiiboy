from core.actions import ActionEvent
from outputs.base import Output


class DebugOutput(Output):
    def handle(self, event: ActionEvent) -> None:
        print(f"output=debug action={event.action.value:<18} value={event.value}")
