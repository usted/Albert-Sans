# Code for converting a Substitution object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type
from itertools import cycle
from typing import Union

def glyphref(g) -> Union[feaast.GlyphName, feaast.GlyphClass]:
    if len(g) == 1:
        return feaast.GlyphName(g[0])
    return feaast.GlyphClass([feaast.GlyphName(x) for x in g])

# Whether or not the input or the replacement has classes (so, entire statement).
def has_classes(self) -> bool:
    input_has_class = next((i for i,v in enumerate([len(x) for x in self.input]) if v>1), None)
    replacement_has_class = next((i for i,v in enumerate([len(x) for x in self.replacement]) if v>1), None)

    return (input_has_class is not None or replacement_has_class is not None)

# Excepting single glyphs, if classes are defined, the input and replacement
# all use classes of equal length.
def all_classes_equal(self) -> bool:
    input_lengths = [len(x) for x in self.input if len(x) != 1]
    replacement_lengths = [len(x) for x in self.replacement if len(x) != 1]

    if len(input_lengths) == 0 and len(replacement_lengths) == 0:
        return True

    return len(set(input_lengths+replacement_lengths)) == 1

# One of the substitution/replacements has all-but-one arity one,
# and both arities are the same
def is_paired(self) -> bool:
    input_lengths = [len(x) for x in self.input if len(x) != 1]
    replacement_lengths = [len(x) for x in self.replacement if len(x) != 1]
    if not (len(input_lengths) == 1 and len(replacement_lengths) == 1):
        return False
    if input_lengths[0] != replacement_lengths[0]:
        import warnings
        warnings.warn("Unbalanced paired substitution")
        return False
    return True

# Expand ligature substitutions ending in a class, such that:
#   * Substitute [f f.ss01] i -> [f_i f_i.ss01];
# Expands to:
#   * sub f i -> f_i;
#   * sub f.ss01 i -> f_i.ss01;
# Likewise:
#   * Substitute [f f.ss01] [i i.ss01] -> [f_i f_i.ss01];
# Expands to:
#   * sub f i -> f_i;
#   * sub f.ss01 i.ss01 -> f_i.ss01;
def paired_ligature(self) -> feaast.LigatureSubstStatement:
    b = feaast.Block()
    inputs = []
    for i in self.input:
        if len(i) == 1:
            inputs.append(cycle(i))
        else:
            inputs.append(i)
    lhs = zip(*inputs)
    replacements = []
    for j in self.replacement:
        if len(j) == 1:
            replacements.append(cycle(j))
        else:
            replacements.append(j)
    rhs = zip(*replacements)

    for l, r in zip(lhs,rhs):
        stmt = feaast.LigatureSubstStatement(
            [glyphref(x) for x in self.precontext],
            [glyphref([x]) for x in l],
            [glyphref(x) for x in self.postcontext],
            glyphref([r[0]]),
            False,
        )
        b.statements.append(stmt)
    return b

# Expand multiple substitutions, such that:
#   * Substitute [a b] -> before_tail [a.2 b.2] tail;
# Becomes in FEA:
#   * sub a by before_tail a.2 tail;
#   * sub b by before_tail b.2 tail;
def paired_mult(self) -> feaast.MultipleSubstStatement:
    b = feaast.Block()

    input_lengths = [len(x) for x in self.input]
    replacement_lengths = [len(x) for x in self.replacement]

    if len(input_lengths) != 1:
        raise ValueError("Multiple substitution only valid on input of length one, use a Chain instead")

    input_length = input_lengths[0]

    if not sum([l for l in replacement_lengths if l == 1]) in [len(replacement_lengths), len(replacement_lengths)-1]:
        raise ValueError("Cannot expand multiple glyph classes in a multiple substitution — creates ambiguity")

    # Look for the glyph class in the replacement, or default to first glyph in replacement
    glyphcls = next((i for i, v in enumerate(self.replacement) if len(v)> 1), 0)

    if input_length != len(self.replacement[glyphcls]):
        raise ValueError("Glyph class in input must be same length as that in replacement. {} != {}".format(input_length, len(self.replacement[glyphcls])))

    zipped = zip(self.input[0], self.replacement[glyphcls])

    prior_reps = self.replacement[:glyphcls]
    after_reps = self.replacement[glyphcls+1:]

    for f, t in zipped:
        stmt = feaast.MultipleSubstStatement(
            [glyphref(x) for x in self.precontext],
            glyphref([f]),
            [glyphref(x) for x in self.postcontext],
            [glyphref(g) for g in prior_reps+[[t]]+after_reps]
        )
        b.statements.append(stmt)

    return b

def asFeaAST(self):
    lut = lookup_type(self, forFea=True)
    if not lut:
        return feaast.Comment("")

    if not self.replacement: # Delete
        return feaast.MultipleSubstStatement(
            [glyphref(x) for x in self.precontext],
            glyphref(self.input[0]),
            [glyphref(x) for x in self.postcontext],
            [],
        )

    if lut == 1: # GSUB 1 Single Substitution
        return feaast.SingleSubstStatement(
            [glyphref(x) for x in self.input],
            [glyphref(x) for x in self.replacement],
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.postcontext],
            False,
        )
    elif lut == 2: # GSUB 2 Multiple Substitution
        # Paired rules need to become a set of statements
        if is_paired(self):
            return paired_mult(self)

        return feaast.MultipleSubstStatement(
            [glyphref(x) for x in self.precontext],
            glyphref(self.input[0]),
            [glyphref(x) for x in self.postcontext],
            [glyphref(x) for x in self.replacement],
        )
    elif lut == 3: # GSUB 3 Alternate Substitution
        return feaast.AlternateSubstStatement(
            [glyphref(x) for x in self.precontext],
            glyphref(self.input[0]),
            [glyphref(x) for x in self.postcontext],
            feaast.GlyphClass([feaast.GlyphName(x) for x in self.replacement[0]]),
        )
    elif lut == 4: # GSUB 4 Ligature Substitution
        # Some rules with classes need to become a set of statements.
        if has_classes(self) and all_classes_equal(self) and not len(self.replacement[0]) == 1:
            return paired_ligature(self)

        return feaast.LigatureSubstStatement(
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.input],
            [glyphref(x) for x in self.postcontext],
            glyphref(self.replacement[0]),
            False,
        )
    elif lut in [5, 6, 7]: # GSUB 5, 6, 7 Different types of contextual substitutions
        raise NotImplementedError("Use the Chain verb for this")
    elif lut == 8: # GSUB 8 Reverse Chaining Single Substitution
        return feaast.ReverseChainSingleSubstStatement(
            [glyphref(x) for x in self.precontext],
            [glyphref(x) for x in self.postcontext],
            [glyphref(x) for x in self.input],
            [glyphref(self.replacement[0])],
        )
    elif lut >= 9:
        raise NotImplementedError("Invalid GSUB lookup type requested: {}".format(lut))

    raise ValueError("LookupType must be a single positive integer")
