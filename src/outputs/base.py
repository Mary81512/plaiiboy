from abc import ABC, abstractmethod

from core.actions import ActionEvent


class Output(ABC):
    @abstractmethod
    def handle(self, event: ActionEvent) -> None:
        raise NotImplementedError
