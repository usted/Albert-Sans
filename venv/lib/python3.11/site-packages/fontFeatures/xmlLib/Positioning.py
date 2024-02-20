"""Routines for converting Positioning rules to and from XML."""

from lxml import etree
from fontFeatures import ValueRecord

# We can't monkeypatch this, because it's not our class.
def _valuerecord_fromXML(el):
    v = ValueRecord()
    for part in ["xPlacement", "yPlacement", "xAdvance", "yAdvance"]:
        if el.get(part):
            setattr(v, part, int(el.get(part)))
    return v


def _valuerecord_toXML(v):
    el = etree.Element("valuerecord")
    for part in ["xPlacement", "yPlacement", "xAdvance", "yAdvance"]:
        if getattr(v, part):
            el.set(part, str(getattr(v, part)))
    return el


def _toXML(self, root):
    self._makeglyphslots(root, "glyphs", self.glyphs)
    wrapper = etree.SubElement(root, "positions")
    for p in self.valuerecords:
        wrapper.append(_valuerecord_toXML(p))
    return root


@classmethod
def fromXML(klass, el):
    """Creates a rule from a lxml Element object."""
    position = el.find("positions")
    positions = [_valuerecord_fromXML(x) for x in position.findall("valuerecord")]
    rule = klass(
        klass._slotArray(klass, el.find("glyphs")),
        positions,
        precontext=klass._slotArray(klass, el.find("precontext")),
        postcontext=klass._slotArray(klass, el.find("postcontext")),
        address=el.get("address"),
        languages=el.get("languages"),
        flags=el.get("flags"),
    )
    if el.find("lookups"):
        rule.lookups = []
        for slot in list(el):
            routines = [Routine.fromXML(x) for x in slot.findall("routine")]
            rule.lookups.append(routines)

    return rule
