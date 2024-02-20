"""ttLib.ValueRecord: Converting ValueRecord rules to TrueType."""

from fontTools.ttLib.tables.otBase import ValueRecord as OTLValueRecord
from fontTools.feaLib.variableScalar import VariableScalar
from fontTools.varLib.builder import buildVarDevTable


def toOTValueRecord(self, ff, pairPosContext=False):
    """Converts the ValueRecord to an ``OTLValueRecord`` object. If the
    value record contains any variable scalars, they are saved to the
    GDEF variation store."""
    otl_value = OTLValueRecord()
    if pairPosContext and not self:
        self.XAdvance = 0
    for item in ["xPlacement", "yPlacement", "xAdvance", "yAdvance"]:
        itemvalue = getattr(self, item)
        if not itemvalue:
            continue
        item = item[0].upper() + item[1:]
        if isinstance(itemvalue, VariableScalar):
            itemvalue, index = itemvalue.add_to_variation_store(ff.varstorebuilder)
            if index != 0xFFFF:
                setattr(otl_value, item[0:4]+"Device", buildVarDevTable(index))
        setattr(otl_value, item, itemvalue)
    return otl_value
