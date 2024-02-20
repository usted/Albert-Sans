from fontFeatures import Attachment, Routine, Positioning, ValueRecord
import logging


log = logging.getLogger(__name__)


def build_all_features(font, ttFont):
    build_cursive(font)
    build_mark_mkmk(font)
    build_mark_mkmk(font, "mkmk")
    build_kern(font)

    font.features.buildBinaryFeatures(ttFont, font.axes)


def build_kern(font):
    def _expand_class(c):
        if c[0] != "@":
            return [c]
        if c[1:] not in font.features.namedClasses:
            logging.info("Attempted to use undefined kerning class %s" % c)
            return None
        return [x for x in font.features.namedClasses[c[1:]] if font.glyphs[x].exported]

    kernroutine = Routine()
    for (l,r), kern in font._all_kerning.items():
        l, r = _expand_class(l), _expand_class(r)
        if l is None or r is None:
            continue
        kernroutine.rules.append(Positioning(
            [ l, r ],
            [ ValueRecord(xAdvance=kern), ValueRecord() ],
        ))
    font.features.addFeature("kern", [kernroutine])


def build_cursive(font):
    anchors = font._all_anchors
    if "entry" in anchors and "exit" in anchors:
        attach = Attachment(
            "entry", "exit", anchors["entry"], anchors["exit"],
            flags=(0x8 | 0x1)
        )
        r = Routine(rules=[attach], )
        font.features.addFeature("curs", [r])

def build_mark_mkmk(font, which="mark", strict=False):
    # Find matching pairs of foo/_foo anchors
    anchors = font._all_anchors
    r = Routine(rules=[])
    if which == "mark":
        basecategory = "base"
    else:
        basecategory = "mark"
    for baseanchor in anchors:
        markanchor = "_" + baseanchor
        if markanchor not in anchors:
            continue
        # Filter glyphs to those which are baseanchors
        bases = {
            k: v
            for k, v in anchors[baseanchor].items()
            if font.glyphs[k].exported and (font.glyphs[k].category == basecategory)
        }
        marks = {
            k: v
            for k, v in anchors[markanchor].items()
            if font.glyphs[k].exported and (not strict or font.glyphs[k].category == "mark")
        }
        if not (bases and marks):
            continue
        attach = Attachment(baseanchor, markanchor, bases, marks)
        attach.fontfeatures = font.features  # THIS IS A TERRIBLE HACK
        r.rules.append(attach)
    if r.rules:
        font.features.addFeature(which, [r])
