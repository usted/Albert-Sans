import uharfbuzz as hb
from pathlib import Path
from fontTools.ttLib import TTFont
from kurbopy import BezPath, Point, TranslateScale, Vec2, BezPathCreatingPen
from typing import NamedTuple


class Collision(NamedTuple):
    glyph1: str
    glyph2: str
    path1: BezPath
    path2: BezPath
    point: Point


def _get_sequential_cluster_ids(glyphs):
    cur_cluster = None
    sci = 0  # sequential cluster ID
    scis = []
    for g in glyphs:
        if g["cluster"] != cur_cluster:
            sci += 1
            cur_cluster = g["cluster"]
        scis.append(sci)
    return scis


def kurbo_to_skia(path):
    import pathops

    points = [(p.x, p.y) for p in path.flatten(1)]
    skiapath = pathops.Path()
    pen = skiapath.getPen()
    pen.moveTo(points[0])
    for pt in points[1:]:
        pen.lineTo(pt)
    pen.endPath()
    return skiapath


_KNOWN_RULES = ["faraway", "marks", "adjacent_clusters", "cursive", "area"]


class Collidoscope:
    """Detect collisions between font glyphs"""

    def __init__(self, fontfilename, rules, direction="LTR", location=None, scale_factor=1.0):
        """Create a collision detector.

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
            location: for variable fonts, location in the designspace as a dictionary
                (e.g. {"wght": 600})
            scale_factor: Outlines are scaled by this factor before comparison.
        """
        self.fontfilename = fontfilename
        self.glyphcache = {}
        self.direction = direction
        self.fontbinary = None
        self.scale_factor = scale_factor
        self.fontbinary = Path(fontfilename).read_bytes()
        self.ttfont = TTFont(fontfilename)
        self.glyphorder = self.ttfont.getGlyphOrder()
        self.location = location
        self.rules = rules
        self.glyphcache = {}
        self.prep_shaper()
        self.get_cursive_anchors()

    def get_beziers(self, glyph):
        pen = BezPathCreatingPen()
        self.hbfont.draw_glyph_with_pen(self.glyphorder.index(glyph), pen)
        return pen.paths

    def get_category(self, glyph):
        if "GDEF" not in self.ttfont:
            return "base"
        table = self.ttfont["GDEF"].table
        if not table.GlyphClassDef:
            return "base"
        category = table.GlyphClassDef.classDefs.get(glyph, 1)
        if category == 3:
            return "mark"
        return "base"

    def get_rules(self):
        """Return all rules that are known.

        This can be used to implement a kind of versioning of the interface
        to collidoscope.

        E.g. if the client wants to be sure that it is running against a
        version of collidoscope with the new adjacent_clusters rule,
        the client can just make sure that the adjacent_clusters rule gets
        "echoed back" or "acknowledged" by this routine.

        In practice, just the existence of this routine accomplishes the
        same version-detection for this particular adjacent_clusters feature.

        Alternately, we could use whatever the real/official mechanism is
        for versioning a Python module, presumably a 3-integer dotted SemVer?

        Version: 0.0.6 in collidoscope.egg-info/PKG-INFO?

        But this routine provides something perhaps useful beyond versioning:
        it can be used to make sure that the rules passed in don't have a typo
        in them.

        One might imagine enforcing all this in the constructor, e.g.
        throwing an exception if an unknown rule is passed in.

        But that would prevent a more gentle "use this rule if you have it"
        semantics for some future rule.
        """
        return {rk: rv for rk, rv in self.rules.items() if rk in _KNOWN_RULES}

    def prep_shaper(self):
        face = hb.Face(self.fontbinary)
        font = hb.Font(face)
        upem = face.upem
        font.scale = (upem, upem)
        hb.ot_font_set_funcs(font)
        if self.location:
            font.set_variations(self.location)
        self.hbfont = font

    def shape_a_text(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf)
        self.direction = buf.direction
        return buf

    def get_cursive_anchors(self):
        if not("cursive" in self.rules and self.rules["cursive"]):
            self.anchors = {}
            return
        # Find the GPOS CursiveAttachment lookups
        cursives = filter(
            lambda x: x.LookupType == 3, self.font["GPOS"].table.LookupList.Lookup
        )
        anchors = {}

        for c in cursives:
            # XXX This should be adjusted for variable fonts
            for s in c.SubTable:
                for glyph, record in zip(s.Coverage.glyphs, s.EntryExitRecord):
                    anchors[glyph] = []
                    if record.EntryAnchor:
                        anchors[glyph].append(
                            (
                                record.EntryAnchor.XCoordinate,
                                record.EntryAnchor.YCoordinate,
                            )
                        )
                    if record.ExitAnchor:
                        anchors[glyph].append(
                            (
                                record.ExitAnchor.XCoordinate,
                                record.ExitAnchor.YCoordinate,
                            )
                        )
        self.anchors = anchors

    def scale_path(self, p):
        centroid = p.bounding_box().center()
        out = TranslateScale.translate(Vec2(centroid.x * -1, centroid.y * -1))
        scale = TranslateScale.scale(self.scale_factor)
        in_ = TranslateScale.translate(Vec2(centroid.x, centroid.y))
        transform = out * scale * in_
        return transform * p

    def get_cached_glyph(self, name):
        if name in self.glyphcache:
            return self.glyphcache[name]
        paths = self.get_beziers(name)

        paths = [self.scale_path(p) for p in paths]
        has_anchor = False
        if paths:
            bbox = paths[0].bounding_box()
            for p in paths:
                bbox = bbox.union(p.bounding_box())
                if name in self.anchors:
                    for a in self.anchors[name]:
                        if p.winding(Point(*a)) == +1:
                            has_anchor = True
        else:
            return {
                "name": name,
                "category": self.get_category(name),
                "paths": []
            }
        self.glyphcache[name] = {
            "name": name,
            "paths": paths,
            "category": self.get_category(name),
            "has_anchor": has_anchor,
            "bbox": bbox,
        }
        return self.glyphcache[name]

    def get_positioned_glyph(self, name, pos):
        if not isinstance(pos, Point):
            pos = Point(pos.x, pos.y)
        g = self.get_cached_glyph(name)
        if not g["paths"]:
            return g
        translation = TranslateScale.translate(pos.to_vec2())

        positioned = {
            "name": g["name"],
            "paths": [translation * p for p in g["paths"]],
            "category": g["category"],
            "has_anchor": g["has_anchor"],
            "bbox": translation * g["bbox"]
        }
        return positioned

    def find_overlaps(self, g1, g2):
        rv = []
        if not g1["paths"] or not g2["paths"]:
            return []
        if g1["bbox"].intersect(g2["bbox"]).area() < 0.2:
            return rv
        for p1 in g1["paths"]:
            for p2 in g2["paths"]:
                for pt in p1.intersects(p2):
                    rv.append(Collision(glyph1=g1["name"], glyph2=g2["name"], path1=p1, path2=p2, point=pt))
        return rv

    def get_glyphs(self, text, buf=None):
        """Returns an list of dictionaries representing a shaped string.

        Args:
            text: text to check
            buf: (Optional) already shaped uharfbuzz buffer.

        This is the first step in collision detection; the dictionaries
        returned can be fed to ``draw_overlaps`` and ``has_collisions``."""
        if not buf:
            buf = self.shape_a_text(text)
        cursor = 0
        glyphs = []
        ix = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            position = Point(cursor + pos.position[0], pos.position[1])
            name = self.glyphorder[info.codepoint]
            g = self.get_positioned_glyph(name, position)
            g["cluster"] = info.cluster
            glyphs.append(g)
            ix = ix + 1
            cursor = cursor + pos.position[2]
        return glyphs

    def draw_overlaps(self, glyphs, collisions, attribs=""):
        """Return an SVG string displaying the collisions.

        Args:
            glyphs: A list of glyphs dictionaries.
            collisions: A list of Collision objects.
            attribs: String of attributes added to SVG header.
        """
        svgpaths = []
        bboxes = [ g["bbox"] for g in glyphs if "bbox" in g ]
        if not bboxes:
            return "<svg></svg>"
        bbox = bboxes[0]
        for newbox in bboxes[1:]:
            bbox = bbox.union(newbox)
        col = ["green", "red", "purple", "blue", "yellow"]
        for ix, g in enumerate(glyphs):
            for p in g["paths"]:
                svgpaths.append(
                    '<path d="%s" fill="%s"/>' % (p.to_svg(), col[ix % len(col)])
                )
        # for c in collisions:
        #     intersect = c.path1.intersection(c.path2)
        #     for i in intersect:
        #         svgpaths.append('<path d="%s" fill="black"/>' % (i.asSVGPath()))
        return '<svg %s viewBox="%i %i %i %i">%s</svg>\n' % (
            attribs,
            bbox.min_x(),
            bbox.min_y(),
            bbox.width(),
            bbox.height(),
            "\n".join(svgpaths),
        )

    def has_collisions(self, glyphs_in):
        """Run the collision detection algorithm according to the rules provided.

        Args:
            glyphs: A list of glyph dictionaries returned by ``get_glyphs``.

        Returns: A list of Collision objects.
        """
        glyphs = glyphs_in
        if self.direction == "RTL":
            glyphs = list(reversed(glyphs))

        overlaps = []
        for firstIx, first in enumerate(glyphs):
            for secondIx, second in enumerate(glyphs):
                if self.we_care_about_this_index(firstIx, secondIx, glyphs):
                    for o in self.find_overlaps(first, second):
                        if self.we_care_about_this_overlap(firstIx, secondIx, glyphs, o):
                            overlaps.append(o)
        return overlaps

    def we_care_about_this_index(self, left_ix, right_ix, glyphs):
        if right_ix == left_ix:
            return False
        left = glyphs[left_ix]
        right = glyphs[right_ix]
        if left["category"] != "mark" and right["category"] != "mark":
            if self.rules.get("bases") is False:
                return False
            if self.rules.get("bases"):
                return True

        if self.rules.get("marks"):
            if left["category"] == "mark" and right["category"] == "mark":
                return True

        if self.rules.get("faraway"):
            next_base = left_ix + 1
            while next_base < len(glyphs) and glyphs[next_base]["category"] == glyphs[left_ix]["category"]:
                next_base += 1
            if right_ix >= next_base:
                return True

        if self.rules.get("adjacent_clusters"):
            adjacency = abs(left["cluster"] - right["cluster"])
            if adjacency < 2:
                return True

        return False

    def we_care_about_this_overlap(self, firstIx, secondIx, glyphs, o):
        if self.rules.get("cursive"):
            first = glyphs[firstIx]
            second = glyphs[secondIx]
            first_has_anchors = first["has_anchor"]
            second_has_anchors = second["has_anchor"]
            if first_has_anchors and second_has_anchors:
                # if there's a base in between, these aren't anchored together
                # so we do care about them
                for i in range(firstIx+1, secondIx):
                    if glyphs[i]["category"] != "mark":
                        return True
                return False

        if self.rules.get("area"):
            # This is going to get tricky, since we now need boolean
            # operations to work out the area of the intersection
            skiapath1 = kurbo_to_skia(o.path1)
            skiapath2 = kurbo_to_skia(o.path2)
            area1 = abs(o.path1.area())
            area2 = abs(o.path2.area())

            import pathops

            result = pathops.Path()
            pathops.operations.intersection([skiapath1], [skiapath2], result.getPen())
            intersections = BezPath.fromDrawable(result)
            for i in intersections:
                ia = abs(i.area())
                # print("Intersection area: %i Path 1 area: %i Path 2 area: %i" % (ia, area1, area2))
                if (
                    ia > area1 * self.rules["area"]
                    or ia > area2 * self.rules["area"]
                ):
                    return True
            return False
        return True
