from dataclasses import dataclass
from .BaseObject import BaseObject, Color, Position


@dataclass
class _GuideFields:
    pos: Position
    name: str = None
    color: Color = None

@dataclass
class Guide(BaseObject, _GuideFields):
    pass
