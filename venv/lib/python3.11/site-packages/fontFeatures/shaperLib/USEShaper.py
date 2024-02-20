from youseedee import ucd_data, database
from .SyllabicShaper import SyllabicShaper
from .IndicShaperData import make_syllable_machine
from fontFeatures.shaperLib.Buffer import BufferItem
import unicodedata
from collections import OrderedDict

states = OrderedDict(
    h="H | HVM | Sk",
    consonant_modifiers="CMAbv* CMBlw* ((h B | SUB) CMAbv? CMBlw*)*",
    medial_consonants="MPre? MAbv? MBlw? MPst?",
    dependent_vowels="VPre* VAbv* VBlw* VPst*",
    vowel_modifiers="HVM? VMPre* VMAbv* VMBlw* VMPst*",
    final_consonants="FAbv* FBlw* FPst*",
    final_modifiers="FMAbv* FMBlw* | FMPst?",
    complex_syllable_start="(R | CS)? (B | GB)",
    complex_syllable_middle="consonant_modifiers medial_consonants dependent_vowels vowel_modifiers (Sk B)*",
    complex_syllable_tail="complex_syllable_middle final_consonants final_modifiers",
    number_joiner_terminated_cluster_tail="(HN N)* HN",
    numeral_cluster_tail="(HN N)+",
    symbol_cluster_tail="SMAbv+ SMBlw* | SMBlw+",
    virama_terminated_cluster="complex_syllable_start consonant_modifiers h",
    sakot_terminated_cluster="complex_syllable_start complex_syllable_middle Sk",
    standard_cluster="complex_syllable_start complex_syllable_tail",
    broken_cluster="R? (complex_syllable_tail | number_joiner_terminated_cluster_tail | numeral_cluster_tail | symbol_cluster_tail)",
    number_joiner_terminated_cluster="N number_joiner_terminated_cluster_tail",
    numeral_cluster="N numeral_cluster_tail?",
    symbol_cluster="(S | GB) symbol_cluster_tail?",
    hieroglyph_cluster="SB+ | SB* G SE* (J SE* (G SE*)?)*",
    independent_cluster="O",
)
use_categories = set([x[2] for x in database["USECategory.txt"]["data"]])


class USEShaper(SyllabicShaper):
    basic_features = ["rkrf", "abvf", "blwf", "half", "pstf", "vatu", "cjct"]
    topographical_features = ["isol", "init", "medi", "fina"]
    other_features = ["abvs", "blws", "haln", "pres", "psts"]
    repha = "R"
    syllable_machine = make_syllable_machine(states, additional_categories=use_categories)
    syllable_types = [
        "independent_cluster",
        "virama_terminated_cluster",
        "sakot_terminated_cluster",
        "standard_cluster",
        "number_joiner_terminated_cluster",
        "numeral_cluster",
        "symbol_cluster",
        "hieroglyph_cluster",
        "broken_cluster",
        "other",
    ]

    def collect_features(self, shaper):
        shaper.add_pause(self.setup_syllables)
        # Default glyph pre-processing
        shaper.add_features("locl", "ccmp", "nukt", "akhn")
        shaper.add_pause(self.clear_substitution)
        shaper.add_features("rphf")
        shaper.add_pause(self.record_rphf_use)
        shaper.add_pause(self.clear_substitution)
        shaper.add_features("pref")
        shaper.add_pause(self.record_pref_use)

        shaper.add_features(*self.basic_features)
        shaper.add_pause(self.initial_reordering)
        # shaper.add_pause(self.clear_syllables)
        shaper.add_features(*self.topographical_features)
        shaper.add_pause()
        shaper.add_features(*self.other_features)

    def assign_category(self, item):
        item.syllabic_category = ucd_data(item.codepoint).get("USE_Category", "X")
        # Separate positional categories are not used, it's all in the syllabic_category
        item.positional_category = "x"

    def cat(self, i):
        return self.buffer.items[i].syllabic_category

    def setup_syllables(self, shaper):
        super().setup_syllables(shaper)
        self.setup_rphf_mask()
        self.setup_topographical_masks()

    def setup_rphf_mask(self):
        for index, syll_type, start, end in self.iterate_syllables():
            if self.cat(start) == "R":
                limit = 1
            else:
                limit = min(3, end - start)
            for i in range(start, end):
                self.buffer.items[i].feature_masks["rphf"] = i > start + limit

    def clear_substitution(self, shaper):
        for i in self.buffer.items:
            i.substituted = False

    def record_pref_use(self, shaper):
        for i in self.buffer.items:
            if i.substituted:
                i.syllabic_category = "VPre"

    def record_rphf_use(self, shaper):
        for i in self.buffer.items:
            if i.substituted:
                i.syllabic_category = "R"

    def is_post_base(self, i):
        return self.cat(i) in [
            "FAbv",
            "FBlw",
            "FPst",
            "MAbv",
            "MBlw",
            "MPst",
            "MPre",
            "VAbv",
            "VBlw",
            "VPst",
            "VPre",
            "VMAbv",
            "VMBlw",
            "VMPst",
            "VMPre",
        ]

    def is_halant(self, i):
        return self.cat(i) in ["H", "HVM"] and not self.buffer.items[i].ligated

    def reorder_syllable(self, start, end):
        if self.cat(start) == "R":
            for i in range(start + 1, end):
                post_base = self.is_post_base(i) or self.is_halant(i)
                if post_base or i == end - 1:
                    if post_base:
                        i -= 1
                    self.buffer.merge_clusters(start, i + 1)
                    self.buffer.move_item(src=start, dest=i)
                    break
        j = start
        for i in range(start, end):
            if self.is_halant(i):
                j = i + 1
            if self.cat(i) in ["VPre", "VMPre"] and j < i:  # XXX Only first ligcomp
                self.buffer.merge_clusters(j, i + 1)
                self.buffer.move_item(src=i, dest=j)

    initial_reordering_syllable = {
        "virama_terminated_cluster": reorder_syllable,
        "sakot_terminated_cluster": reorder_syllable,
        "standard_cluster": reorder_syllable,
        "broken_cluster": reorder_syllable,
    }

    def setup_topographical_masks(self):
        # Right now we don't actually send joining scripts through the USE
        pass

    def normalize_unicode_buffer(self):
        unicodes = [item.codepoint for item in self.buffer.items]
        newunicodes = []
        for cp in unicodes:
            newunicodes.extend([ord(x) for x in unicodedata.normalize("NFD", chr(cp))])
        # Now recompose
        newstring = ""
        ix = 0
        while ix < len(newunicodes):
            a = newunicodes[ix]
            if ix + 1 == len(newunicodes):
                newstring = newstring + chr(a)
                break

            b = newunicodes[ix + 1]
            s = chr(a) + chr(b)
            composed = unicodedata.normalize("NFC", s)
            if ucd_data(a)["General_Category"][0] == "M":
                newstring = newstring + chr(a)
                ix = ix + 1
                continue
            elif composed != unicodedata.normalize("NFD", s):
                assert len(s) == 1
                newunicodes[ix] = ord(x)
                del newunicodes[ix + 1]
                continue
            else:
                newstring = newstring + chr(a)
                ix = ix + 1

        self.buffer.store_unicode(newstring)
