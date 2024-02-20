"""Routines for converting FontFeatures objects to and from XML."""

from lxml import etree


def toXML(self):
    """Serializes a FontFeatures object to a lxml Element object."""
    root = etree.Element("fontfeatures")
    root.append(xml_glyph_classes(self))

    routines = etree.Element("routines")
    for r in self.routines:
        routines.append(r.toXML())
    root.append(routines)

    features = etree.Element("features")
    for f, routines in self.features.items():
        f_el = etree.Element("feature")
        f_el.set("name", f)
        for r in routines:
            f_el.append(r.toXML())
        features.append(f_el)
    root.append(features)

    anchor_el = etree.Element("anchors")
    for glyph, anchors in self.anchors.items():
        glyph_el = etree.Element("glyph")
        glyph_el.set("name", glyph)
        for name, pos in anchors.items():
            a_el = etree.Element("anchor")
            a_el.set("name", name)
            a_el.set("x", str(pos[0]))
            a_el.set("y", str(pos[1]))
            glyph_el.append(a_el)
        anchor_el.append(glyph_el)
    root.append(anchor_el)

    glyphclasses = etree.Element("glyphclasses")
    for glyph, classname in self.glyphclasses.items():
        glyph_el = etree.Element("glyph")
        glyph_el.set("name", glyph)
        glyph_el.set("class", classname)
        glyphclasses.append(glyph_el)
    root.append(glyphclasses)

    return root


def xml_glyph_classes(self):
    root = etree.Element("namedclasses")
    for name, values in self.namedClasses.items():
        gc = etree.Element("class")
        gc.set("name", name)
        for g in values:
            glyph_el = etree.Element("glyph")
            glyph_el.text = g
            gc.append(glyph_el)
        root.append(gc)
    return root


@classmethod
def fromXML(klass, el):
    """Creates a FontFeatures object from a lxml Element object."""
    f = klass()
    from fontFeatures import RoutineReference, Routine

    for part in el:
        if part.tag == "namedclasses":
            for cl_el in part:
                f.namedClasses[cl_el.get("name")] = [g.text for g in cl_el]
        elif part.tag == "routines":
            f.routines = [Routine.fromXML(r) for r in part]
        elif part.tag == "features":
            for feat in part:
                f.features[feat.get("name")] = [
                    RoutineReference.fromXML(x) for x in feat
                ]
        elif part.tag == "anchors":
            for glyph in part:
                f.anchors[glyph.get("name")] = {
                    el.get("name"): (int(el.get("x")), int(el.get("y"))) for el in glyph
                }
        elif part.tag == "glyphclasses":
            for cl_el in part:
                f.glyphclasses[cl_el.get("name")] = cl_el.get("class")

    for refs in f.features.values():
        for ref in refs:
            ref.resolve(f)
    return f
