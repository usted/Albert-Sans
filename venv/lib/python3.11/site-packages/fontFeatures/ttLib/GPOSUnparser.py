"""GPOSUnparser: Convert binary GPOS lookups to fontFeatures objects."""
from .GTableUnparser import GTableUnparser
import fontFeatures


class GPOSUnparser(GTableUnparser):
    """Unparse a GPOS table into a fontFeatures object. See :py:class:`fontFeatures.ttLib.GTableUnparser`."""

    _table = "GPOS"
    lookupTypes = {
        1: "SinglePositioning",
        2: "PairPositioning",
        3: "CursiveAttachment",
        4: "MarkToBase",
        5: "MarkToLigature",
        6: "MarkToMark",
        7: "Contextual",
        8: "ChainedContextual",
        9: "Extension",
    }

    _attrs = {
        "lookup": "PosLookupRecord",
        "format1_ruleset": "PosRuleSet",
        "format1_rule": "PosRule",
        "format2_classset": "PosClassSet",
        "format2_rule": "PosClassRule",
        "chain_format1_ruleset": "ChainPosRuleSet",
        "chain_format1_rule": "ChainPosRule",
        "chain_format2_classset": "ChainPosClassSet",
        "chain_format2_rule": "ChainPosClassRule",
    }

    def makeValueRecord(self, valueRecord):
        """Helper routine to create ValueRecord instances.

        Args:
            valueRecord: An ``otTables.ValueRecord`` object.

        Returns a ``fontFeatures.ValueRecord`` object."""
        valueFormatFlags = (
            ("XPlacement", 0x0001),  # Includes horizontal adjustment for placement
            ("YPlacement", 0x0002),  # Includes vertical adjustment for placement
            ("XAdvance", 0x0004),  # Includes horizontal adjustment for advance
            ("YAdvance", 0x0008),  # Includes vertical adjustment for advance
            # Currently we don't have a way to express or represent value records
            # with Device tables, whether old-style (ppem adjustment) or new-style
            # (VariationIndex). Even if we could represent them, then what? See
            # issue #31.
            # ("XPlaDevice", 0x0010),  # Includes horizontal Device table for placement
            # ("YPlaDevice", 0x0020),  # Includes vertical Device table for placement
            # ("XAdvDevice", 0x0040),  # Includes horizontal Device table for advance
            # ("YAdvDevice", 0x0080)  # Includes vertical Device table for advance
            # , 'Reserved': 0xF000 For future use (set to zero)
        )

        # defaults to 0
        values = [getattr(valueRecord, name, 0) or None for name, _ in valueFormatFlags]
        return fontFeatures.ValueRecord(*values)

    def isChaining(self, lookupType):
        """Returns true if the given lookup type is a chaining lookup."""
        return lookupType >= 7

    def unparseSinglePositioning(self, lookup):
        """Turn a GPOS1 (single positioning) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(name=self.getname("SinglePositioning" + self.gensym()))
        self._fix_flags(b, lookup)

        for subtable in lookup.SubTable:
            if subtable.Format == 1:
                spos = fontFeatures.Positioning(
                    [subtable.Coverage.glyphs],
                    [self.makeValueRecord(subtable.Value)],
                    address=self.currentLookup,
                    flags=lookup.LookupFlag,
                )
                b.addRule(spos)
            else:
                # Optimize it later
                for g, v in zip(subtable.Coverage.glyphs, subtable.Value):
                    spos = fontFeatures.Positioning(
                        [[g]],
                        [self.makeValueRecord(v)],
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                    b.addRule(spos)
        return b, []

    def unparsePairPositioning(self, lookup):
        """Turn a GPOS2 (pair adjustment) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(name=self.getname("PairPositioning" + self.gensym()))
        self._fix_flags(b, lookup)
        for subtable in lookup.SubTable:
            if subtable.Format == 1:
                for g, pair in zip(subtable.Coverage.glyphs, subtable.PairSet):
                    for vr in pair.PairValueRecord:
                        spos = fontFeatures.Positioning(
                            [[g], [vr.SecondGlyph]],
                            [
                                self.makeValueRecord(vr.Value1),
                                self.makeValueRecord(vr.Value2),
                            ],
                            address=self.currentLookup,
                            flags=lookup.LookupFlag,
                        )
                        b.addRule(spos)
            else:
                class1 = self._invertClassDef(subtable.ClassDef1.classDefs, self.font)
                class2 = self._invertClassDef(subtable.ClassDef2.classDefs, self.font)
                for ix1, c1 in enumerate(subtable.Class1Record):
                    if ix1 not in class1:
                        continue  # XXX
                    for ix2, c2 in enumerate(c1.Class2Record):
                        if ix2 not in class2:
                            continue  # XXX
                        vr1 = self.makeValueRecord(c2.Value1)
                        vr2 = self.makeValueRecord(c2.Value2)
                        if not vr1 and not vr2:
                            continue
                        firstClass = list(
                            set(class1[ix1]) & set(subtable.Coverage.glyphs)
                        )
                        spos = fontFeatures.Positioning(
                            [firstClass, class2[ix2]],
                            [vr1, vr2],
                            address=self.currentLookup,
                            flags=lookup.LookupFlag,
                        )
                        b.addRule(spos)
        return b, []

    def unparseCursiveAttachment(self, lookup):
        """Turn a GPOS3 (cursive attachment) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(name=self.getname("CursiveAttachment" + self.gensym()))
        self._fix_flags(b, lookup)
        entries = {}
        exits = {}
        for s in lookup.SubTable:
            assert s.Format == 1
            for glyph, record in zip(s.Coverage.glyphs, s.EntryExitRecord):
                if record.EntryAnchor:
                    entries[glyph] = (
                        record.EntryAnchor.XCoordinate,
                        record.EntryAnchor.YCoordinate,
                    )
                if record.ExitAnchor:
                    exits[glyph] = (
                        record.ExitAnchor.XCoordinate,
                        record.ExitAnchor.YCoordinate,
                    )
        b.addRule(
            fontFeatures.Attachment(
                "cursive_entry",
                "cursive_exit",
                entries,
                exits,
                flags=lookup.LookupFlag,
                address=self.currentLookup,
            )
        )
        return b, []

    def unparseMarkToBase(self, lookup):
        """Turn a GPOS4 (mark to base) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(name=self.getname("MarkToBase" + self.gensym()))
        self._fix_flags(b, lookup)
        for subtable in lookup.SubTable:  # fontTools.ttLib.tables.otTables.MarkBasePos
            assert subtable.Format == 1
            for classId in range(0, subtable.ClassCount):
                anchorClassPrefix = "Anchor" + self.gensym()
                marks = self._formatMarkArray(
                    subtable.MarkArray, subtable.MarkCoverage, classId
                )
                bases = self._formatBaseArray(
                    subtable.BaseArray, subtable.BaseCoverage, classId
                )
                b.addRule(
                    fontFeatures.Attachment(
                        anchorClassPrefix,
                        "_"+anchorClassPrefix,
                        bases,
                        marks,
                        font=self.font,
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                )
        return b, []

    def _formatMarkArray(self, markArray, markCoverage, classId):
        id2Name = markCoverage.glyphs
        marks = {}
        for i, markRecord in enumerate(markArray.MarkRecord):
            if markRecord.Class == classId:
                marks[id2Name[i]] = (
                    markRecord.MarkAnchor.XCoordinate,
                    markRecord.MarkAnchor.YCoordinate,
                    # markRecord.Class
                )
        return marks

    def _formatMark2Array(self, markArray, markCoverage, anchorClassPrefix):
        id2Name = markCoverage.glyphs
        marks = {}
        for i, markRecord in enumerate(markArray.Mark2Record):
            anchor = markRecord.Mark2Anchor[anchorClassPrefix]
            if not anchor:
                continue
            marks[id2Name[i]] = (
                anchor.XCoordinate,
                anchor.YCoordinate,
            )
        return marks

    def _formatBaseArray(self, baseArray, baseCoverage, wantedClassId):
        id2Name = baseCoverage.glyphs
        bases = {}
        for i, baseRecord in enumerate(baseArray.BaseRecord):
            for classId, anchor in enumerate(baseRecord.BaseAnchor):
                if classId != wantedClassId:
                    continue
                if not anchor:
                    continue
                bases[id2Name[i]] = (anchor.XCoordinate, anchor.YCoordinate)  # ClassId?
        return bases

    def unparseMarkToLigature(self, lookup):
        """Turn a GPOS5 (mark to ligature) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(name=self.getname("MarkToLigature" + self.gensym()))
        self._fix_flags(b, lookup)
        self.unparsable(b, "Mark to lig pos", lookup)
        return b, []

    def unparseMarkToMark(self, lookup):
        """Turn a GPOS6 (mark to mark) subtable into a fontFeatures Routine."""
        b = fontFeatures.Routine(name=self.getname("MarkToMark" + self.gensym()))
        self._fix_flags(b, lookup)
        for subtable in lookup.SubTable:  # fontTools.ttLib.tables.otTables.MarkBasePos
            assert subtable.Format == 1
            for classId in range(0, subtable.ClassCount):
                anchorClassPrefix = "Anchor" + self.gensym()
                marks = self._formatMarkArray(
                    subtable.Mark1Array, subtable.Mark1Coverage, classId
                )
                bases = self._formatMark2Array(
                    subtable.Mark2Array, subtable.Mark2Coverage, classId
                )
                b.addRule(
                    fontFeatures.Attachment(
                        anchorClassPrefix,
                        anchorClassPrefix + "_",
                        bases,
                        marks,
                        font=self.font,
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                        force_markmark=True
                    )
                )
        return b, []
