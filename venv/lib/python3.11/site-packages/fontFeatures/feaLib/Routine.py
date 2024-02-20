# Code for converting a Routine object into feaLib statements
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type as sub_lookup_type
from fontFeatures.ttLib.Positioning import lookup_type as pos_lookup_type
from fontFeatures.feaLib import bad_statement_to_comment
import copy


def lookup_type(rule):
    from fontFeatures import Substitution, Positioning, Attachment, Chaining

    if isinstance(rule, Substitution):
        return sub_lookup_type(rule)
    if isinstance(rule, Positioning):
        return pos_lookup_type(rule)
    if isinstance(rule, Attachment):
        return rule.is_cursive
    if isinstance(rule, Chaining):
        return 1
    raise ValueError


counter = 0


def gensym(prefix):
    global counter
    counter = counter + 1
    return prefix + str(counter)

def feaPreamble(self, ff):
    preamble = []
    for r in self.rules:
        preamble.extend(r.feaPreamble(ff))
    if self.flags & 0xFF00:
        assert(self.markAttachmentSet is not None)
        self.markAttachmentSetAsClass = ff.getNamedClassFor(self.markAttachmentSet, gensym("markAttachmentSet"))
    if self.flags & 0x10:
        assert(self.markFilteringSet is not None)
        self.markFilteringSetAsClass = ff.getNamedClassFor(self.markFilteringSet, gensym("markFilteringSet"))
    return preamble


def asFeaAST(self):
    if self.name:
        f = feaast.LookupBlock(name=self.name)
    else:
        f = feaast.Block()

    if hasattr(self, "flags"):
        flags = feaast.LookupFlagStatement(self.flags)
        if self.flags & 0x10 and hasattr(self, "markFilteringSetAsClass"): # XXX
            # We only need the name, not the contents
            mfs = feaast.GlyphClassDefinition(self.markFilteringSetAsClass,
                feaast.GlyphClass([])
            )
            flags.markFilteringSet = feaast.GlyphClassName(mfs)
        if self.flags & 0xFF00 and hasattr(self, "markAttachmentSetAsClass"): # XXX
            mfs = feaast.GlyphClassDefinition(self.markAttachmentSetAsClass,
                feaast.GlyphClass([])
            )
            flags.markAttachment=feaast.GlyphClassName(mfs)

        f.statements.append(flags)

    for x in self.comments:
        f.statements.append(feaast.Comment(x))

    f.statements.append(feaast.Comment(";"))
    lastaddress = self.address
    if lastaddress:
        f.statements.append(feaast.Comment("# Original source: %s " % (" ".join([str(x) for x in lastaddress]))))
    for x in self.rules:
        if x.address and x.address != lastaddress:
            f.statements.append(feaast.Comment("# Original source: %s " % x.address))
            lastaddress = x.address
        if hasattr(x, "note"):
            f.statements.append(feaast.Comment("\n".join([ f"# {n}" for n in x.note.split("\n")])))
        f.statements.append(bad_statement_to_comment(x.asFeaAST()))
    return f


def asFea(self):
    return self.asFeaAST().asFea()
