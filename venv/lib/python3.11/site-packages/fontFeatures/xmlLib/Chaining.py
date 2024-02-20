"""Routines for converting Chaining rules to and from XML."""

from lxml import etree


def _toXML(self, root):
    self._makeglyphslots(root, "input", self.input)
    return root


@classmethod
def fromXML(klass, el):
  """Creates a rule from a lxml Element object."""
  from fontFeatures import Routine, RoutineReference
  rule = klass(
      klass._slotArray(klass, el.find("input")),
      precontext = klass._slotArray(klass, el.find("precontext")),
      postcontext = klass._slotArray(klass, el.find("postcontext")),
      address = el.get("address"),
      languages = el.get("languages"),
      flags = int(el.get("flags") or 0)
  )
  lookupsxml = el.find("lookups")
  rule.lookups = []
  for slot in lookupsxml:
    routines = []
    for lu in slot:
        if lu.tag == "routinereference":
            routines.append(RoutineReference.fromXML(lu))
        elif lu.tag == "routine":
            routines.append(Routine.fromXML(lu))
    rule.lookups.append(routines)
  return rule
