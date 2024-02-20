"""
voltLib: Load fontFeatures objects from Microsoft VOLT
======================================================

This module is experimental and incomplete.
"""

import logging
import re
from io import StringIO
from fontTools.ttLib import TTFont, TTLibError
from fontTools.voltLib import ast as VAst
from fontTools.voltLib.parser import Parser
from fontFeatures import ValueRecord, FontFeatures, Routine, Substitution, RoutineReference

log = logging.getLogger()

class Group:
    def __init__(self, group):
        self.name = group.name.lower()
        self.groups = [
            x.group.lower() for x in group.enum.enum if isinstance(x, VAst.GroupName)
        ]

    def __lt__(self, other):
        if self.name in other.groups:
            return True
        if other.name in self.groups:
            return False
        return self.name < other.name


class VoltParser:
    _NOT_LOOKUP_NAME_RE = re.compile(r"[^A-Za-z_0-9.]")
    _NOT_CLASS_NAME_RE = re.compile(r"[^A-Za-z_0-9.\-]")

    def __init__(self, file_or_path, font=None):
        self._file_or_path = file_or_path
        self._font = font

        self._glyph_map = {}
        self._glyph_order = None

        self._gdef = {}
        self._glyphclasses = {}
        self._features = {}
        self._lookups = {}

        self._marks = set()
        self._ligatures = {}

        self._markclasses = {}
        self._anchors = {}

        self._settings = {}

        self._lookup_names = {}
        self._class_names = {}

    def _lookupName(self, name):
        if name not in self._lookup_names:
            res = self._NOT_LOOKUP_NAME_RE.sub("_", name)
            while res in self._lookup_names.values():
                res += "_"
            self._lookup_names[name] = res
        return self._lookup_names[name]

    def _className(self, name):
        if name not in self._class_names:
            res = self._NOT_CLASS_NAME_RE.sub("_", name)
            while res in self._class_names.values():
                res += "_"
            self._class_names[name] = res
        return self._class_names[name]

    def _collectStatements(self, doc):
        # Collect and sort group definitions first, to make sure a group
        # definition that references other groups comes after them since VOLT
        # does not enforce such ordering, and feature file require it.
        groups = [s for s in doc.statements if isinstance(s, VAst.GroupDefinition)]
        for statement in sorted(groups, key=lambda x: Group(x)):
            self._groupDefinition(statement)

        for statement in doc.statements:
            if isinstance(statement, VAst.GlyphDefinition):
                self._glyphDefinition(statement)
            elif isinstance(statement, VAst.AnchorDefinition):
                self._anchorDefinition(statement)
            elif isinstance(statement, VAst.SettingDefinition):
                self._settingDefinition(statement)
            elif isinstance(statement, VAst.GroupDefinition):
                pass  # Handled above
            elif isinstance(statement, VAst.ScriptDefinition):
                self._scriptDefinition(statement)
            elif not isinstance(statement, VAst.LookupDefinition):
                raise NotImplementedError(statement)

        # Lookup definitions need to be handled last as they reference glyph
        # and mark classes that might be defined after them.
        for statement in doc.statements:
            if isinstance(statement, VAst.LookupDefinition):
                self._lookupDefinition(statement)

        # Now rearrange features
        for feature, thing in self._features.items():
            for script, thing in thing.items():
                for lang, lookups in thing.items():
                    for lookup in lookups:
                        ref = RoutineReference(name=lookup)
                        ref.resolve(self.ff)
                        ref.language = (script, lang)
                        self.ff.addFeature(feature, [ref])

    def convert(self):
        doc = Parser(self._file_or_path).parse()
        if self._font is not None:
            self._glyph_order = self._font.getGlyphOrder()

        self.ff = FontFeatures()
        self._collectStatements(doc)
        return self.ff

    def _glyphName(self, glyph):
        try:
            name = glyph.glyph
        except AttributeError:
            name = glyph
        return name

    def _groupName(self, group):
        try:
            name = group.group
        except AttributeError:
            name = group
        return self.ff.namedClasses[name.lower()]

    def _coverage(self, coverage):
        items = []
        for item in coverage:
            if isinstance(item, VAst.GlyphName):
                items.append([self._glyphName(item)])
            elif isinstance(item, VAst.GroupName):
                items.append(self._groupName(item))
            elif isinstance(item, VAst.Enum):
                items.append(self._enum(item))
            elif isinstance(item, VAst.Range):
                items.append((item.start, item.end))
            else:
                raise NotImplementedError(item)
        return items

    def _enum(self, enum):
        return self._coverage(enum.enum)

    def _context(self, context):
        out = []
        for item in context:
            coverage = self._coverage(item)
            if not isinstance(coverage, (tuple, list)):
                coverage = [coverage]
            out.extend(coverage)
        return out

    def _groupDefinition(self, group):
        name = self._className(group.name)
        glyphs = [self._glyphName(x) for x in group.enum.enum]
        self.ff.namedClasses[group.name.lower()] = glyphs

    def _glyphDefinition(self, glyph):
        try:
            self._glyph_map[glyph.name] = self._glyph_order[glyph.id]
        except TypeError:
            pass

        if glyph.type in ("BASE", "MARK", "LIGATURE", "COMPONENT"):
            self.ff.glyphclasses[glyph.name] = glyph.type.lower()

        if glyph.type == "MARK":
            self._marks.add(glyph.name)
        elif glyph.type == "LIGATURE":
            self._ligatures[glyph.name] = glyph.components

    def _scriptDefinition(self, script):
        stag = script.tag
        for lang in script.langs:
            ltag = lang.tag
            for feature in lang.features:
                lookups = {l.split("\\")[0]: True for l in feature.lookups}
                ftag = feature.tag
                if ftag not in self._features:
                    self._features[ftag] = {}
                if stag not in self._features[ftag]:
                    self._features[ftag][stag] = {}
                assert ltag not in self._features[ftag][stag]
                self._features[ftag][stag][ltag] = lookups.keys()

    def _settingDefinition(self, setting):
        if setting.name.startswith("COMPILER_"):
            self._settings[setting.name] = setting.value
        else:
            log.warning(f"Unsupported setting ignored: {setting.name}")

    def _adjustment(self, adjustment):
        adv, dx, dy, adv_adjust_by, dx_adjust_by, dy_adjust_by = adjustment

        adv_device = adv_adjust_by and adv_adjust_by.items() or None
        dx_device = dx_adjust_by and dx_adjust_by.items() or None
        dy_device = dy_adjust_by and dy_adjust_by.items() or None

        return ValueRecord(
            xPlacement=dx,
            yPlacement=dy,
            xAdvance=adv,
            xPlaDevice=dx_device,
            yPlaDevice=dy_device,
            xAdvDevice=adv_device,
        )

    def _anchor(self, adjustment):
        adv, dx, dy, adv_adjust_by, dx_adjust_by, dy_adjust_by = adjustment
        return (dx or 0, dy or 0)

    def _anchorDefinition(self, anchordef):
        anchorname = anchordef.name
        glyphname = anchordef.glyph_name
        anchor = self._anchor(anchordef.pos)

        if anchorname.startswith("MARK_"):
            name = "_".join(anchorname.split("_")[1:])
            markclass = self._className(name)
            glyph = self._glyphName(glyphname)
            self._markclasses[(glyphname, anchorname)] = markclass
        else:
            if glyphname not in self._anchors:
                self._anchors[glyphname] = {}
            if anchorname not in self._anchors[glyphname]:
                self._anchors[glyphname][anchorname] = {}
            self._anchors[glyphname][anchorname][anchordef.component] = anchor

    def _gposLookup(self, lookup, fealookup):
        statements = fealookup.statements

        pos = lookup.pos
        if isinstance(pos, VAst.PositionAdjustPairDefinition):
            for (idx1, idx2), (pos1, pos2) in pos.adjust_pair.items():
                coverage_1 = pos.coverages_1[idx1 - 1]
                coverage_2 = pos.coverages_2[idx2 - 1]

                # If not both are groups, use “enum pos” otherwise makeotf will
                # fail.
                enumerated = False
                for item in coverage_1 + coverage_2:
                    if not isinstance(item, VAst.GroupName):
                        enumerated = True

                glyphs1 = self._coverage(coverage_1)
                glyphs2 = self._coverage(coverage_2)
                record1 = self._adjustment(pos1)
                record2 = self._adjustment(pos2)
                assert len(glyphs1) == 1
                assert len(glyphs2) == 1
                statements.append(
                    ast.PairPosStatement(
                        glyphs1[0], record1, glyphs2[0], record2, enumerated=enumerated
                    )
                )
        elif isinstance(pos, VAst.PositionAdjustSingleDefinition):
            for a, b in pos.adjust_single:
                glyphs = self._coverage(a)
                record = self._adjustment(b)
                assert len(glyphs) == 1
                statements.append(
                    ast.SinglePosStatement([(glyphs[0], record)], [], [], False)
                )
        elif isinstance(pos, VAst.PositionAttachDefinition):
            anchors = {}
            for marks, classname in pos.coverage_to:
                for mark in marks:
                    # Set actually used mark classes. Basically a hack to get
                    # around the feature file syntax limitation of making mark
                    # classes global and not allowing mark positioning to
                    # specify mark coverage.
                    for name in mark.glyphSet():
                        key = (name, "MARK_" + classname)
                        self._markclasses[key].used = True
                markclass = ast.MarkClass(self._className(classname))
                for base in pos.coverage:
                    for name in base.glyphSet():
                        if name not in anchors:
                            anchors[name] = []
                        if classname not in anchors[name]:
                            anchors[name].append(classname)

            for name in anchors:
                components = 1
                if name in self._ligatures:
                    components = self._ligatures[name]

                marks = []
                for mark in anchors[name]:
                    markclass = ast.MarkClass(self._className(mark))
                    for component in range(1, components + 1):
                        if len(marks) < component:
                            marks.append([])
                        anchor = None
                        if component in self._anchors[name][mark]:
                            anchor = self._anchors[name][mark][component]
                        marks[component - 1].append((anchor, markclass))

                base = self._glyphName(name)
                if name in self._marks:
                    mark = ast.MarkMarkPosStatement(base, marks[0])
                elif name in self._ligatures:
                    mark = ast.MarkLigPosStatement(base, marks)
                else:
                    mark = ast.MarkBasePosStatement(base, marks[0])
                statements.append(mark)
        elif isinstance(pos, VAst.PositionAttachCursiveDefinition):
            # Collect enter and exit glyphs
            enter_coverage = []
            for coverage in pos.coverages_enter:
                for base in coverage:
                    for name in base.glyphSet():
                        enter_coverage.append(name)
            exit_coverage = []
            for coverage in pos.coverages_exit:
                for base in coverage:
                    for name in base.glyphSet():
                        exit_coverage.append(name)

            # Write enter anchors, also check if the glyph has exit anchor and
            # write it, too.
            for name in enter_coverage:
                glyph = self._glyphName(name)
                entry = self._anchors[name]["entry"][1]
                exit = None
                if name in exit_coverage:
                    exit = self._anchors[name]["exit"][1]
                    exit_coverage.pop(exit_coverage.index(name))
                statements.append(ast.CursivePosStatement(glyph, entry, exit))

            # Write any remaining exit anchors.
            for name in exit_coverage:
                glyph = self._glyphName(name)
                exit = self._anchors[name]["exit"][1]
                statements.append(ast.CursivePosStatement(glyph, None, exit))
        else:
            raise NotImplementedError(pos)

    def _gposContextLookup(
        self, lookup, prefix, suffix, ignore, fealookup, targetlookup
    ):
        statements = fealookup.statements

        assert not lookup.reversal

        pos = lookup.pos
        if isinstance(pos, VAst.PositionAdjustPairDefinition):
            for (idx1, idx2), (pos1, pos2) in pos.adjust_pair.items():
                glyphs1 = self._coverage(pos.coverages_1[idx1 - 1])
                glyphs2 = self._coverage(pos.coverages_2[idx2 - 1])
                assert len(glyphs1) == 1
                assert len(glyphs2) == 1
                glyphs = (glyphs1[0], glyphs2[0])

                if ignore:
                    statement = ast.IgnorePosStatement([(prefix, glyphs, suffix)])
                else:
                    lookups = (targetlookup, targetlookup)
                    statement = ast.ChainContextPosStatement(
                        prefix, glyphs, suffix, lookups
                    )
                statements.append(statement)
        elif isinstance(pos, VAst.PositionAdjustSingleDefinition):
            glyphs = [ast.GlyphClass()]
            for a, b in pos.adjust_single:
                glyph = self._coverage(a)
                glyphs[0].extend(glyph)

            if ignore:
                statement = ast.IgnorePosStatement([(prefix, glyphs, suffix)])
            else:
                statement = ast.ChainContextPosStatement(
                    prefix, glyphs, suffix, [targetlookup]
                )
            statements.append(statement)
        elif isinstance(pos, VAst.PositionAttachDefinition):
            glyphs = [ast.GlyphClass()]
            for coverage, _ in pos.coverage_to:
                glyphs[0].extend(self._coverage(coverage))

            if ignore:
                statement = ast.IgnorePosStatement([(prefix, glyphs, suffix)])
            else:
                statement = ast.ChainContextPosStatement(
                    prefix, glyphs, suffix, [targetlookup]
                )
            statements.append(statement)
        else:
            raise NotImplementedError(pos)

    def _gsubLookup(self, lookup, prefix, suffix, ignore, chain, routine):
        sub = lookup.sub
        for key, val in sub.mapping.items():
            if not key or not val:
                path, line, column = sub.location
                log.warning(f"{path}:{line}:{column}: Ignoring empty substitution")
                continue
            statement = None
            glyphs = self._coverage(key)
            replacements = self._coverage(val)
            if ignore:
                chain_context = (prefix, glyphs, suffix)
                statement = ast.IgnoreSubstStatement([chain_context])
            else:
                statement = Substitution(
                    glyphs,
                    replacements,
                    precontext=prefix,
                    postcontext=suffix,
                    lookups=chain
                )
                if isinstance(sub, VAst.SubstitutionReverseChainingSingleDefinition):
                    statement.reversed = True
            routine.rules.append(statement)

    def _lookupDefinition(self, lookup):
        mark_attachement = None
        mark_filtering = None

        flags = 0
        if lookup.direction == "RTL":
            flags |= 1
        if not lookup.process_base:
            flags |= 2
        # FIXME: Does VOLT support this?
        # if not lookup.process_ligatures:
        #     flags |= 4
        if not lookup.process_marks:
            flags |= 8
        elif isinstance(lookup.process_marks, str):
            mark_attachement = self._groupName(lookup.process_marks)
        elif lookup.mark_glyph_set is not None:
            mark_filtering = self._groupName(lookup.mark_glyph_set)
        if "\\" in lookup.name:
            # Merge sub lookups as subtables (lookups named “base\sub”),
            # makeotf/feaLib will issue a warning and ignore the subtable
            # statement if it is not a pairpos lookup, though.
            name = lookup.name.split("\\")[0]
            if name.lower() not in self._lookups:
                fealookup = ast.LookupBlock(self._lookupName(name))
                if lookupflags is not None:
                    fealookup.statements.append(lookupflags)
                fealookup.statements.append(ast.Comment("# " + lookup.name))
            else:
                fealookup = self._lookups[name.lower()]
                fealookup.statements.append(ast.SubtableStatement())
                fealookup.statements.append(ast.Comment("# " + lookup.name))
            self._lookups[name.lower()] = fealookup
        else:
            routine = Routine(name=lookup.name, flags=flags,
                markFilteringSet = mark_filtering,
                markAttachmentSet = mark_attachement)
            self.ff.routines.append(routine)
            self._lookups[lookup.name.lower()] = routine

        contexts = []
        if lookup.context:
            for context in lookup.context:
                prefix = self._context(context.left)
                suffix = self._context(context.right)
                ignore = context.ex_or_in == "EXCEPT_CONTEXT"
                contexts.append([prefix, suffix, ignore, False])
                # It seems that VOLT will create contextual substitution using
                # only the input if there is no other contexts in this lookup.
                if ignore and len(lookup.context) == 1:
                    contexts.append([[], [], False, True])
        else:
            contexts.append([[], [], False, False])

        targetlookup = None
        for prefix, suffix, ignore, chain in contexts:
            if lookup.sub is not None:
                self._gsubLookup(lookup, prefix, suffix, ignore, chain, routine)

            if lookup.pos is not None:
                if self._settings.get("COMPILER_USEEXTENSIONLOOKUPS"):
                    fealookup.use_extension = True
                if prefix or suffix or chain or ignore:
                    if not ignore and targetlookup is None:
                        targetname = self._lookupName(lookup.name + " target")
                        targetlookup = ast.LookupBlock(targetname)
                        fealookup.targets = getattr(fealookup, "targets", [])
                        fealookup.targets.append(targetlookup)
                        self._gposLookup(lookup, targetlookup)
                    self._gposContextLookup(
                        lookup, prefix, suffix, ignore, fealookup, targetlookup
                    )
                # else:
                    # self._gposLookup(lookup, fealookup)


def main(args=None):
    import argparse

    parser = argparse.ArgumentParser(description="Convert VOLT/VTP to feature files.")
    parser.add_argument("input", metavar="INPUT", help="input font/VTP file to process")
    parser.add_argument("featurefile", metavar="FEATUEFILE", help="output feature file")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress non-error messages"
    )
    parser.add_argument(
        "--traceback", action="store_true", help="Don’t catch exceptions"
    )

    options = parser.parse_args(args)

    if options.quiet:
        log.setLevel(logging.ERROR)
    logging.basicConfig(format="%(levelname)s: %(message)s")

    file_or_path = options.input
    font = None
    try:
        font = TTFont(file_or_path)
        if "TSIV" in font:
            file_or_path = StringIO(font["TSIV"].data.decode("utf-8"))
        else:
            log.error('"TSIV" table is missing, font was not saved from VOLT?')
            return 1
    except TTLibError:
        pass

    converter = VoltParser(file_or_path, font)
    try:
        ff = converter.convert()
    except NotImplementedError as e:
        if options.traceback:
            raise
        location = getattr(e.args[0], "location", None)
        message = f'"{e}" is not supported'
        if location:
            path, line, column = location
            log.error(f"{path}:{line}:{column}: {message}")
        else:
            log.error(message)
        return 1
    print(ff.asFea())


if __name__ == "__main__":
    import sys

    sys.exit(main())
