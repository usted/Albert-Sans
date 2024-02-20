"""Routines for converting Attachment rules to and from XML."""

from lxml import etree


def _toXML(self, root):
    root.set("basename", self.base_name)
    root.set("markname", self.mark_name)
    for n, anchor in self.bases.items():
        base = etree.SubElement(root, "base")
        base.set("name", n)
        base.set("anchorX", str(anchor[0]))
        base.set("anchorY", str(anchor[1]))
    for n, anchor in self.marks.items():
        mark = etree.SubElement(root, "mark")
        mark.set("name", n)
        mark.set("anchorX", str(anchor[0]))
        mark.set("anchorY", str(anchor[1]))
    return root


@classmethod
def fromXML(klass, el):
    """Creates a rule from a lxml Element object."""
    rule = klass(
        base_name = el.get("basename"),
        mark_name = el.get("markname"),
        address=el.get("address"),
        flags=int(el.get("flags") or 0),
    )
    for baseormark in el:
        key = baseormark.get("name")
        value = (int(baseormark.get("anchorX")), int(baseormark.get("anchorY")))
        if baseormark.tag == "base":
            rule.bases[key] = value
        elif baseormark.tag == "mark":
            rule.marks[key] = value
    return rule
