from __future__ import annotations

import json
from typing import Any, BinaryIO, Type

from ufoLib2.converters import structure, unstructure
from ufoLib2.serde.util import read_bytes, write_bytes
from ufoLib2.typing import PathLike, T

have_orjson = False
try:
    import orjson

    have_orjson = True
except ImportError:
    pass


def dumps(
    obj: Any,
    indent: int | None = None,
    sort_keys: bool = False,
    **kwargs: Any,
) -> bytes:
    data = unstructure(obj)

    if have_orjson:
        if indent is not None:
            if indent != 2:
                raise ValueError("indent must be 2 or None for orjson")
            kwargs["option"] = kwargs.pop("option", 0) | orjson.OPT_INDENT_2
        if sort_keys:
            kwargs["option"] = kwargs.pop("option", 0) | orjson.OPT_SORT_KEYS
        # orjson.dumps always returns bytes
        result = orjson.dumps(data, **kwargs)
    else:
        # built-in json.dumps returns a string, not bytes, hence the encoding
        s = json.dumps(data, indent=indent, sort_keys=sort_keys, **kwargs)
        result = s.encode("utf-8")
    return result


def loads(s: str | bytes, object_class: Type[T], **kwargs: Any) -> T:
    if have_orjson:
        data = orjson.loads(s, **kwargs)
    else:
        data = json.loads(s, **kwargs)
    return structure(data, object_class)


def dump(
    obj: Any,
    fp: PathLike | BinaryIO,
    indent: int | None = None,
    sort_keys: bool = False,
    **kwargs: Any,
) -> None:
    write_bytes(fp, dumps(obj, indent=indent, sort_keys=sort_keys, **kwargs))


def load(fp: PathLike | BinaryIO, object_class: Type[T], **kwargs: Any) -> T:
    return loads(read_bytes(fp), object_class, **kwargs)
