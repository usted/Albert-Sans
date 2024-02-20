from .BaseObject import BaseObject, I18NDictionary
from dataclasses import dataclass, field
import uuid
from fontTools.varLib.models import normalizeValue


@dataclass
class _AxisFields:
    name: I18NDictionary = field(
        metadata={"description": "The display name for this axis."}
    )
    tag: str = field(metadata={"description": "The four-letter axis tag."})
    id: str = field(
        default_factory=lambda: str(uuid.uuid1()),
        repr=False,
        metadata={
            "description": """An ID used to refer to this axis in the Master,
Layer and Instance `location` fields. (This is allows the user to change the
axis tag without the locations becoming lost.) If not provided, one will be
automatically generated on import from a UUID."""
        },
    )
    min: int = field(
        default=None,
        metadata={
            "description": "The minimum value of this axis, in user space coordinates."
        },
    )
    max: int = field(
        default=None,
        metadata={
            "description": "The maximum value of this axis, in user space coordinates."
        },
    )
    default: int = field(
        default=None,
        metadata={
            "description": """The default value of this axis (center of interpolation),
in user space coordinates. Note that if the min/max/default values are not supplied,
they are returned as `None` in the Python object, and should be computed from the
master locations on export."""
        },
    )
    map: [(int, int)] = field(
        default=None,
        metadata={
            "description": """The mapping between userspace and designspace coordinates."""
        },
    )


@dataclass
class Axis(BaseObject, _AxisFields):
    """Represents an axis in a multiple master or variable font."""

    _write_one_line = True

    def __post_init__(self):
        # If they smacked my name with a bare string, replace with I18NDict
        if isinstance(self.name, str):
            self.name = I18NDictionary.with_default(self.name)
        super().__post_init__()

    def normalize_value(self, value):
        return normalizeValue(
            value, (self.map_forward(self.min), self.map_forward(self.default), self.map_forward(self.max))
        )

    def denormalize_value(self, value):
        if value == 0:
            return self.default
        elif value > 0:
            return self.default + (self.max - self.default) * value
        else:
            return self.default + (self.default - self.min) * value

    # Compatibility with designspaceLib. Our names are smaller for serialization.
    @property
    def maximum(self):
        return self.max

    @property
    def minimum(self):
        return self.min

    # Compatibility with fontTools.varLib
    @property
    def maxValue(self):
        return self.max

    @property
    def minValue(self):
        return self.min

    @property
    def axisTag(self):
        return self.tag

    @property
    def defaultValue(self):
        return self.default

    # Stolen from fontTools.designspaceLib

    def map_forward(self, v):
        from fontTools.varLib.models import piecewiseLinearMap

        if not self.map:
            return v
        return piecewiseLinearMap(v, {k: v for k, v in self.map})

    def map_backward(self, v):
        from fontTools.varLib.models import piecewiseLinearMap

        if not self.map:
            return v
        return piecewiseLinearMap(v, {v: k for k, v in self.map})
