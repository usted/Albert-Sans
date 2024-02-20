"""The base class for complex shapers.

Shaper.py is the top-level interface to shaperlib. This is a lower-level
module implementing common routines used to the individual complex shapers."""

from fontFeatures.shaperLib.Buffer import Buffer, BufferItem
from copy import copy
import unicodedata
from youseedee import ucd_data
from fontFeatures import RoutineReference



def _is_default_ignorable(c):
    return (
        c in [0x00AD, 0x034F, 0x061C, 0x17B4, 0x17B5, 0xFEFF]
        or 0x180B <= c <= 0x180E
        or 0x200B <= c <= 0x200F
        or 0x202A <= c <= 0x202E
        or 0x2060 <= c <= 0x206F
        or 0xFE00 <= c <= 0xFE0F
        or 0xFFF0 <= c <= 0xFFF8
        or 0x1D173 <= c <= 0x1D17A
        or 0xE0000 <= c <= 0xE0FFF
    )


class BaseShaper:
    """A complex shaper object."""
    def __init__(self, plan, font, buf, features=[]):
        self.plan = plan
        self.font = font
        self.buffer = buf
        self.features = features

    def shape(self):
        """Shape a buffer."""
        self.plan.fontfeatures.resolveAllRoutines()
        # self.buffer.set_unicode_props()
        # self.insert_dotted_circles()
        # self.buffer.form_clusters()
        # self.buffer.ensure_native_direction()
        if not self.buffer.is_all_glyphs:
            self.preprocess_text()
            # Substitute pre
            self.substitute_default()
        self.substitute_complex()
        # Substitute post
        self.delete_default_ignorables()

        self.position()
        self.postprocess_glyphs()
        # self.buffer.propagate_flags()

    def preprocess_text(self):
        """Do any processing which needs to happen to character items before shaping."""
        pass

    def postprocess_glyphs(self):
        """Do any processing which needs to happen to glyph items after shaping."""
        pass

    def substitute_default(self):
        """Do initial subsitution processing: buffer normalization and mapping."""
        self.normalize_unicode_buffer()
        self.buffer.map_to_glyphs()
        self.plan.msg("Initial glyph mapping", self.buffer)
        # Setup masks
        # if self.buf.fallback_mark_positioning:
        # self.fallback_mark_position_recategorize_marks()
        pass

    def normalize_unicode_buffer(self):
        """Normalize an OpenType buffer."""
        unistring = "".join([chr(item.codepoint) for item in self.buffer.items])
        self.buffer.store_unicode(unicodedata.normalize("NFC", unistring))

        # Some fix-ups from hb-ot-shape-normalize
        for item in self.buffer.items:
            if ucd_data(item.codepoint)[
                "General_Category"
            ] == "Zs" and self.font.unicode_map.get(0x20, None):
                item.codepoint = 0x20
                # Harfbuzz adjusts the width here, in _hb_ot_shape_fallback_spaces
            if item.codepoint == 0x2011 and self.font.unicode_map.get(0x2010, None):
                item.codepoint = 0x2010

    def collect_features(self, shaper):
        """Collect all complex features to be run by this shaper. (Abstract method.)"""
        return []

    def substitute_complex(self):
        """Run the substitution stage."""
        self._run_stage("sub")

    def position(self):
        """Run the positioning stage."""
        self._run_stage("pos")
        self.buffer.clear_mask()
        # zero width marks
        for i in self.buffer.items:
            if i.category[0] == "mark":
                i.position.xAdvance = 0
        # zero width default ignorables
        self.zero_width_default_ignorables()
        for i in range(0,len(self.buffer.items)):
            self.propagate_attachment_offsets(i)
        self.plan.msg("Positioning done", self.buffer)

    def propagate_attachment_offsets(self, i):
        """Resolve attachment offsets for item ``i``."""
        if not hasattr(self.buffer.items[i], "attach_type"):
            return
        attach_type = self.buffer.items[i].attach_type
        attach_chain = self.buffer.items[i].attach_chain
        if not attach_chain:
            return
        self.buffer.items[i].attach_chain = None
        j = i + attach_chain
        if j >= len(self.buffer.items):
            return
        self.propagate_attachment_offsets(j)
        if attach_type == "cursive":
            pass
            # self.buffer.items[i].position.yPlacement = (self.buffer.items[i].position.yPlacement or 0) + (self.buffer.items[j].position.yPlacement or 0) # XXX Horizontal only
        else:
            self.buffer.items[i].position.xPlacement += self.buffer.items[j].position.xPlacement or 0
            self.buffer.items[i].position.yPlacement += self.buffer.items[j].position.yPlacement or 0
            assert j < i
            if self.buffer.direction == "LTR":
                for k in range(j,i):
                    self.buffer.items[i].position.xPlacement -= self.buffer.items[k].position.xAdvance
                    self.buffer.items[i].position.yPlacement -= self.buffer.items[k].position.yAdvance or 0
            else:
                for k in range(j+1,i+1):
                    self.buffer.items[i].position.xPlacement += self.buffer.items[k].position.xAdvance
                    self.buffer.items[i].position.yPlacement += self.buffer.items[k].position.yAdvance or 0


    def _run_stage(self, current_stage):
        self.plan.msg("Running %s stage" % current_stage)
        self.plan.fontfeatures.hoist_languages()
        for stage in self.plan.stages:
            lookups = []
            if isinstance(stage, list):  # Features
                for f in stage:
                    if f not in self.plan.fontfeatures.features:
                        continue

                    routines = self.plan.fontfeatures.features[f]
                    routines = [x.routine if isinstance(x, RoutineReference) else x for x in routines]
                    lookups.extend(
                        [(routine, f) for routine in self._filter_by_lang(routines)]
                    )
                self.plan.msg("Processing features: %s" % ",".join(stage))
                for r, feature in lookups:
                    self.plan.msg(
                        "Before %s (%s)" % (r.name, feature), buffer=self.buffer
                    )
                    r.apply_to_buffer(self.buffer, stage=current_stage, feature=feature, namedclasses=self.plan.fontfeatures.namedClasses)
                    self.plan.msg(
                        "After %s (%s)" % (r.name, feature), buffer=self.buffer
                    )
            else:
                # It's a pause. We only support GSUB pauses.
                if current_stage == "sub":
                    stage(current_stage)

    def _filter_by_lang(self, routines):
        script = self.script_to_opentype.get(self.buffer.script,"DFLT")
        s_l = self.plan.fontfeatures.scripts_and_languages
        if not self.buffer.script or len(s_l.values()) < 2 and (
            len(s_l.values()) == 0 or len(list(s_l.values())[0]) < 2):
            return routines # !
        language = self.buffer.language or "dflt"
        if script in s_l and (script, language) != ("DFLT", "dflt"):
            return [x for x in routines if x.languages and (script, language) in x.languages]
        else:
            return [x for x in routines if not x.languages or ("DFLT", language) in x.languages]

    def delete_default_ignorables(self):
        """Remove all items from the buffer which are ignorable."""
        self.buffer.items = [x for x in self.buffer.items if not(x.codepoint) or not _is_default_ignorable(x.codepoint)]

    def zero_width_default_ignorables(self):
        """Set all items from the buffer which are ignorable to zero advance width."""
        space = BufferItem.new_unicode(0x20)
        space.map_to_glyph(self.buffer.font)
        if space.glyph == -1:
            return
        for ix, item in enumerate(self.buffer.items):
            if item.codepoint and _is_default_ignorable(item.codepoint):
                item.glyph = space.glyph
                item.position.xAdvance = 0
                for i in self.buffer.items[ix:]:
                    if hasattr(i, "syllable_index"):
                        i.syllable_index += 1

    def would_substitute(self, feature, subbuffer_items):
        """Test whether the feature would apply to a list of BufferItem objects."""
        if not feature in self.plan.fontfeatures.features:
            return False
        subbuffer = Buffer(
            self.buffer.font,
            direction=self.buffer.direction,
            script=self.buffer.script,
            language=self.buffer.language,
        )
        subbuffer.clear_mask()
        subbuffer.items = [copy(x) for x in subbuffer_items]
        subbuffer.clear_mask()
        routines = self.plan.fontfeatures.features[feature]
        for r in routines:
            if isinstance(r, RoutineReference):
                r = r.routine
            for rule in r.rules:
                if rule.stage == "pos":
                    continue
                if any(
                    [
                        rule.would_apply_at_position(subbuffer, i, namedclasses=self.plan.fontfeatures.namedClasses)
                        for i in range(len(subbuffer))
                    ]
                ):
                    return True
        return False

    script_to_opentype = {
        "Common": "zyyy",
        "Inherited": "zinh",
        "Unknown": "zzzz",
        "Arabic": "arab",
        "Armenian": "armn",
        "Bengali": "bng2", # Not beng
        "Cyrillic": "cyrl",
        "Devanagari": "dev2", # Not deva
        "Georgian": "geor",
        "Greek": "grek",
        "Gujarati": "gjr2", # Not gujr
        "Gurmukhi": "gur2", # Not guru
        "Hangul": "hang",
        "Han": "hani",
        "Hebrew": "hebr",
        "Hiragana": "hira",
        "Kannada": "knd2", # Not knda
        "Katakana": "kana",
        "Lao": "laoo",
        "Latin": "latn",
        "Malayalam": "mlm2", # Not mlym
        "Oriya": "ory2", # Not orya
        "Tamil": "tml2", # Not taml
        "Telugu": "tel2", # Not telu
        "Thai": "thai",
        "Tibetan": "tibt",
        "Bopomofo": "bopo",
        "Braille": "brai",
        "Canadian_Syllabics": "cans",
        "Cherokee": "cher",
        "Ethiopic": "ethi",
        "Khmer": "khmr",
        "Mongolian": "mong",
        "Myanmar": "mym2", # Not mymr
        "Ogham": "ogam",
        "Runic": "runr",
        "Sinhala": "sinh",
        "Syriac": "syrc",
        "Thaana": "thaa",
        "Yi": "yiii",
        "Deseret": "dsrt",
        "Gothic": "goth",
        "Old_Italic": "ital",
        "Buhid": "buhd",
        "Hanunoo": "hano",
        "Tagalog": "tglg",
        "Tagbanwa": "tagb",
        "Cypriot": "cprt",
        "Limbu": "limb",
        "Linear_B": "linb",
        "Osmanya": "osma",
        "Shavian": "shaw",
        "Tai_Le": "tale",
        "Ugaritic": "ugar",
        "Buginese": "bugi",
        "Coptic": "copt",
        "Glagolitic": "glag",
        "Kharoshthi": "khar",
        "New_Tai_Lue": "talu",
        "Old_Persian": "xpeo",
        "Syloti_Nagri": "sylo",
        "Tifinagh": "tfng",
        "Balinese": "bali",
        "Cuneiform": "xsux",
        "Nko": "nkoo",
        "Phags_Pa": "phag",
        "Phoenician": "phnx",
        "Carian": "cari",
        "Cham": "cham",
        "Kayah_Li": "kali",
        "Lepcha": "lepc",
        "Lycian": "lyci",
        "Lydian": "lydi",
        "Ol_Chiki": "olck",
        "Rejang": "rjng",
        "Saurashtra": "saur",
        "Sundanese": "sund",
        "Vai": "vaii",
        "Avestan": "avst",
        "Bamum": "bamu",
        "Egyptian_Hieroglyphs": "egyp",
        "Imperial_Aramaic": "armi",
        "Inscriptional_Pahlavi": "phli",
        "Inscriptional_Parthian": "prti",
        "Javanese": "java",
        "Kaithi": "kthi",
        "Lisu": "lisu",
        "Meetei_Mayek": "mtei",
        "Old_South_Arabian": "sarb",
        "Old_Turkic": "orkh",
        "Samaritan": "samr",
        "Tai_Tham": "lana",
        "Tai_Viet": "tavt",
        "Batak": "batk",
        "Brahmi": "brah",
        "Mandaic": "mand",
        "Chakma": "cakm",
        "Meroitic_Cursive": "merc",
        "Meroitic_Hieroglyphs": "mero",
        "Miao": "plrd",
        "Sharada": "shrd",
        "Sora_Sompeng": "sora",
        "Takri": "takr",
        "Bassa_Vah": "bass",
        "Caucasian_Albanian": "aghb",
        "Duployan": "dupl",
        "Elbasan": "elba",
        "Grantha": "gran",
        "Khojki": "khoj",
        "Khudawadi": "sind",
        "Linear_A": "lina",
        "Mahajani": "mahj",
        "Manichaean": "mani",
        "Mende_Kikakui": "mend",
        "Modi": "modi",
        "Mro": "mroo",
        "Nabataean": "nbat",
        "Old_North_Arabian": "narb",
        "Old_Permic": "perm",
        "Pahawh_Hmong": "hmng",
        "Palmyrene": "palm",
        "Pau_Cin_Hau": "pauc",
        "Psalter_Pahlavi": "phlp",
        "Siddham": "sidd",
        "Tirhuta": "tirh",
        "Warang_Citi": "wara",
        "Ahom": "ahom",
        "Anatolian_Hieroglyphs": "hluw",
        "Hatran": "hatr",
        "Multani": "mult",
        "Old_Hungarian": "hung",
        "Signwriting": "sgnw",
        "Adlam": "adlm",
        "Bhaiksuki": "bhks",
        "Marchen": "marc",
        "Osage": "osge",
        "Tangut": "tang",
        "Newa": "newa",
        "Masaram_Gondi": "gonm",
        "Nushu": "nshu",
        "Soyombo": "soyo",
        "Zanabazar_Square": "zanb",
        "Dogra": "dogr",
        "Gunjala_Gondi": "gong",
        "Hanifi_Rohingya": "rohg",
        "Makasar": "maka",
        "Medefaidrin": "medf",
        "Old_Sogdian": "sogo",
        "Sogdian": "sogd",
        "Elymaic": "elym",
        "Nandinagari": "nand",
        "Nyiakeng_Puachue_Hmong": "hmnp",
        "Wancho": "wcho",
        "Chorasmian": "chrs",
        "Dives_Akuru": "diak",
        "Khitan_Small_Script": "kits",
        "Yezidi": "yezi",
    }

