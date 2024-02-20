"""Routines for converting RoutineReference objects to and from Adobe FEA."""
import fontTools.feaLib.ast as feaast
from fontFeatures.ttLib.Substitution import lookup_type as sub_lookup_type
from fontFeatures.ttLib.Positioning import lookup_type as pos_lookup_type

def feaPreamble(self, ff):
    return []


def asFeaAST(self, expand=False):
    # if self.routine.usecount == 1:
    #     return self.routine.asFeaAST()
    f = feaast.Block()
    f.statements.append(feaast.LookupReferenceStatement(self.routine.asFeaAST()))
    return f

