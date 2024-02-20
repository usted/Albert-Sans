"""ttLib: Interfacing with TrueType fonts.

This package contains routines for converting between fontTools objects
(representing TrueType/OpenType fonts) and fontFeatures. This particular
module is mainly concerned with getting information out of binary OTF/TTF
fonts and into fontFeatures."""
from collections import OrderedDict

from .GDEFUnparser import GDEFUnparser
from .GSUBUnparser import GSUBUnparser
from .GPOSUnparser import GPOSUnparser


def unparseLanguageSystems(tables):
    """Build a set of script / language pairs from a GSUB/GPOS table.

    Args:
        tables: A list of ``fontTools.ttLib.tables.G_S_U_B_.table_G_S_U_B_`` /
            ``fontTools.ttLib.tables.G_P_O_S_.table_G_P_O_S_`` objects.

    Returns an ordered dictionary whose keys are four-character script tags and
      whose values are a set of four-character language tags.
    """
    scripts = OrderedDict()
    for table in tables:
        if not table.table.ScriptList:
            continue
        for scriptRecord in table.table.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            languages = scripts.get(scriptTag, [])
            script = scriptRecord.Script
            items = []
            if script.DefaultLangSys is not None:
                items.append(("dflt", script.DefaultLangSys))
            items += [(l.LangSysTag, l.LangSys) for l in script.LangSysRecord]
            languages = set([i[0] for i in items])

            if languages and not scriptTag in scripts:
                scripts[scriptTag] = languages

    return scripts


def unparse(font, do_gdef=False, doLookups=True, config={}):
    """Convert a binary OpenType font into a fontFeatures object

    Args:
        font: A ``TTFont`` object.
        do_gdef: Boolean. Whether the GDEF table should also be read.
        doLookups: Whether the lookups should be read, or just the script/language
            information and top-level features.
        config: A dictionary of glyph class and routine names.
    """
    gsub_gpos = [font[tableTag] for tableTag in ("GSUB", "GPOS") if tableTag in font]
    from fontFeatures import FontFeatures
    ff = FontFeatures()

    languageSystems = unparseLanguageSystems(gsub_gpos)

    if "GSUB" in font:
        GSUBUnparser(
            font["GSUB"], ff, languageSystems, font=font, config=config
        ).unparse(doLookups=doLookups)

    if "GPOS" in font:
        GPOSUnparser(
            font["GPOS"], ff, languageSystems, font=font, config=config
        ).unparse(doLookups=doLookups)

    if "GDEF" in font and do_gdef:
        GDEFUnparser(font["GDEF"], ff).unparse()

    return ff
