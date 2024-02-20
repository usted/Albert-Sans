from __future__ import annotations

from typing import Any, BinaryIO, Type, cast

import msgpack  # type: ignore

from ufoLib2.converters import binary_converter
from ufoLib2.serde.util import read_bytes, write_bytes
from ufoLib2.typing import PathLike, T


def dumps(obj: Any, **kwargs: Any) -> bytes:
    data = binary_converter.unstructure(obj)
    result = msgpack.packb(data, **kwargs)
    return cast(bytes, result)


def loads(s: bytes, object_class: Type[T], **kwargs: Any) -> T:
    data = msgpack.unpackb(s, **kwargs)
    return binary_converter.structure(data, object_class)


def dump(obj: Any, fp: PathLike | BinaryIO, **kwargs: Any) -> None:
    write_bytes(fp, dumps(obj, **kwargs))


def load(fp: PathLike | BinaryIO, object_class: Type[T], **kwargs: Any) -> T:
    return loads(read_bytes(fp), object_class, **kwargs)
