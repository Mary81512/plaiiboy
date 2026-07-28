from enum import Enum


class Layer(Enum):
    LAYER_1 = "layer_1"
    LAYER_2 = "layer_2"
    LAYER_3 = "layer_3"

    @property
    def number(self) -> int:
        return {
            Layer.LAYER_1: 1,
            Layer.LAYER_2: 2,
            Layer.LAYER_3: 3,
        }[self]

    @property
    def lightbar_color(self) -> tuple[int, int, int]:
        return {
            Layer.LAYER_1: (255, 0, 0),
            Layer.LAYER_2: (0, 255, 0),
            Layer.LAYER_3: (0, 0, 255),
        }[self]


class LayerManager:
    def __init__(self) -> None:
        self._active_layer = Layer.LAYER_1

    @property
    def active_layer(self) -> Layer:
        return self._active_layer

    def activate(self, layer: Layer) -> None:
        self._active_layer = layer

    def cycle(self) -> Layer:
        layers = list(Layer)
        current_index = layers.index(self._active_layer)
        next_index = (current_index + 1) % len(layers)

        self._active_layer = layers[next_index]
        return self._active_layer
