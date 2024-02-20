"""GSUBUnparser: Convert binary GSUB lookups to fontFeatures objects."""
import fontTools
from collections import OrderedDict
from .GTableUnparser import GTableUnparser
from itertools import groupby
import fontFeatures

# These are silly little functions which help to document the intent
def glyph(x):
    """Wraps a glyph name in an array, to document the fact that it occupies a slot."""
    assert isinstance(x, str)
    return [x]

def singleglyph(x):
    """Wraps a glyph name in two arrays, to document the fact that it is the only occupant of a slot."""
    return [glyph(x)]


class GSUBUnparser(GTableUnparser):
    """Unparse a GSUB table into a fontFeatures object. See :py:class:`fontFeatures.ttLib.GTableUnparser`."""
    _table = "GSUB"
    lookupTypes = {
        1: "SingleSubstitution",
        2: "MultipleSubstitution",
        3: "AlternateSubstitution",
        4: "LigatureSubstitution",
        5: "Contextual",
        6: "ChainedContextual",
        7: "Extension",
        8: "ReverseContextualSubstitution",
    }

    _attrs = {
        "lookup": "SubstLookupRecord",
        "format1_ruleset": "SubRuleSet",
        "format1_rule": "SubRule",
        "format2_classset": "SubClassSet",
        "format2_rule": "SubClassRule",
        "chain_format1_ruleset": "ChainSubRuleSet",
        "chain_format1_rule": "ChainSubRule",
        "chain_format2_classset": "ChainSubClassSet",
        "chain_format2_rule": "ChainSubClassRule",
    }

    def isChaining(self, lookupType):
        """Returns true if the given lookup type is a chaining lookup."""
        return lookupType >= 5

    def unparseReverseContextualSubstitution(self, lookup):
        """Turn a GPOS8 (reverse contextual substitution) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(
            name=self.getname("ReverseContextualSubstitution" + self.gensym())
        )
        self._fix_flags(b, lookup)
        for sub in lookup.SubTable:
            prefix  = []
            outputs = []
            suffix  = []
            if hasattr(sub, "BacktrackCoverage"):
                for coverage in reversed(sub.BacktrackCoverage):
                    prefix.append(coverage.glyphs)
            if hasattr(sub, "LookAheadCoverage"):
                for i, coverage in enumerate(sub.LookAheadCoverage):
                    suffix.append(coverage.glyphs)
            outputs = [ sub.Substitute ]
            inputs =  [ sub.Coverage.glyphs ]
            b.addRule(
                fontFeatures.Substitution(
                    inputs,
                    outputs,
                    prefix,
                    suffix,
                    flags=lookup.LookupFlag,
                    reverse=True
                )
            )
        return b,[]

    def unparseLigatureSubstitution(self, lookup):
        """Turn a GPOS4 (ligature substitution) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(
            name=self.getname("LigatureSubstitution" + self.gensym())
        )
        self._fix_flags(b, lookup)
        for sub in lookup.SubTable:
            for first, ligatures in sub.ligatures.items():
                for lig in ligatures:
                    substarray = [glyph(first)]
                    for x in lig.Component:
                        substarray.append(glyph(x))
                    b.addRule(
                        fontFeatures.Substitution(
                            substarray,
                            singleglyph(lig.LigGlyph),
                            address=self.currentLookup,
                            flags=lookup.LookupFlag,
                        )
                    )
        return b, []

    def unparseMultipleSubstitution(self, lookup):
        """Turn a GPOS2 (multiple substitution) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(
            name=self.getname("MultipleSubstitution" + self.gensym())
        )
        self._fix_flags(b, lookup)

        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.mapping.items():
                b.addRule(
                    fontFeatures.Substitution(
                        singleglyph(in_glyph),
                        [glyph(x) for x in out_glyphs],
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                )
        return b, []

    def unparseAlternateSubstitution(self, lookup):
        """Turn a GPOS3 (alternate substitution) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(
            name=self.getname("AlternateSubstitution" + self.gensym())
        )
        self._fix_flags(b, lookup)
        for sub in lookup.SubTable:
            for in_glyph, out_glyphs in sub.alternates.items():
                b.addRule(
                    fontFeatures.Substitution(
                        singleglyph(in_glyph),
                        [out_glyphs],
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                        force_alt=True,
                    )
                )
        return b, []

    def unparseSingleSubstitution(self, lookup):
        """Turn a GPOS1 (single substitution) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(
            name=self.getname("SingleSubstitution" + self.gensym())
        )
        self._fix_flags(b, lookup)
        for sub in lookup.SubTable:
            for k, v in sub.mapping.items():
                b.addRule(
                    fontFeatures.Substitution(
                        [[k]],
                        [[v]],
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                )
        return b, []
