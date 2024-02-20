from dataclasses import dataclass, field
from datetime import datetime
from .BaseObject import BaseObject, OTValue, IncompatibleMastersError
from .Glyph import GlyphList
from .Axis import Axis
from .Instance import Instance
from .Master import Master
from .Names import Names
import functools
from fontTools.varLib.models import VariationModel
from fontFeatures import FontFeatures
from fontTools.feaLib.variableScalar import VariableScalar
import fontFeatures
import logging


log = logging.getLogger(__name__)

@dataclass
class _FontFields:
    upm: int = field(default=1000, metadata={"description": "The font's units per em."})
    version: (int, int) = field(
        default=(1, 0),
        metadata={
            "description": "Font version number as a tuple of integers (major, minor).",
            "json_type": "[int,int]",
        },
    )
    axes: [Axis] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of axes, in the case of variable/multiple master font. May be empty.",
        },
    )
    instances: [Instance] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of named/static instances.",
        },
    )
    masters: [Master] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of the font's masters.",
        },
    )
    glyphs: GlyphList = field(
        default_factory=GlyphList,
        metadata={
            "skip_serialize": True,
            "separate_items": True,
            "json_type": "[dict]",
            "json_location": "glyphs.json",
            "description": """A list of all glyphs supported in the font.

The `GlyphList` structure in the Python object is a dictionary with array-like
properties (or you might think of it as an array with dictionary-like properties)
containing [`Glyph`](Glyph.html) objects. The `GlyphList` may be iterated
directly, and may be appended to, but may also be used to index a `Glyph` by
its name. This is generally what you want:

```Python

for g in font.glyphs:
    assert isinstance(g, Glyph)

font.glyphs.append(newglyph)

glyph_ampersand = font.glyphs["ampersand"]
```
            """,
        },
    )
    note: str = field(
        default=None,
        metadata={"description": "Any user-defined textual note about this font."},
    )
    date: datetime = field(
        default_factory=datetime.now,
        metadata={
            "description": """The font's date. When writing to Babelfont-JSON, this
should be stored in the format `%Y-%m-%d %H:%M:%S`. *If not provided, defaults
to the current date/time*.""",
            "json_type": "str",
        },
    )
    names: Names = field(default_factory=Names, metadata={"skip_serialize": True})
    customOpenTypeValues: [OTValue] = field(
        default_factory=list,
        metadata={
            "description": "Any values to be placed in OpenType tables on export to override defaults"
        },
    )
    features: FontFeatures = field(
        default_factory=FontFeatures,
        metadata={
            "skip_serialize": True,
            "description": "A representation of the font's OpenType features",
        },
    )


@dataclass
class Font(_FontFields, BaseObject):
    """Represents a font, with one or more masters."""

    def __repr__(self):
        return "<Font '%s' (%i masters)>" % (
            self.names.familyName.get_default(),
            len(self.masters),
        )

    def save(self, filename, **kwargs):
        from .convertors import Convert

        return Convert(filename).save(self, **kwargs)

    def master(self, mid):
        return self._master_map[mid]

    def map_forward(self, location):
        location2 = dict(location)
        for a in self.axes:
            if a.tag in location2:
                location2[a.tag] = a.map_forward(location2[a.tag])
        return location2

    def map_backward(self, location):
        location2 = dict(location)
        for a in self.axes:
            if a.tag in location2:
                location2[a.tag] = a.map_backward(location2[a.tag])
        return location2

    @functools.cached_property
    def default_master(self):
        default_loc = {a.tag: a.map_forward(a.default) for a in self.axes}
        for m in self.masters:
            if m.location == default_loc:
                return m
        if len(self.masters) == 1:
            return self.masters[0]
        raise ValueError("Could not determine default master")

    @functools.cached_property
    def _master_map(self):
        return {m.id: m for m in self.masters}

    @functools.cached_property
    def unicode_map(self):
        unicodes = {}
        for g in self.glyphs:
            if not g.codepoints:
                continue
            for u in g.codepoints:
                if u:
                    unicodes[u] = g.name
        return unicodes

    def variation_model(self):
        return VariationModel(
            [m.normalized_location for m in self.masters],
            axisOrder=[a.tag for a in self.axes],
        )

    @functools.cached_property
    def _all_kerning(self):
        all_keys = [set(m.kerning.keys()) for m in self.masters]
        kerndict = {}
        for (l, r) in list(set().union(*all_keys)):
            kern = VariableScalar()
            kern.axes = self.axes
            for m in self.masters:
                thiskern = m.kerning.get((l, r), 0)
                if (l, r) not in m.kerning:
                    log.debug(
                        "Master %s did not define a kern pair for (%s, %s), using 0"
                        % (m.name.get_default(), l, r)
                    )
                kern.add_value(m.location, thiskern)
            kerndict[(l, r)] = kern
        return kerndict

    @functools.cached_property
    def _all_anchors(self):
        _all_anchors_dict = {}
        for g in sorted(self.glyphs.keys()):
            default_layer = self.default_master.get_glyph_layer(g)
            has_mark = None
            for a in default_layer.anchors_dict.keys():
                if a[0] == "_":
                    if has_mark:
                        log.warning("Glyph %s tried to be in two mark classes (%s, %s). The first one will win." % (g, has_mark, a))
                        continue
                    has_mark = a
                if not a in _all_anchors_dict:
                    _all_anchors_dict[a] = {}
                _all_anchors_dict[a][g] = self.get_variable_anchor(g, a)
        return _all_anchors_dict

    def get_variable_anchor(self, glyph, anchorname):
        x_vs = VariableScalar()
        x_vs.axes = self.axes
        y_vs = VariableScalar()
        y_vs.axes = self.axes
        for ix, m in enumerate(self.masters):
            layer = m.get_glyph_layer(glyph)
            if anchorname not in layer.anchors_dict:
                raise IncompatibleMastersError(
                    "Anchor %s not found on glyph %s in master %s"
                    % (anchorname, glyph, m)
                )
            anchor = m.get_glyph_layer(glyph).anchors_dict[anchorname]
            x_vs.add_value(self.map_forward(m.location), anchor.x)
            y_vs.add_value(self.map_forward(m.location), anchor.y)
        return (x_vs, y_vs)

    def exportedGlyphs(self):
        return [g.name for g in self.glyphs if g.exported]
