"""Routines for converting RoutineReference objects to and from XML."""
from lxml import etree


def toXML(self):
    """Serializes a RoutineReference to a lxml Element object."""
    root = etree.Element("routinereference")
    if self.name:
        root.attrib["name"] = self.name
    return root


@classmethod
def fromXML(klass, el):
    """Creates a RoutineReference from a lxml Element object."""
    rule = klass(name=el.get("name"))
    id = el.get("id")
    return rule
