from dataclasses import dataclass
from fontFeatures import ValueRecord
from glyphtools import get_glyph_metrics, categorize_glyph
from youseedee import ucd_data
import sys
import warnings


def _add_value_records(vr1, vr2):
    if vr1.xPlacement or vr2.xPlacement:
        vr1.xPlacement = (vr1.xPlacement or 0) + (vr2.xPlacement or 0)
    if vr1.yPlacement or vr2.yPlacement:
        vr1.yPlacement = (vr1.yPlacement or 0) + (vr2.yPlacement or 0)
    if vr1.xAdvance or vr2.xAdvance:
        vr1.xAdvance = (vr1.xAdvance or 0) + (vr2.xAdvance or 0)
    if vr1.yAdvance or vr2.yAdvance:
        vr1.yAdvance = (vr1.yAdvance or 0) + (vr2.yAdvance or 0)


@dataclass
class BufferItem:
    # codepoint: int
    # glyph: str
    # position: ValueRecord
    # category: str

    def __repr__(self):
        s = ""
        if self.glyph:
            s = self.glyph
            if self.category[0] == "base":
                s = s + "_"
            elif self.category[0] == "mark":
                s = s + "^"
            elif self.category[0] == "ligature":
                s = s + "(ﬁ)"
            else:
                s = s + "?"
        else:
            s = "U+%04x" % self.codepoint
        return "BufferItem(%s)" % s

    @classmethod
    def new_unicode(klass, codepoint):
        self = klass()
        self.codepoint = codepoint
        self.glyph = None
        self.feature_masks = {}
        return self

    @classmethod
    def new_glyph(klass, glyph, font):
        self = klass()
        self.codepoint = None
        self.glyph = glyph
        self.feature_masks = {}
        self.prep_glyph(font)
        return self

    def map_to_glyph(self, font):
        if not self.glyph:
            self.glyph = font.unicode_map.get(self.codepoint)
        if not self.glyph:
            # Notdef
            self.glyph = list(font.glyphs.keys())[0]
        self.prep_glyph(font)

    def prep_glyph(self, font):
        if "pytest" in sys.modules:
            if self.glyph in font.exportedGlyphs():
                self.gid = font.exportedGlyphs().index(self.glyph)
            else:
                self.gid = -1 # ?
        self.substituted = False
        self.ligated = False
        self.multiplied = False
        self.recategorize(font)
        try:
            self.position = ValueRecord(xAdvance=0)
            self.position.xAdvance=font.default_master.get_glyph_layer(self.glyph).width
        except Exception as e:
            if "pytest" in sys.modules:
                # We tolerate broken fonts in pytest
                pass
            else:
                raise ValueError("Could not get xAdvance for glyph %s (%i)" % (self.glyph, self.codepoint))

    def recategorize(self, font):
        try:
            self.category = categorize_glyph(font, self.glyph)
            if not self.category[0]:
                self.category = ("unknown", None)
        except Exception as e:
            warnings.warn("Error getting category: %s" % str(e))
            self._fallback_categorize()

    def _fallback_categorize(self):
        if not self.codepoint:
            # Now what?
            self.category = ("unknown", None)
            return
        genCat = ucd_data(self.codepoint).get("General_Category", "L")
        if genCat[0] == "M":
            self.category = ("mark", None)
        elif genCat == "Ll":
            self.category = ("ligature", None)
        elif genCat[0] == "L":
            self.category = ("base", None)
        else:
            self.category = ("unknown", None)

    def add_position(self, vr2):
        _add_value_records(self.position, vr2)


class Buffer:
    """A buffer holding either characters to be shaped or shaped glyphs."""
    itemclass = BufferItem

    def __init__(self, font, glyphs=[], unicodes=[], direction=None, script=None, language=None):
        self.font = font
        self.direction = direction
        self.script = script
        self.language = language
        self.fallback_mark_positioning = False
        self.fallback_glyph_classes = False
        self.items = []
        self.mask = []
        self.flags = 0
        self.current_feature_mask = None
        if glyphs:
            self.store_glyphs(glyphs)
            self.clear_mask()
        elif unicodes:
            self.store_unicode(unicodes)
            self.guess_segment_properties()

    def store_glyphs(self, glyphs):
        """Initialize the buffer with list of glyphs.

        Args:
            glyphs (list): A list of glyph names.
        """
        self.items = [self.itemclass.new_glyph(g, self.font) for g in glyphs]

    def store_unicode(self, unistring):
        """Initialize the buffer with list of Unicode codepoints.

        Args:
            glyphs (list or str): A list of characters.
        """
        self.items = [self.itemclass.new_unicode(ord(char)) for char in unistring ]

    def guess_segment_properties(self):
        """Try to automatically determine the script and direction properties."""
        for u in self.items:
            # Guess segment properties
            if not self.script:
                thisScript = ucd_data(u.codepoint)["Script"]
                if thisScript not in ["Common", "Unknown", "Inherited"]:
                    self.script = thisScript
        if not self.direction:
            from fontFeatures.shaperLib.Shaper import _script_direction
            self.direction = _script_direction(self.script)

    def map_to_glyphs(self):
        """Convert a buffer of codepoints to its initial glyph mapping."""
        glyphs = []
        for u in self.items:
            u.map_to_glyph(self.font)
        self.clear_mask()

    @property
    def is_all_glyphs(self):
        """Returns true if the contents are glyph items."""
        return all([x.glyph is not None for x in self.items])

    @property
    def is_all_unicodes(self):
        """Returns true if the contents are character items."""
        return all([x.codepoint is not None for x in self.items])

    def __getitem__(self, key):
        indexed = self.mask[key]
        if isinstance(indexed, range) or isinstance(indexed, slice):
            indexed = slice(indexed.start, indexed.stop, indexed.step)
        if isinstance(indexed, list):
            return [self.items[g] for g in indexed]
        return self.items[indexed]

    def __setitem__(self, key, value):
        indexed = self.mask[key]
        if len(indexed) == 1:  # Easy
            self.items[indexed[0] : indexed[0] + 1] = value
            return
        if len(value) == 1:  # Also easy
            self.items[indexed[0]] = value[0]
            for i in reversed(indexed[1:]):
                del self.items[i]
            return
        else:
            raise ValueError("Too hard :-(")

    def __len__(self):
        return len(self.mask)

    def update(self):
        """Categorises glyphs and recomputes masks.

        Called internally when the contents of the buffer changes."""
        for g in self.items:
            g.recategorize(self.font)
        self.recompute_mask()

    def clear_mask(self):
        """Clear the buffer mask."""
        self.flags = 0
        self.markFilteringSet = None
        self.markAttachmentSet = None
        self.current_feature_mask = None
        self.recompute_mask()

    def set_mask(self, flags, markFilteringSet=None, markAttachmentSet=None):
        """Apply a routine's flags and mark filtering set to the buffer."""
        self.flags = flags
        if self.flags & 0x10:
            assert(markFilteringSet)
        self.markFilteringSet = markFilteringSet
        if self.flags & 0xFF00:
            assert(markAttachmentSet)
        self.markAttachmentSet = markAttachmentSet
        self.recompute_mask()

    def recompute_mask(self):
        """Computes the mask property

        ``buffer.mask`` is a list of buffer item indices which is the current
        "view" of the buffer. For example, if ``buffer.flags == 0x8``, then the
        indices of all mark glyphs will be excluded from ``buffer.mask``.
        """
        mask = range(0, len(self.items))
        self.flags = self.flags or 0
        if self.flags & 0x2:  # IgnoreBases
            mask = list(filter(lambda ix: self.items[ix].category[0] != "base", mask))
        if self.flags & 0x4:  # IgnoreLigatures
            mask = list(
                filter(lambda ix: self.items[ix].category[0] != "ligature", mask)
            )
        if self.flags & 0x8:  # IgnoreMarks
            mask = list(filter(lambda ix: self.items[ix].category[0] != "mark", mask))
        if self.flags & 0x10:  # UseMarkFilteringSet
            mask = list(
                filter(
                    lambda ix: self.items[ix].category[0] != "mark"
                    or self.items[ix].glyph in self.markFilteringSet,
                    mask,
                )
            )
        if self.flags & 0xFF00:  # MarkAttachmentType
            mask = list(
                filter(
                    lambda ix: self.items[ix].category[0] != "mark"
                    or self.items[ix].glyph in self.markAttachmentSet,
                    mask,
                )
            )

        if self.current_feature_mask:
            feature = self.current_feature_mask
            mask = list(
                filter(
                    lambda ix: (feature not in self.items[ix].feature_masks)
                        or (not self.items[ix].feature_masks[feature]),
                    mask
                )
            )
        self.mask = mask

    def set_feature_mask(self, feature):
        """Applies the mask for a particular feature."""
        self.current_feature_mask = feature
        self.recompute_mask()

    def move_item(self, src, dest):
        """Moves an item from src to dest."""
        self.items[dest:dest] = [ self.items.pop(src) ]

    def merge_clusters(self, start, end):
        """Currently unimplemented."""
        pass  # XXX

    def serialize(self, additional = None, position=True, names=True, ned=False):
        """Serialize a buffer to a string.

    Returns:
        The contents of the given buffer in a string format similar to
        that used by ``hb-shape``.

    """
        outs = []
        if additional:
            if not isinstance(additional, list):
                additional = [additional]
        else:
            additional = []
        xcursor = 0
        for ix,info in enumerate(self.items):
            if hasattr(info, "glyph") and info.glyph:
                if names:
                    outs.append("%s" % info.glyph)
                else:
                    outs.append("%s" % info.gid)
            else:
                outs.append("U+%04x" % info.codepoint)
            if ned:
                position = info.position
                if xcursor + (position.xPlacement or 0):
                    outs[-1] = outs[-1] + "@%i,%i" % (xcursor + (position.xPlacement or 0), position.yPlacement or 0)
                xcursor = xcursor + position.xAdvance
            elif position and hasattr(info, "position"):
                position = info.position
                if hasattr(info, "syllable_index"):
                    cluster = info.syllable_index
                else:
                    cluster = ix
                outs[-1] = outs[-1] + "=%i" % (cluster)
                if position.xPlacement or position.yPlacement:
                    outs[-1] = outs[-1] + "@%i,%i" % (
                        position.xPlacement or 0,
                        position.yPlacement or 0,
                    )
                outs[-1] = outs[-1] + "+%i" % (position.xAdvance)
            relevant = list(filter(lambda a: hasattr(info,a), additional))
            if relevant:
                outs[-1] = outs[-1] + "(%s)" % ",".join(
                    [str(getattr(info, a)) for a in relevant]
                )
        return "|".join(outs)
