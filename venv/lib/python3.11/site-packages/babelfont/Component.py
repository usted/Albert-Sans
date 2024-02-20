from dataclasses import dataclass
from .BaseObject import BaseObject


@dataclass
class Component(BaseObject):
    name: str
    position: list = None
    transform: list = None

    _serialize_slots = ["name", "transform"]
