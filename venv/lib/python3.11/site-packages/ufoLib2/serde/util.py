from __future__ import annotations

from typing import BinaryIO, cast

from ufoLib2.typing import PathLike


def read_bytes(fp: PathLike | BinaryIO) -> bytes:
    if hasattr(fp, "read"):
        fp = cast(BinaryIO, fp)
        return fp.read()
    else:
        fp = cast(PathLike, fp)
        with open(fp, "rb") as f:
            return f.read()


def write_bytes(fp: PathLike | BinaryIO, data: bytes) -> None:
    if hasattr(fp, "write"):
        fp = cast(BinaryIO, fp)
        fp.write(data)
    else:
        fp = cast(PathLike, fp)
        with open(fp, "wb") as f:
            f.write(data)
