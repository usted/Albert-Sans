from dataclasses import dataclass, field
from .BaseObject import BaseObject, I18NDictionary
from .Guide import Guide

CORE_METRICS = ["xHeight", "capHeight", "ascender", "descender"]


@dataclass
class _MasterFields:
    name: I18NDictionary
    id: str = field(
        repr=False,
        metadata={
            "description": """An ID used to refer to this master in the
`Layer._master` field. (This is allows the user to change the master name
without the layers becoming lost.)"""
        },
    )
    location: dict = field(
        default=None,
        metadata={
            "description": """A dictionary mapping axis tags to coordinates
in order to locate this instance in the design space."""
        },
    )
    guides: [Guide] = field(
        default_factory=list,
        repr=False,
        metadata={"separate_items": True, "description": "A list of guides."},
    )
    metrics: dict = field(
        default_factory=dict,
        repr=False,
        metadata={
            "description": """A dictionary mapping metric names (string) to metric value (integer). The following
metric names are reserved: `%s`. Other metrics may be added to this dictionary
as needed by font clients, but their interpretation is not guaranteed to be
compatible between clients."""
            % (",".join(CORE_METRICS))
        },
    )
    kerning: dict = field( # I think I want this to be UFO-style (l,r) -> value
        default_factory=dict,
        repr=False,
        metadata={
            "separate_items": True,
            "description": "I'll be honest, I haven't worked out how this is meant to work.",
        },
    )
    font: object = field(
        default=None,
        repr=False,
        metadata={
            "python_only": True,
            "description": "Within the Python object, provides a reference to the font object containing this master.",
        },
    )


@dataclass
class Master(BaseObject, _MasterFields):
    """A font master."""

    CORE_METRICS = CORE_METRICS

    def __post_init__(self):
        super().__post_init__()
        # If they smacked my name with a bare string, replace with I18NDict
        if isinstance(self.name, str):
            self.name = I18NDictionary.with_default(self.name)

    def get_glyph_layer(self, glyphname):
        g = self.font.glyphs[glyphname]
        for layer in g.layers:
            if layer._master == self.id:
                return layer

    @property
    def normalized_location(self):
        return {a.tag: a.normalize_value(self.location[a.tag]) for a in self.font.axes}

    @property
    def xHeight(self):
        return self.metrics.get("xHeight", 0)

    @property
    def capHeight(self):
        return self.metrics.get("capHeight", 0)

    @property
    def ascender(self):
        return self.metrics.get("ascender", 0)

    @property
    def descender(self):
        return self.metrics.get("descender", 0)

    @property
    def valid(self):
        if not self.font: return False
        if self.location and list(self.location.keys()) != [n.tag for n in self.font.axes]:
            return False
        return True
