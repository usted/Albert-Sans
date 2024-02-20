from .IndicShaperData import IndicPosition, make_syllable_machine, syllabic_category_map
from .SyllabicShaper import SyllabicShaper
import unicodedata
from youseedee import ucd_data
from collections import OrderedDict


khmer_category_reassignments = {
    0x179A: "Ra",
    0x17CC: "Robatic",
    0x17C9: "Robatic",
    0x17CA: "Robatic",
    0x17C6: "Xgroup",
    0x17CB: "Xgroup",
    0x17CD: "Xgroup",
    0x17CE: "Xgroup",
    0x17CF: "Xgroup",
    0x17D0: "Xgroup",
    0x17D1: "Xgroup",
    0x17C7: "Ygroup",
    0x17C8: "Ygroup",
    0x17DD: "Ygroup",
    0x17D3: "Ygroup",
}

states = OrderedDict(
    c = "(C | Ra | V)",
    cn = "c ((ZWJ|ZWNJ)? Robatic)?",
    joiner = "(ZWJ | ZWNJ)",
    xgroup = "(joiner* Xgroup)*",
    ygroup = "Ygroup*",
    matra_group = "VPre? xgroup VBlw? xgroup (joiner? VAbv)? xgroup VPst?",
    syllable_tail = "xgroup matra_group xgroup (Coeng c)? ygroup",
    broken_cluster = "(Coeng cn)* (Coeng | syllable_tail)",
    consonant_syllable = "(cn|PLACEHOLDER|DOTTEDCIRCLE) broken_cluster",
)


class KhmerShaper(SyllabicShaper):
    repha = "Repha"
    syllable_machine = make_syllable_machine(
        states,
        additional_categories=["Ra","Robatic","Xgroup", "Ygroup", "VPre", "VBlw", "VAbv", "VPst"]
    )
    syllable_types = [ "consonant_syllable", "broken_cluster", "other" ]

    def collect_features(self, shaper):
        shaper.add_pause(self.setup_syllables)
        shaper.add_pause(self.initial_reordering)
        shaper.add_features("locl", "ccmp")
        shaper.add_features("pref", "blwf", "abvf", "pstf", "cfar")
        shaper.add_pause() # Clear syllables
        shaper.add_features("pres", "blws", "abvs", "psts")


    def override_features(self, shaper):
        shaper.add_features("clig")
        shaper.disable_feature("liga")

    def reassign_category(self, item):
        cp = item.codepoint
        if cp in khmer_category_reassignments:
            item.syllabic_category = khmer_category_reassignments[cp]

        if item.syllabic_category == "M":
            if item.syllabic_position == IndicPosition.PRE_C:
                item.syllabic_category = "VPre"
            elif item.syllabic_position == IndicPosition.ABOVE_C:
                item.syllabic_category = "VAbv"
            elif item.syllabic_position == IndicPosition.BELOW_C:
                item.syllabic_category = "VBlw"
            elif item.syllabic_position == IndicPosition.POST_C:
                item.syllabic_category = "VPst"

    def initial_reordering_consonant_syllable(self, start, end):
        def cat(i):
            return self.buffer.items[i].syllabic_category
        def mask_disallow(places, *feats):
            for p in places:
                for f in feats:
                    self.buffer.items[p].feature_masks[f] = True
        def mask_allow(places, *feats):
            for p in places:
                for f in feats:
                    self.buffer.items[p].feature_masks[f] = False

        mask_allow(range(start+1, end), "blwf", "advf", "pstf")
        mask_disallow(range(start, end), "cfar")

        num_coengs = 0
        for i in range(start+1, end):
            if cat(i) == "Coeng" and num_coengs <= 2 and i + 1 < end:
                num_coengs += 1
                if cat(i+1) == "Ra":
                    mask_allow([i, i+1], "pref")
                    # Move the Coeng,Ro sequence to the start.
                    # XXX merge_clusters
                    ro = self.buffer.items.pop(i+1)
                    coeng = self.buffer.items.pop(i)
                    self.buffer.items = self.buffer.items[:start] + [coeng, ro] + self.buffer.items[start:]
                    mask_allow(range(i+2, end), "cfar")
                    num_coengs = 2
            elif cat(i) == "VPre":
                # XXX merge_clusters
                vpre = self.buffer.items.pop(i)
                self.buffer.items = self.buffer.items[:start] + [vpre] + self.buffer.items[start:]

    initial_reordering_syllable = {
        "broken_cluster": initial_reordering_consonant_syllable,
        "consonant_syllable": initial_reordering_consonant_syllable,
    }


    def normalize_unicode_buffer(self):
        unicodes = [item.codepoint for item in self.buffer.items]
        newunicodes = []
        for cp in unicodes:
            if cp in [0x17BE,0x17BF, 0x17C0, 0x17C4, 0x17C5]:
                newunicodes.extend([0x17C1, cp])
            else:
                newunicodes.extend([ord(x) for x in unicodedata.normalize("NFD", chr(cp)) ])
        # Now recompose
        newstring = ""
        ix = 0
        while ix < len(newunicodes):
            a = newunicodes[ix]
            if ix+1 == len(newunicodes):
                newstring = newstring + chr(a)
                break

            b = newunicodes[ix+1]
            s = chr(a) + chr(b)
            composed = unicodedata.normalize("NFC", s)
            if ucd_data(a)["General_Category"][0] == "M":
                newstring = newstring + chr(a)
                ix = ix + 1
                continue
            elif composed != unicodedata.normalize("NFD", s):
                assert(len(s) == 1)
                newunicodes[ix] = ord(x)
                del newunicodes[ix+1]
                continue
            else:
                newstring = newstring + chr(a)
                ix = ix + 1

        self.buffer.store_unicode(newstring)
