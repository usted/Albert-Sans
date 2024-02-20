from dataclasses import dataclass
from .BaseObject import BaseObject
from fontTools.misc.transform import Transform
from .Node import Node
import math


@dataclass
class _ShapeFields:
    ref: str = None
    transform: Transform = None
    nodes: [Node] = None
    closed: bool = True
    direction: int = 1

    _layer = None

@dataclass
class Shape(BaseObject, _ShapeFields):
    @property
    def _write_one_line(self):
        return self.is_component

    @property
    def is_path(self):
        return not bool(self.ref)

    @property
    def is_component(self):
        return bool(self.ref)

    @property
    def component_layer(self):
        if not self.is_component:
            return None
        return self._layer.master.get_glyph_layer(self.ref)

    @property
    def pos(self):
        assert self.is_component
        if not self.transform:
            return (0,0)
        return tuple(self.transform[4:])

    @property
    def angle(self):
        assert self.is_component
        if not self.transform:
            return 0
        return math.atan2(self.transform[1], self.transform[0]) * 180 / math.pi

    @property
    def scale(self):
        assert self.is_component
        if not self.transform:
            return (1,1)
        print(self.transform)
        scaleX = math.sqrt(self.transform[0] ** 2 + self.transform[2] ** 2)
        scaleY = math.sqrt(self.transform[1] ** 2 + self.transform[3] ** 2)
        return (scaleX, scaleY)
