"""
GTableUnparser: Base class for reading binary GSUB/GPOS tables
==============================================================
"""
from collections import OrderedDict
from fontTools.misc.xmlWriter import XMLWriter
import fontFeatures
from io import BytesIO
import warnings


def glyph(x):
    """Helper routine to document that a glyph name goes in a slot."""
    assert isinstance(x, str)
    return [x]


class GTableUnparser:
    """Base class for reading binary GSUB/GPOS tables."""

    def __init__(self, table, ff, languageSystems, font=None, config={}):
        """Create a new unparser

        Args:
            table: An object returned by ``font["GSUB"]`` or ``font["GPOS"]``.
            ff: A fontFeatures object in which to return the output.
            font: A ``TTFont`` object (optional).
            config: A dictionary mapping generated names to friendly names.

        The config dictionary is used to make the output more human readable.
        For example, after dumping a binary TTF and reading the output, you might
        discover that what we are calling ``SingleSubstitution1`` would be better
        named ``fiLigature``. Passing ``{"SingleSubstitution1": "fiLigature"}``
        to the call will cause the routine to be renamed appropriately."""

        self.table = table.table
        self.font = font
        self.fontFeatures = ff
        self.config = config
        self.index = 0
        self.lookups = []  # We keep a separate list because this is per-table
        self.sharedClasses = {}
        self.languageSystems = languageSystems
        self.sharedLookups = OrderedDict()

    def _unparse_lookups(self, slr, inputs, in_lookups=None):
        lookups = []
        note = None
        if in_lookups:
            lookups = in_lookups
        indices = [sl.SequenceIndex for sl in slr]
        if indices != list(sorted(indices)):
            # https://github.com/adobe-type-tools/afdko/issues/1167
            note = (
                f"Out-of-order lookup application in lookup {self.currentLookup}\n"
                f" A chaining rule calls lookups in the order {indices}\n"
                " This cannot be directly expressed in Adobe FEA syntax;\n"
                "  asFea() output will be incorrect"
            )
            warnings.warn(note)
        for sl in slr:
            if len(lookups) <= sl.SequenceIndex:
                lookups.extend([None] * (1 + sl.SequenceIndex - len(lookups)))
            if not lookups[sl.SequenceIndex]:
                lookups[sl.SequenceIndex] = []
            if sl.LookupListIndex >= len(self.lookups):
                raise ValueError("Lookups unparsed out of order: unparse %i first!" % sl.LookupListIndex)
            rr = fontFeatures.RoutineReference(routine=self.lookups[sl.LookupListIndex])
            lookups[sl.SequenceIndex].append(rr)
        if len(lookups) < len(inputs):
            lookups.extend([None] * (len(inputs) - len(lookups)))
        assert len(lookups) == len(inputs)
        return lookups, note

    def _invertClassDef(self, a, font):
        classes = {}
        for glyph, klass in a.items():
            if klass not in classes:
                classes[klass] = []
            classes[klass].append(glyph)
        glyphset = set(font.getGlyphOrder())
        classes[0] = glyphset - set(a.keys())
        return classes

    def getname(self, n):
        """Renames its input using the configuration dictionary"""
        return self.config.get(n, n)

    def gensym(self):
        """Generates a new unique name"""
        self.index = self.index + 1
        return str(self.index)

    def unparse(self, doLookups=True):
        """Unparse the table to the fontFeatures object."""
        if not self.table.ScriptList:
            return
        self.unparseLookups()
        self.collectFeatures()
        self.fontFeatures.resolveAllRoutines()

    def _prepareFeatureLangSys(self, langTag, langSys, table, features, scriptTag):
        # This is a part of prepareFeatures
        for featureIdx in langSys.FeatureIndex:
            featureRecord = self.table.FeatureList.FeatureRecord[featureIdx]
            featureTag = featureRecord.FeatureTag
            scripts = features.get(featureTag, None)
            if scripts is None:
                scripts = OrderedDict()
                features[featureTag] = scripts

            languages = scripts.get(scriptTag, None)
            if languages is None:
                languages = OrderedDict()
                scripts[scriptTag] = languages

            lookups = languages.get(langTag, None)
            if lookups is None:
                lookups = []
                languages[langTag] = lookups

            for lookupIdx in featureRecord.Feature.LookupListIndex:
                self.lookups[lookupIdx].languages.append((scriptTag, langTag))
                # Add reference if there isn't one
                if not featureTag in self.fontFeatures.features:
                    self.fontFeatures.features[featureTag] = []
                if not any(
                    r.routine == self.lookups[lookupIdx]
                    for r in self.fontFeatures.features[featureTag]
                ):
                    self.fontFeatures.addFeature(
                        featureTag,
                        [
                            self.lookups[lookupIdx]
                        ],
                    )
                lookups.append(lookupIdx)

    def collectFeatures(self):
        """Traverse the script/language table looking for features."""
        features = OrderedDict()
        for scriptRecord in self.table.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            if scriptRecord.Script.DefaultLangSys is not None:
                self._prepareFeatureLangSys(
                    "dflt",
                    scriptRecord.Script.DefaultLangSys,
                    self.table,
                    features,
                    scriptTag,
                )
            for langSysRecord in scriptRecord.Script.LangSysRecord:
                self._prepareFeatureLangSys(
                    langSysRecord.LangSysTag,
                    langSysRecord.LangSys,
                    self.table,
                    features,
                    scriptTag,
                )
        self.features = features

    def addFeatures(self, doLookups=True):
        """Add lookup references from the features list into the fontFeatures object."""
        for name, feature in self.features.items():
            f = []
            for scriptname, langs in feature.items():
                for lang, lookups in langs.items():
                    if doLookups:
                        for lookupIdx in lookups:
                            f.append(
                                RoutineReference(
                                    routine=self.fontFeatures.routines[lookupIdx]
                                )
                            )
                            self.fontFeatures.routines[lookupIdx].languages.append(
                                (scriptname, lang)
                            )
            self.fontFeatures.addFeature(name, f)

    def unparseLookups(self):
        """Unparses the lookups to fontFeatures routines."""
        if not self.table.LookupList:
            return
        # Create a dummy list first, to allow resolving chained lookups
        for _ in self.table.LookupList.Lookup:
            r = fontFeatures.Routine()
            self.lookups.append(r)
            self.fontFeatures.routines.append(r)

        for lookupIdx, lookup in enumerate(self.table.LookupList.Lookup):
            routine, deps = self.unparseLookup(lookup, lookupIdx)
            debug = self.getDebugInfo(self._table, lookupIdx)
            if debug:
                routine.address = (self._table, lookupIdx, *debug)
                if debug[1]:
                    routine.name = debug[1]
            self._copyRoutineToRoutine(routine, self.lookups[lookupIdx])

    def _copyRoutineToRoutine(self, src, dst):
        dst.name = src.name
        dst.rules = src.rules
        dst.flags = src.flags
        dst.address = src.address
        dst.comments = src.comments
        dst.inlined = src.inlined
        dst.languages = src.languages
        dst.parent = src.parent
        dst.flags = src.flags
        dst.markFilteringSet = src.markFilteringSet
        dst.markAttachmentSet = src.markAttachmentSet

    def unparseLookup(self, lookup, lookupIdx):
        """Dispatches to the appropriate lookup unparser."""
        self.currentLookup = lookupIdx
        unparser = getattr(self, "unparse" + self.lookupTypes[lookup.LookupType])
        return unparser(lookup)

    def unparseExtension(self, lookup):
        """Handles extension lookups by recursing into them."""
        routines = []
        dependencies = []
        for xt in lookup.SubTable:
            xt.SubTable = [xt.ExtSubTable]
            xt.LookupType = xt.ExtSubTable.LookupType
            xt.LookupFlag = lookup.LookupFlag
            if hasattr(lookup, "MarkFilteringSet"):
                xt.MarkFilteringSet = lookup.MarkFilteringSet
            routine, deps = self.unparseLookup(xt, self.currentLookup)
            routines.append(routine)
            dependencies.extend(deps)
        extension = fontFeatures.ExtensionRoutine(
            routines=routines,
            name=self.getname("Extension" + self.gensym()),
        )
        self._fix_flags(extension, lookup)
        return extension, dependencies

    def getDebugInfo(self, table, ix):
        """If information is present in the font's Debg table, use that to
        retrieve the original address and routine names."""
        if not self.font or "Debg" not in self.font:
            return None
        debug_data = self.font["Debg"].data
        if "com.github.fonttools.feaLib" not in debug_data:
            return None
        debug_data = debug_data["com.github.fonttools.feaLib"][table][str(ix)]
        return debug_data[0], debug_data[1]

    def _asXML(self, sub):
        writer = XMLWriter(BytesIO())
        sub.toXML(writer, self.font)
        out = writer.file.getvalue().decode("utf-8")
        return out

    def unparsable(self, b, e, sub):
        """Warn about an unparsable lookup."""
        import warnings

        warnings.warn(
            "# XXX Unparsable rule: " + str(e) + " in " + str(self.currentLookup)
        )
        b.addComment("# ----")
        out = self._asXML(sub).splitlines()
        for ln in out:
            b.addComment("# " + ln)
        b.addComment("# ----\n")

    def _fix_flags(self, routine, lookup):
        routine.flags = lookup.LookupFlag
        mat = lookup.LookupFlag & 0xFF00
        if mat:
            mat = mat >> 8
            classDefs = self.font["GDEF"].table.MarkAttachClassDef.classDefs
            glyphs = [g for g in classDefs.keys() if classDefs[g] == mat]
            routine.markAttachmentSet = glyphs
        if lookup.LookupFlag & 0x10 and hasattr(lookup, "MarkFilteringSet"):
            routine.markFilteringSet = (
                self.font["GDEF"]
                .table.MarkGlyphSetsDef.Coverage[lookup.MarkFilteringSet]
                .glyphs
            )

        if routine.flags & 0x10:
            assert routine.markFilteringSet is not None


    def unparseContextual(self, lookup):
        """Handles a generic contextual lookup, in various formats."""
        b = fontFeatures.Routine(
            name=self.getname("Contextual" + self._table + self.gensym())
        )
        self._fix_flags(b, lookup)
        for sub in lookup.SubTable:
            if sub.Format == 1:
                self._unparse_contextual_format1(sub, b, lookup)
            elif sub.Format == 2:
                self._unparse_contextual_format2(sub, b, lookup)
            elif sub.Format == 3:
                self._unparse_contextual_format3(sub, b, lookup)
            else:
                raise ValueError
        return b, []

    def _unparse_contextual_format1(self, sub, b, lookup):
        lookups = []
        rulesetattr, ruleattr, lookupattr = [
            self._attrs[x] for x in ["format1_ruleset", "format1_rule", "lookup"]
        ]

        for subrulesets, input_ in zip(getattr(sub, rulesetattr), sub.Coverage.glyphs):
            for subrule in getattr(subrulesets, ruleattr):
                lookups = []
                allinput = [glyph(x) for x in ([input_] + subrule.Input)]
                lookups, note = self._unparse_lookups(getattr(subrule, lookupattr), allinput)
                rule = fontFeatures.Chaining(
                        allinput,
                        lookups=lookups,
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                if note:
                    rule.note = note
                b.addRule(rule)
        return

    def _unparse_contextual_format2(self, sub, b, lookup):
        return self._unparse_contextual_chain_format2(sub, b, lookup, chain=False)

    def _unparse_contextual_format3(self, sub, b, lookup):
        return self._unparse_contextual_chain_format3(sub, b, lookup, chain=False)

    def unparseChainedContextual(self, lookup):
        """Handles a generic chained contextual lookup, in various formats."""
        b = fontFeatures.Routine(
            name=self.getname("ChainedContextual" + self._table + self.gensym())
        )
        self._fix_flags(b, lookup)
        for sub in lookup.SubTable:
            if sub.Format == 1:
                self._unparse_contextual_chain_format1(sub, b, lookup)
            elif sub.Format == 2:
                self._unparse_contextual_chain_format2(sub, b, lookup)
            elif sub.Format == 3:
                self._unparse_contextual_chain_format3(sub, b, lookup)
            else:
                raise ValueError
        return b, []

    def _unparse_contextual_chain_format1(self, sub, b, lookup):
        rulesetattr, ruleattr, lookupattr = [
            self._attrs[x]
            for x in ["chain_format1_ruleset", "chain_format1_rule", "lookup"]
        ]

        for subrulesets, input_ in zip(getattr(sub, rulesetattr), sub.Coverage.glyphs):
            for subrule in getattr(subrulesets, ruleattr):
                lookups = []
                inputs = [glyph(x) for x in ([input_] + subrule.Input)]
                prefix = [glyph(x) for x in reversed(subrule.Backtrack)]
                suffix = [glyph(x) for x in subrule.LookAhead]
                lookups, note = self._unparse_lookups(getattr(subrule, lookupattr), inputs)
                rule = fontFeatures.Chaining(
                        inputs,
                        prefix,
                        suffix,
                        lookups=lookups,
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                if note:
                    rule.note = note
                b.addRule(rule)

    def _unparse_contextual_chain_format2(self, sub, b, lookup, chain=True):
        if chain:
            rulesetattr, ruleattr, lookupattr = [
                self._attrs[x]
                for x in ["chain_format2_classset", "chain_format2_rule", "lookup"]
            ]
        else:
            rulesetattr, ruleattr, lookupattr = [
                self._attrs[x] for x in ["format2_classset", "format2_rule", "lookup"]
            ]

        if chain:
            backtrack = {}
            if sub.BacktrackClassDef:
                backtrack = self._invertClassDef(
                    sub.BacktrackClassDef.classDefs, self.font
                )
            lookahead = {}
            if sub.LookAheadClassDef:
                lookahead = self._invertClassDef(
                    sub.LookAheadClassDef.classDefs, self.font
                )
            inputs = {}
            inputs = self._invertClassDef(sub.InputClassDef.classDefs, self.font)
        else:
            inputs = self._invertClassDef(sub.ClassDef.classDefs, self.font)

        rulesets = getattr(sub, rulesetattr)
        for classId, ruleset in enumerate(rulesets):
            if not ruleset:
                continue
            rules = getattr(ruleset, ruleattr)
            inputclass = inputs.get(classId, [])
            # The coverage filters the input class...
            inputclass = [g for g in inputclass if g in sub.Coverage.glyphs]
            for r in rules:
                if chain:
                    prefix = list(reversed([backtrack[x] for x in r.Backtrack]))
                    suffix = [lookahead[x] for x in r.LookAhead]
                    input_ = [inputclass] + [inputs[x] for x in r.Input]
                else:
                    prefix, suffix = [], []
                    input_ = [inputclass] + [inputs[x] for x in r.Class]
                lookups, note = self._unparse_lookups(getattr(r, lookupattr), input_)
                rule = fontFeatures.Chaining(
                        input_,
                        prefix,
                        suffix,
                        lookups=lookups,
                        address=self.currentLookup,
                        flags=lookup.LookupFlag,
                    )
                if note:
                    rule.note = note
                b.addRule(rule)

    def _unparse_contextual_chain_format3(self, sub, b, lookup, chain=True):
        lookupattr = self._attrs["lookup"]
        prefix, suffix, inputs = [], [], []

        if chain:
            for coverage in reversed(sub.BacktrackCoverage):
                prefix.append(coverage.glyphs)
            for coverage in sub.LookAheadCoverage:
                suffix.append(coverage.glyphs)
            for coverage in sub.InputCoverage:
                inputs.append(coverage.glyphs)
        else:
            for coverage in sub.Coverage:
                inputs.append(coverage.glyphs)

        lookups, note = self._unparse_lookups(getattr(sub, lookupattr), inputs)
        rule = fontFeatures.Chaining(
                inputs,
                prefix,
                suffix,
                lookups=lookups,
                address=self.currentLookup,
                flags=lookup.LookupFlag,
            )
        if note:
            rule.note = note
        b.addRule(rule)
