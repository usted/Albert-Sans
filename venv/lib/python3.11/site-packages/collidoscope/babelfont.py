from . import Collidoscope as BaseCollidoscope
from babelfont import load, Font
from kurbopy import BezPath


class Collidoscope(BaseCollidoscope):
    def __init__(
        self,
        fontfilename,
        rules,
        direction="LTR",
        master=None,
        scale_factor=1.0,
        babelfont=None,
    ):
        """Create a collision detector (using Babelfont)

        The rules dictionary may contain the following entries:
            faraway (boolean): If true, non-adjacent base glyphs are tested for
                overlap. Mark glyphs are ignored. All collisions are reported.
            marks (boolean): If true, collisions between all pairs of marks in
                the string are reported.
            bases (boolean): If *false*, collisions between all pairs of bases in
                the string are *ignored*.
            adjacent_clusters (boolean): If true, collisions between all pairs
                of glyphs in adjacent clusters are reported.
            cursive (boolean): If true, adjacent glyphs are tested for overlap.
                Paths containing cursive anchors are allowed to overlap, but
                collisions between other paths are reported.
            area (float): If provided, adjacent glyphs are tested for overlap.
                Collisions are reported if the intersection area is greater than
                the given proportion of the smallest path. (i.e. where cursive
                connection anchors are not used in an Arabic font, you may wish
                to ignore collisions if the overlaid area is less than 5% of the
                smallest path, because this is likely to be the connection point
                between the glyphs. But collisions affecting more than 5% of the
                glyph will be reported.)

        Args:
            fontfilename: file name of font.
            rules: dictionary of collision rules.
            direction: "LTR" or "RTL"
            master: master name
            scale_factor: Outlines are scaled by this factor before comparison.
        """
        self.fontfilename = fontfilename
        self.glyphcache = {}
        self.direction = direction
        self.fontbinary = None
        self.scale_factor = scale_factor
        if isinstance(fontfilename, Font):
            self.font = fontfilename
        else:
            self.font = load(str(fontfilename))
        self.glyphorder = [g.name for g in self.font.glyphs]
        self.rules = rules
        self.glyphcache = {}
        self.anchors = {}
        if babelfont:
            raise ValueError(
                "Supplying a babelfont object is deprecated;"
                " instead, use the collidoscope.babelfont module"
            )
        if master:
            masters = [m for m in self.font.masters if m.name.get_default() == master]
            if not masters:
                raise ValueError("Could not find a master called %s" % master)
            self.master = masters[0]
        else:
            self.master = self.font.default_master
        self.glyphset = {
            k: self.master.get_glyph_layer(k) for k in self.font.glyphs.keys()
        }

    def get_beziers(self, glyph):
        layer = self.glyphset[glyph]
        rv = BezPath.fromDrawable(layer, self.glyphset)
        return rv

    def get_category(self, glyph):
        return self.font.glyphs[glyph].category

    def shape_a_text(self, text):
        raise ValueError(
            "text shaping is not implemented in collidoscope.babelfont"
            "; either use a pre-computed buffer or supply glyphs positions explicitly."
        )

    def get_cursive_anchors(self):
        raise ValueError("Currently unimplemented")
