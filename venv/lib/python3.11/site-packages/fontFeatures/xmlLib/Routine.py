"""Routines for converting Routine objects to and from XML."""
from lxml import etree
from fontFeatures.xmlLib.utils import put_languages, put_address


def toXML(self):
    """Serializes a Routine to a lxml Element object."""
    root = etree.Element("routine")
    if self.flags:
        root.attrib["flags"] = str(self.flags)
    put_address(self, root)
    put_languages(self, root)
    if self.name:
        root.attrib["name"] = self.name
    for r in self.rules:
        root.append(r.toXML())

    return root


@classmethod
def fromXML(klass, el):
    """Creates a Routine from a lxml Element object."""
    from fontFeatures import Rule

    rule = klass(
        address=(el.get("address") or "").split("|"), name=el.get("name"), flags=(int(el.get("flags") or 0))
    )
    for r in el:
        rule.addRule(Rule.fromXML(r))
    return rule
