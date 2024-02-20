# Code for converting a Attachment object into feaLib statements
import fontTools.feaLib.ast as feaast
from glyphtools import categorize_glyph
import warnings
from fontTools.feaLib.variableScalar import VariableScalar


def fix_scalar(scalar):
    if isinstance(scalar, int):
        return scalar
    if isinstance(scalar, float):
        return int(scalar)
    if hasattr(scalar, "axes"):
        # assume it's a variable scalar of some kind
        return scalar
    raise ValueError("Illegal anchor position %s" % scalar)

def _glyphref(g):
    if len(g) == 1:
        return feaast.GlyphName(g[0])
    return feaast.GlyphClass([feaast.GlyphName(x) for x in g])


def sortByAnchor(self):
    anchors = {}
    for name, pos in self.marks.items():
        if not pos in anchors:
            anchors[pos] = []
        anchors[pos].append(name)
    self.markslist = [(v, k) for k, v in anchors.items()]

    anchors = {}
    for name, pos in self.bases.items():
        if not pos in anchors:
            anchors[pos] = []
        anchors[pos].append(name)
    self.baseslist = [(v, k) for k, v in anchors.items()]


def feaPreamble(self, ff):
    if self.is_cursive:
        return []
    sortByAnchor(self)
    if not "mark_classes_done" in ff.scratch:
        ff.scratch["mark_classes_done"] = {}
    b = feaast.Block()
    fullname = self.base_name + "_" + self.mark_name
    for mark in self.markslist:
        if not (fullname, tuple(mark[0])) in ff.scratch["mark_classes_done"]:
            b.statements.append(
                feaast.MarkClassDefinition(
                    feaast.MarkClass(fullname),
                    feaast.Anchor(fix_scalar(mark[1][0]), fix_scalar(mark[1][1])),
                    _glyphref(mark[0]),
                )
            )
            ff.scratch["mark_classes_done"][(fullname, tuple(mark[0]))] = True
    return [b]


def asFeaAST(self):
    b = feaast.Block()
    if self.is_cursive:
        allglyphs = set(self.bases.keys()) | set(self.marks.keys())
        for g in allglyphs:
            b.statements.append(
                feaast.CursivePosStatement(
                    _glyphref([g]),
                    g in self.bases and feaast.Anchor(fix_scalar(self.bases[g][0]),fix_scalar(self.bases[g][1])),
                    g in self.marks and feaast.Anchor(fix_scalar(self.marks[g][0]),fix_scalar(self.marks[g][1])),
                )
            )
    else:
        if not hasattr(self, "baseslist"):
            sortByAnchor(self)  # e.g. when testing
        for base in self.baseslist:
            statementtype = feaast.MarkBasePosStatement
            fullname = self.base_name + "_" + self.mark_name
            if self.font:
                if categorize_glyph(self.font, base[0][0])[0] == "mark":
                    statementtype = feaast.MarkMarkPosStatement
            if self.force_markmark:
                statementtype = feaast.MarkMarkPosStatement
            b.statements.append(
                statementtype(
                    _glyphref(base[0]),
                    [[feaast.Anchor(fix_scalar(base[1][0]), fix_scalar(base[1][1])), feaast.MarkClass(fullname)]],
                )
            )

    return b
