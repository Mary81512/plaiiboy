from enum import Enum


class Layer(Enum):
    DEFAULT = "default"


class LayerManager:
    def __init__(self) -> None:
        self._active_layer = Layer.DEFAULT

    @property
    def active_layer(self) -> Layer:
        return self._active_layer

    def activate(self, layer: Layer) -> None:
        self._active_layer = layer
