from .IndicShaperData import IndicPosition, make_syllable_machine, syllabic_category_map
from .SyllabicShaper import SyllabicShaper
from collections import OrderedDict


myanmar_category_reassignments = {
    0x002D: "GB",
    0x00A0: "GB",
    0x00D7: "GB",
    0x1004: "Ra",
    0x101B: "Ra",
    0x1032: "A",
    0x1036: "A",
    0x1038: "SM",
    0x1039: "H",
    0x103A: "As",
    0x103B: "MY",
    0x103C: "MR",
    0x103D: "MW",
    0x103E: "MH",
    0x1040: "D",  # XXX The spec says D0, but Uniscribe doesn't seem to do.
    0x104A: "P",
    0x104B: "P",
    0x104E: "C",
    0x105A: "Ra",
    0x105E: "MY",
    0x105F: "MY",
    0x1060: "MH",
    0x1082: "MW",
    0x109A: "SM",
    0x109B: "SM",
    0x109C: "SM",
    0x2012: "GB",
    0x2013: "GB",
    0x2014: "GB",
    0x2015: "GB",
    0x2022: "GB",
    0x25CC: "GB",
    0x25FB: "GB",
    0x25FC: "GB",
    0x25FD: "GB",
    0x25FE: "GB",
    0xAA74: "C",
    0xAA75: "C",
    0xAA76: "C",  # https://github.com/harfbuzz/harfbuzz/issues/218
}

for cp in range(0x1041, 0x1049 + 1):
    myanmar_category_reassignments[cp] = "D"
for cp in range(0x1090, 0x1099 + 1):
    myanmar_category_reassignments[cp] = "D"
for cp in range(0xF300, 0xFE0F + 1):
    myanmar_category_reassignments[cp] = "VS"
for cp in range(0x1087, 0x108F + 1):
    myanmar_category_reassignments[cp] = "SM"
for cp in [0x1063, 0x1064, 0x1069, 0x106A, 0x106B, 0x106C, 0x106D, 0xAA7B]:
    myanmar_category_reassignments[cp] = "PT"


states = OrderedDict(
    j="ZWJ|ZWNJ",  # Joiners
    k="(Ra As H)",  # Kinzi
    c="C|Ra",  # is_consonant
    medial_group="MY? As? MR? ((MW MH? | MH) As?)?",
    main_vowel_group="(VPre VS?)* VAbv* VBlw* A* (DB As?)?",
    post_vowel_group="VPst MH? As* VAbv* A* (DB As?)?",
    pwo_tone_group="PT A* DB? As?",
    complex_syllable_tail="As* medial_group main_vowel_group post_vowel_group* pwo_tone_group* V* j?",
    syllable_tail="(H (c|IV) VS?)* (H | complex_syllable_tail)",
    consonant_syllable="(k|CS)? (c|IV|D|GB) VS? syllable_tail",
    punctuation_cluster="P V",
    broken_cluster="k? VS? syllable_tail",
)


class MyanmarShaper(SyllabicShaper):
    basic_features = ["rphf", "pref", "blwf", "pstf"]
    other_features = ["pres", "abvs", "blws", "psts"]
    repha = None
    syllable_machine = make_syllable_machine(
        states,
        additional_categories=[
            "VS",
            "MW",
            "P",
            "As",
            "PT",
            "MY",
            "MH",
            "D",
            "GB",
            "MR",
            "VPre",
            "VAbv",
            "VBlw",
            "VPst",
        ],
    )
    syllable_types = [
        "consonant_syllable",
        "punctuation_cluster",
        "broken_cluster",
        "other",
    ]

    def reassign_category(self, item):
        cp = item.codepoint
        if cp in myanmar_category_reassignments:
            item.syllabic_category = myanmar_category_reassignments[cp]

        if item.syllabic_category == "M":
            if item.syllabic_position == IndicPosition.PRE_C:
                item.syllabic_category = "VPre"
                item.syllabic_position = IndicPosition.PRE_M
            elif item.syllabic_position == IndicPosition.ABOVE_C:
                item.syllabic_category = "VAbv"
            elif item.syllabic_position == IndicPosition.BELOW_C:
                item.syllabic_category = "VBlw"
            elif item.syllabic_position == IndicPosition.POST_C:
                item.syllabic_category = "VPst"

    def initial_reordering_consonant_syllable(self, start, end):
        def cat(i):
            return self.buffer.items[i].syllabic_category

        def get_pos(i):
            return self.buffer.items[i].syllabic_position

        def set_pos(i, pos):
            self.buffer.items[i].syllabic_position = pos

        def is_consonant(n):  # XXX Something else is Placeholder too
            isc = cat(n)
            is_medial = isc == "CM"
            return (
                isc in ["C", "CS", "Ra", "V", "PLACEHOLDER", "DOTTEDCIRCLE"]
                or is_medial
            )

        base = end
        has_reph = False

        limit = start
        if (
            start + 3 <= end
            and cat(start) == "Ra"
            and cat(start + 1) == "As"
            and cat(start + 2) == "H"
        ):
            limit += 3
            base = start
            has_reph = True
        if not has_reph:
            base = limit
        for i in range(limit, end):
            if is_consonant(i):
                base = i
                break
        i = start
        while i < start + (3 if has_reph else 0):
            set_pos(i, IndicPosition.AFTER_MAIN)
            i += 1
        while i < base:
            set_pos(i, IndicPosition.PRE_C)
            i += 1
        if i < end:
            set_pos(i, IndicPosition.BASE_C)
            i += 1
        pos = IndicPosition.AFTER_MAIN
        while i < end:
            if cat(i) == "MR":
                set_pos(i, IndicPosition.PRE_C)
            elif get_pos(i) < IndicPosition.BASE_C:  # Left Matra
                pass
            elif cat(i) == "VS":
                set_pos(i, get_pos(i - 1))
            elif pos == IndicPosition.AFTER_MAIN and cat(i) == "VBlw":
                pos = IndicPosition.BELOW_C
                set_pos(i, pos)
            elif pos == IndicPosition.BELOW_C and cat(i) == "A":
                set_pos(i, IndicPosition.BEFORE_SUB)
            elif pos == IndicPosition.BELOW_C and cat(i) == "VBlw":
                set_pos(i, pos)
            elif pos == IndicPosition.BELOW_C and cat(i) != "A":
                pos = IndicPosition.AFTER_SUB
                set_pos(i, pos)
            else:
                set_pos(i, pos)
            i = i + 1
            continue

        self.buffer.items[start:end] = sorted(
            self.buffer.items[start:end], key=lambda x: x.syllabic_position
        )

    initial_reordering_syllable = {
        "broken_cluster": initial_reordering_consonant_syllable,
        "consonant_syllable": initial_reordering_consonant_syllable,
    }
