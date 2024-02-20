# Code for converting a Chaining object into feaLib statements
import fontTools.feaLib.ast as feaast
import fontFeatures


# Can we chain multiple lookups?
from fontTools.feaLib.parser import Parser
import io


def glyphref(g):
    if len(g) == 1:
        return feaast.GlyphName(g[0])
    return feaast.GlyphClass([feaast.GlyphName(x) for x in g])



def gensym(ff):
    if not "index" in ff.scratch:
        ff.scratch["index"] = 0
    ff.scratch["index"] = ff.scratch["index"] + 1
    return str(ff.scratch["index"])


def replaceLongWithClasses(i, ff):
    for ix, gc in enumerate(i):
        if len(gc) > 5:
            classname = ff.getNamedClassFor(sorted(gc), "class" + gensym(ff))
            i[ix] = ["@" + classname]


def feaPreamble(self, ff):
    if not "glyphclasses" in ff.scratch:
        ff.scratch["glyphclasses"] = {tuple(sorted(ff.namedClasses[g])): g for g in ff.namedClasses.keys()}
    replaceLongWithClasses(self.input, ff)
    replaceLongWithClasses(self.precontext, ff)
    replaceLongWithClasses(self.postcontext, ff)
    from fontFeatures import RoutineReference

    # Ensure all linked routines have names
    for lul in self.lookups:
        for r in (lul or []):
            assert isinstance(r, RoutineReference)
            assert r.routine
            if not r.routine.name:
                r.routine.name = "ChainedRoutine"+gensym(ff)
            if not r.name:
                r.name = r.routine.name

    return []


def _complex(self):
    if self.stage == "sub":
        routine = feaast.ChainContextSubstStatement
    else:
        routine = feaast.ChainContextPosStatement

    return routine(
        [glyphref(x) for x in self.precontext],
        [glyphref(x) for x in self.input],
        [glyphref(x) for x in self.postcontext],
        self.lookups,
    )


def asFeaAST(self):
    if len(self.lookups) > 0 and any([x is not None for x in self.lookups]):
        # Fill in the blanks
        if self.stage == "sub":
            routine = feaast.ChainContextSubstStatement
        else:
            routine = feaast.ChainContextPosStatement
        # Check for >1 lookups per position
        if any([x and len(x) > 1 for x in self.lookups]):
            return _complex(self)
        lookups = self.lookups
        return routine(
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.input],
            [glyphref(x) for x in self.postcontext],
            lookups,
        )
    else:
        return feaast.IgnoreSubstStatement(
            chainContexts=[
                [
                    [glyphref(x) for x in self.precontext],
                    [glyphref(x) for x in self.input],
                    [glyphref(x) for x in self.postcontext],
                ]
            ]
        )

