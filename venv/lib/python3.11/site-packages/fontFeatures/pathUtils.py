"""
pathUtils
=========

This is a set of simple routines to help with extracting information from
the outlines of glyphs.
"""
from beziers.path import BezierPath
from beziers.line import Line
from beziers.point import Point


def get_bezier_paths(font, glyphname):
    """Retrieve beziers from a glyph

    Args:
        font: A Babelfont font

    Returns:
        An array of ``beziers.path.BezierPath`` objects representing the
        outlines of the glyph.
    """
    layer = font.default_master.get_glyph_layer(glyphname)
    layer.decompose()
    return BezierPath.fromDrawable(layer, glyphSet = { k:font.default_master.get_glyph_layer(k)
        for k in font.exportedGlyphs()
    })


def find_largest_path(font, glyphname):
    """Find largest path by area

    Args:
        font: A fontTools ``TTFont`` object
        glyphname: The name of a single glyph

    Returns:
        A ``beziers.path.BezierPath`` object representing the largest path
        in the glyph.
    """
    paths = get_bezier_paths(font, glyphname)
    return max(paths, key=lambda p: p.area)


def thickness_at_x(path, x):
    """Find the path thickness at a given X coordinate

    This measure the thickness of the lowest horizontal stem at the given
    coordinate. If there is no stem at this X coordinate, ``None`` is
    returned.

    Args:
        path: A ``beziers.path.BezierPath`` object
        x: X coordinate to search

    Returns:
        The thickness of the path at this point, in font units.
    """
    bounds = path.bounds()
    bounds.addMargin(10)
    ray = Line(Point(x - 0.1, bounds.bottom), Point(x + 0.1, bounds.top))
    intersections = []
    for seg in path.asSegments():
        intersections.extend(seg.intersections(ray))
    if len(intersections) < 2:
        return None
    intersections = list(sorted(intersections, key=lambda i: i.point.y))
    i1, i2 = intersections[0:2]
    inorm1 = i1.seg1.normalAtTime(i1.t1)
    ray1 = Line(i1.point + (inorm1 * 1000), i1.point + (inorm1 * -1000))
    iii = i2.seg1.intersections(ray1)
    if iii:
        ll1 = i1.point.distanceFrom(iii[0].point)
    else:
        # Simple, vertical version
        return abs(i1.point.y - i2.point.y)

    inorm2 = i2.seg1.normalAtTime(i2.t1)
    ray2 = Line(i2.point + (inorm2 * 1000), i2.point + (inorm2 * -1000))
    iii = i1.seg1.intersections(ray2)
    if iii:
        ll2 = i2.point.distanceFrom(iii[0].point)
        return (ll1 + ll2) * 0.5
    else:
        return ll1

    # midpoint = (i1.point + i2.point) / 2
    # # Find closest path to midpoint
    # # Find the tangent at that time
    # inorm2 = i2.seg1.normalAtTime(i2.t1)


# from fontTools.ttLib import TTFont

# font = TTFont("fonts/Amiri-Regular.ttf")
# p = find_largest_path(font, "aHaa.medi")
# print(thickness_at_x(p, 128))
