"""Routines for converting Rule objects to and from XML."""
from lxml import etree
from fontFeatures.xmlLib.utils import put_languages, put_address

@classmethod
def fromXML(klass, el):
    """Creates a Rule from a lxml Element object."""
    import fontFeatures

    subklass = getattr(fontFeatures, el.tag.title())
    assert subklass
    return subklass.fromXML(el)


def toXML(self):
    """Serializes a Rule to a lxml Element object."""
    root = etree.Element(self.__class__.__name__.lower())
    put_address(self, root)
    put_languages(self, root)
    if hasattr(self, "reverse") and self.reverse:
        root.attrib["reverse"] = "true"
    if hasattr(self, "flags") and self.flags:
        root.attrib["flags"] = str(self.flags)
    if hasattr(self, "precontext"):
        self._makeglyphslots(root, "precontext", self.precontext)
    if hasattr(self, "postcontext"):
        self._makeglyphslots(root, "postcontext", self.postcontext)
    if hasattr(self, "lookups") and self.lookups:
        wrapper = etree.SubElement(root, "lookups")
        for slot in self.lookups:
            xmlslot = etree.SubElement(wrapper, "slot")
            if slot:
                for lu in slot:
                    xmlslot.append(lu.toXML())
            else:
                etree.SubElement(xmlslot, "lookup")

    return self._toXML(root)


def _makeglyphslots(self, root, tag, list_of_lists):
    if not list_of_lists:
        return
    wrapper = etree.SubElement(root, tag)
    for slot in list_of_lists:
        xmlslot = etree.SubElement(wrapper, "slot")
        for g in slot:
            etree.SubElement(xmlslot, "glyph").text = g


def _slotArray(self, el):
    if el is None:
        return None
    return [[g.text for g in slot.findall("glyph")] for slot in list(el)]
