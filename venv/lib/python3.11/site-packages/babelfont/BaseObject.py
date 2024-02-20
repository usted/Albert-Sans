from dataclasses import dataclass, fields, field
import orjson
from io import StringIO
from collections import namedtuple
import datetime


class IncompatibleMastersError(ValueError):
    pass

Color = namedtuple("Color", "r,g,b,a", defaults=[0, 0, 0, 0])
Position = namedtuple("Position", "x,y,angle", defaults=[0, 0, 0])
OTValue = namedtuple("OTValue", "table,field,value")

class I18NDictionary(dict):
    @classmethod
    def with_default(cls, s):
        inst = cls()
        inst.set_default(s)
        return inst

    def copy_in(self, other):
        if isinstance(other, dict):
            for k, v in other.items():
                self[k] = v
        else:
            self.set_default(other)

    def default_or_dict(self):
        if len(self.values()) > 1:
            return self
        else:
            return self.get_default()

    def get_default(self):
        if "dflt" in self:
            return self["dflt"]
        elif len(list(self.values())):
            return list(self.values())[0]
        else:
            return "unknown"

    def set_default(self, value):
        if value:
            self["dflt"] = value

    def write(self, stream, indent):
        if len(self.keys()) > 1:
            stream.write(orjson.dumps(self))
        else:
            stream.write('"{0}"'.format(self.get_default()).encode())

    @property
    def as_fonttools_dict(self):
        rv = dict(self)
        if "dflt" in rv:
            if "en" not in rv:
                rv["en"] = rv["dflt"]
            del rv["dflt"]
        return rv

@dataclass
class BaseObject:

    # OK, what's going on here? And why do we split _FoobarFields from Foobar?
    # We want to achieve the following:
    #    * A ``_formatspecific`` field on *every* derived object...
    #    * ...which does not need to be added to the constructor arguments
    #    * ...but which (for convenience when instantiating from JSON) has an
    #      alias of ``_`` which *can* be added to the constructor arguments

    # dataclasses load up their fields by walking the inheritance tree, but
    # (just like Python function declarations) dataclasses don't support putting
    # defaultable fields after non-defaultable fields.

    # Because we want ``_formatspecific`` (and particularly ``_``) to be optional
    # on __init__ it needs to be defaultable. So it needs to appear after the
    # other fields in the inheritance hierarchy. So we inherit from a _...Fields
    # class first and then BaseObject second. Ugly but it works.

    # dataclasses also don't support field aliases. The ``_`` field is only
    # really used for initialization, so in ``__post_init__`` we move its
    # contents into the `_formatspecific` field where it really lives.

    _formatspecific: dict = field(
        default_factory=dict,
        repr=False,
        metadata={
            "skip_serialize": True,
            "description": """
Each object in Babelfont has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the Babelfont-JSON representation. When stored to JSON, this key
is exported not as `_formatspecific` but as a simple underscore (`_`).
""",
        },
    )
    _: dict = field(default=None, repr=False, metadata={"skip_serialize": True})

    def __post_init__(self):
        if self._:
            self._formatspecific = self._

    _write_one_line = False
    _separate_items = {}

    def _should_separate_when_serializing(self, key):
        if (
            key in self.__dataclass_fields__
            and "separate_items" in self.__dataclass_fields__[key].metadata
        ):
            return True
        return False

    def _write_value(self, stream, k, v, indent=0):
        if hasattr(v, "write"):
            v.write(stream, indent + 1)
        elif isinstance(v, tuple):
            stream.write(b"[")
            for ix, l in enumerate(v):
                self._write_value(stream, k, l, indent + 1)
                if ix < len(v) - 1:
                    stream.write(b", ")
            stream.write(b"]")
        elif isinstance(v, dict):
            stream.write(b"{")
            for ix, (k1, v1) in enumerate(v.items()):
                if self._should_separate_when_serializing(k):
                    stream.write(b"\n")
                    stream.write(b"  " * (indent + 2))
                if not isinstance(k1, str):
                    # XXX kerning keys are tuples
                    self._write_value(stream, k, "//".join(k1), indent + 1)
                else:
                    self._write_value(stream, k, k1, indent + 1)
                stream.write(b": ")
                self._write_value(stream, k, v1, indent + 1)
                if ix < len(v.items()) - 1:
                    stream.write(b", ")
            stream.write(b"}")
        elif isinstance(v, list):
            stream.write(b"[")
            for ix, l in enumerate(v):
                if self._should_separate_when_serializing(k):
                    stream.write(b"\n")
                    stream.write(b"  " * (indent + 2))
                self._write_value(stream, k, l, indent + 1)
                if ix < len(v) - 1:
                    stream.write(b", ")
            if self._should_separate_when_serializing(k):
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))
            stream.write(b"]")
        elif isinstance(v, datetime.datetime):
            stream.write('"{0}"'.format(v.__str__()).encode())
        else:
            stream.write(orjson.dumps(v))

    def write(self, stream, indent=0):
        if not self._write_one_line:
            stream.write(b"  " * indent)
        stream.write(b"{")
        towrite = []
        for f in fields(self):
            k = f.name
            if "skip_serialize" in f.metadata or "python_only" in f.metadata:
                continue
            v = getattr(self, k)
            default = f.default
            if (not v and not "serialize_if_false" in f.metadata) or (default and v == default):
                continue
            towrite.append((k, v))

        for ix, (k, v) in enumerate(towrite):
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))

            stream.write('"{0}": '.format(k).encode())
            self._write_value(stream, k, v, indent)
            if ix != len(towrite) - 1:
                stream.write(b", ")

        if hasattr(self, "_formatspecific") and self._formatspecific:
            stream.write(b",")
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))
            stream.write(b'"_":')
            if self._write_one_line:
                stream.write(orjson.dumps(self._formatspecific))
            else:
                stream.write(b"\n")
                stream.write(
                    orjson.dumps(self._formatspecific, option=orjson.OPT_INDENT_2)
                )

        if not self._write_one_line:
            stream.write(b"\n")
        stream.write(b"}")
        if not self._write_one_line:
            stream.write(b"\n")
