from dataclasses import dataclass
from .BaseObject import BaseObject


@dataclass
class _AnchorFields():
    name: str
    x: int = 0
    y: int = 0

@dataclass
class Anchor(BaseObject, _AnchorFields):
    pass
