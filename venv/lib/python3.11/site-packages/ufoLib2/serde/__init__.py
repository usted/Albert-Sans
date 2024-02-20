from __future__ import annotations

from functools import partialmethod
from importlib import import_module
from typing import IO, Any, AnyStr, Callable, Type

from ufoLib2.typing import PathLike, T

_SERDE_FORMATS_ = ("json", "msgpack")


# the @serde decorator sets these as @classmethods on the class, hence
# the cls argument must appear as the first argument; in the standalone loads/load
# functions the input string or file-like object is the first argument and the second
# argument is the object_class, so below just swap the order of the arguments
def _loads(
    cls: Type[T], s: str | bytes, *, __callback: Callable[..., T], **kwargs: Any
) -> T:
    return __callback(s, cls, **kwargs)


def _load(
    cls: Type[T],
    fp: PathLike | IO[AnyStr],
    *,
    __callback: Callable[..., T],
    **kwargs: Any,
) -> T:
    return __callback(fp, cls, **kwargs)


def serde(cls: Type[T]) -> Type[T]:
    """Decorator to add serialization support to a ufoLib2 class.

    This adds f"{format}_loads" / f"{format}_dumps" (from/to bytes) methods, and
    f"{format}_load" / f"{format}_dump" (for file or path) methods to all ufoLib2
    objects, not just Font.

    Currently the supported formats are JSON and MessagePack (msgpack), but other
    formats may be added in the future.

    E.g.::

        from ufoLib2 import Font

        font = Font.open("MyFont.ufo")
        font.json_dump("MyFont.json")
        font2 = Font.json_load("MyFont.json")
        font3 = Font.json_loads(font2.json_dumps())

        font3.msgpack_dump("MyFont.msgpack")
        font4 = Font.msgpack_load("MyFont.msgpack")
        # etc.

    Note this requires additional extras to be installed: e.g. ufoLib2[json,msgpack].
    In additions to the respective serialization library, these installs the `cattrs`
    library for structuring/unstructuring custom objects from/to serializable data
    structures (also available separately as ufoLib2[converters] extra).

    If any of the optional dependencies fails to be imported, the methods will raise
    an ImportError when called.

    If the faster `orjson` library is present, it will be used in place of the
    built-in `json` library on CPython. On PyPy, the `orjson` library is not available,
    so the built-in `json` library will be used (though it's pretty fast anyway).

    If you want a serialization format that works out of the box with all ufoLib2
    objects (but it's mostly limited to Python) you can use the built-in pickle module,
    which doesn't require to use the `cattrs` converters.

    """

    supported_formats = []
    for fmt in _SERDE_FORMATS_:

        try:
            serde_submodule = import_module(f"ufoLib2.serde.{fmt}")
        except ImportError as e:
            exc = e

            def raise_error(*args: Any, **kwargs: Any) -> None:
                raise exc

            for method in ("loads", "load", "dumps", "dump"):
                setattr(cls, f"{fmt}_{method}", raise_error)
        else:
            setattr(
                cls,
                f"{fmt}_loads",
                partialmethod(classmethod(_loads), __callback=serde_submodule.loads),
            )
            setattr(
                cls,
                f"{fmt}_load",
                partialmethod(classmethod(_load), __callback=serde_submodule.load),
            )
            setattr(cls, f"{fmt}_dumps", serde_submodule.dumps)
            setattr(cls, f"{fmt}_dump", serde_submodule.dump)
            supported_formats.append(fmt)

    setattr(cls, "_SERDE_FORMATS_", tuple(supported_formats))

    return cls
