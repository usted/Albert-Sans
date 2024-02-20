from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Mapping, Tuple

from ufoLib2.serde import serde

if TYPE_CHECKING:
    from typing import Type

    from cattrs import Converter

KerningPair = Tuple[str, str]


@serde
class Kerning(Dict[KerningPair, float]):
    def as_nested_dicts(self) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        for (left, right), value in self.items():
            result.setdefault(left, {})[right] = value
        return result

    @classmethod
    def from_nested_dicts(self, kerning: Mapping[str, Mapping[str, float]]) -> Kerning:
        return Kerning(
            ((left, right), kerning[left][right])
            for left in kerning
            for right in kerning[left]
        )

    def _unstructure(self, converter: Converter) -> dict[str, dict[str, float]]:
        del converter  # unused
        return self.as_nested_dicts()

    @staticmethod
    def _structure(
        data: Mapping[str, Mapping[str, float]],
        cls: Type[Kerning],
        converter: Converter,
    ) -> Kerning:
        del converter  # unused
        return cls.from_nested_dicts(data)
