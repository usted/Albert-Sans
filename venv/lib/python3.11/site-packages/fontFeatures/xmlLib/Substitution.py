"""Routines for converting Substitution rules to and from XML."""
from lxml import etree

def _toXML(self, root):
  self._makeglyphslots(root, "from", self.input)
  self._makeglyphslots(root, "to", self.replacement)
  return root

@classmethod
def fromXML(klass, el):
  """Creates a rule from a lxml Element object."""
  rule = klass(
      klass._slotArray(klass, el.find("from")),
      klass._slotArray(klass, el.find("to")),
      precontext = klass._slotArray(klass, el.find("precontext")),
      postcontext = klass._slotArray(klass, el.find("postcontext")),
      address = el.get("address"),
      languages = el.get("languages"),
      reverse = el.get("reverse"),
      flags = el.get("flags")
  )
  if el.find("lookups"):
    rule.lookups = []
    for slot in list(el):
      routines = [Routine.fromXML(x) for x in slot.findall("routine")]
      rule.lookups.append(routines)
  return rule
