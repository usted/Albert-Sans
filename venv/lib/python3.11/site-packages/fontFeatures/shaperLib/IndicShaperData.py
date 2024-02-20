from collections import OrderedDict
from enum import IntEnum
import re
from youseedee import ucd_data


script_config = {
  "Invalid":    dict(old_spec= False, virama =      0, base_pos = "last", reph_pos = "before_post", reph_mode = "implicit", blwf_mode =  "pre_and_post"),
  "Devanagari": dict(old_spec= True,  virama = 0x094D, base_pos = "last", reph_pos = "before_post", reph_mode = "implicit", blwf_mode =  "pre_and_post"),
  "Bengali":    dict(old_spec= True,  virama = 0x09CD, base_pos = "last", reph_pos = "after_sub", reph_mode =   "implicit", blwf_mode =  "pre_and_post"),
  "Gurmukhi":   dict(old_spec= True,  virama = 0x0A4D, base_pos = "last", reph_pos = "before_sub", reph_mode =  "implicit", blwf_mode =  "pre_and_post"),
  "Gujarati":   dict(old_spec= True,  virama = 0x0ACD, base_pos = "last", reph_pos = "before_post", reph_mode = "implicit", blwf_mode =  "pre_and_post"),
  "Oriya":      dict(old_spec= True,  virama = 0x0B4D, base_pos = "last", reph_pos = "after_main", reph_mode =  "implicit", blwf_mode =  "pre_and_post"),
  "Tamil":      dict(old_spec= True,  virama = 0x0BCD, base_pos = "last", reph_pos = "after_post", reph_mode =  "implicit", blwf_mode =  "pre_and_post"),
  "Telugu":     dict(old_spec= True,  virama = 0x0C4D, base_pos = "last", reph_pos = "after_post", reph_mode =  "explicit", blwf_mode =  "post_only"),
  "Kannada":    dict(old_spec= True,  virama = 0x0CCD, base_pos = "last", reph_pos = "after_post", reph_mode =  "implicit", blwf_mode =  "post_only"),
  "Malayalam":  dict(old_spec= True,  virama = 0x0D4D, base_pos = "last", reph_pos = "after_main", reph_mode =  "log_repha", blwf_mode = "pre_and_post"),
  "Sinhala":    dict(old_spec= False, virama = 0x0DCA, base_pos = "last_sinhala", reph_pos = "after_post", reph_mode =  "explicit", blwf_mode = "pre_and_post")
}

# Go from UCD categories to the ones we care about

syllabic_category_map = {
  "Other": "X",
  "Avagraha": "Symbol",
  "Bindu": "SM",
  "Brahmi_Joining_Number": "PLACEHOLDER", # Don't care.
  "Cantillation_Mark": "A",
  "Consonant": "C",
  "Consonant_Dead": "C",
  "Consonant_Final": "CM",
  "Consonant_Head_Letter": "C",
  "Consonant_Killer": "M", # U+17CD only.
  "Consonant_Medial": "CM",
  "Consonant_Placeholder": "PLACEHOLDER",
  "Consonant_Preceding_Repha": "Repha",
  "Consonant_Prefixed": "X", # Don't care.
  "Consonant_Subjoined": "CM",
  "Consonant_Succeeding_Repha": "CM",
  "Consonant_With_Stacker": "CS",
  "Gemination_Mark": "SM", # https://github.com/harfbuzz/harfbuzz/issues/552
  "Invisible_Stacker": "Coeng",
  "Joiner": "ZWJ",
  "Modifying_Letter": "X",
  "Non_Joiner": "ZWNJ",
  "Nukta": "N",
  "Number": "PLACEHOLDER",
  "Number_Joiner": "PLACEHOLDER", # Don't care.
  "Pure_Killer": "M", # Is like a vowel matra.
  "Register_Shifter": "RS",
  "Syllable_Modifier": "SM",
  "Tone_Letter": "X",
  "Tone_Mark": "N",
  "Virama": "H",
  "Visarga": "SM",
  "Vowel": "V",
  "Vowel_Dependent": "M",
  "Vowel_Independent": "V",
  # The following come from reassignment
  "Symbol": "Symbol",
  "Ra": "Ra",
  "Dotted_Circle": "DOTTEDCIRCLE",
}

## Set up the state machine for syllable matching and syllabic
## categories using composed regular expressions


states = OrderedDict(
    c = "C|Ra",
    n = "(ZWNJ?RS)?(N N?)?",
    z = "ZWJ|ZWNJ",
    reph = "Ra H|Repha",
    cn = "c ZWJ?n?",
    forced_rakar = "ZWJ H ZWJ Ra",
    symbol = "Symbol N?",
    matra_group = "z*M N?(H|forced_rakar)?",
    syllable_tail = "(z?SM SM?ZWNJ?)?A*",
    halant_group = "z?H(ZWJ N?)?",
    final_halant_group = "halant_group|H ZWNJ",
    medial_group = "CM?",
    halant_or_matra_group = "final_halant_group|matra_group*",
    complex_syllable_tail = "(halant_group cn)*medial_group halant_or_matra_group syllable_tail",
    consonant_syllable = "((Repha|CS)?cn complex_syllable_tail)",
    vowel_syllable = "(reph?V n?(complex_syllable_tail|ZWJ))",
    standalone_cluster = "((Repha|CS)?PLACEHOLDER|reph?DOTTEDCIRCLE)n? complex_syllable_tail",
    symbol_cluster = "symbol syllable_tail",
    broken_cluster = "reph? n? complex_syllable_tail",
)

def make_syllable_machine(states, additional_categories=[]):
    categories = set(syllabic_category_map.values()) | set(additional_categories)
    syllable_machine = {}
    tail = r'\([^\)]+\)=\d+'
    for value in categories:
        syllable_machine[value] = f'<{value}>' + tail
    syllable_machine["other"] = r'<[^\>]+>' + tail

    for category,definition in states.items():
        # Recursively replace any known states with their definitions:
        states = "\\b("+"|".join(sorted(syllable_machine.keys(),key=len, reverse=True))+")\\b"
        definition = re.sub(states, lambda match: "("+syllable_machine[match[1]]+")", definition)
        definition = definition.replace(" ", "")
        syllable_machine[category] = definition
    return syllable_machine

syllable_machine_indic = make_syllable_machine(states)

class IndicPosition(IntEnum):
  START = 0

  RA_TO_BECOME_REPH = 1
  PRE_M = 2
  PRE_C = 3

  BASE_C = 4
  AFTER_MAIN = 5

  ABOVE_C = 6

  BEFORE_SUB = 7
  BELOW_C = 8
  AFTER_SUB = 9

  BEFORE_POST = 10
  POST_C = 11
  AFTER_POST = 12

  FINAL_C = 13
  SMVD = 14

  END = 15

def is_ra(u):
    return u in [0x0930, 0x09B0, 0x09F0, 0x0A30, 0x0AB0, 0x0B30, 0x0BB0, 0x0C30, 0x0CB0, 0x0D30, 0x0DBB, 0x179A]

def IndicPositionalCategory2IndicPosition(ipc):
    if ipc == "Left":   return IndicPosition.PRE_C
    if ipc == "Top":    return IndicPosition.ABOVE_C
    if ipc == "Bottom": return IndicPosition.BELOW_C

    if ipc == "Right":  return IndicPosition.POST_C
    if ipc == "Bottom_And_Right": return IndicPosition.POST_C
    if ipc == "Left_And_Right": return IndicPosition.POST_C
    if ipc == "Top_And_Bottom_And_Left": return IndicPosition.POST_C

    if ipc == "Top_And_Bottom": return IndicPosition.BELOW_C
    if ipc == "Top_And_Bottom_And_Left": return IndicPosition.BELOW_C
    if ipc == "Top_And_Bottom_And_Right": return IndicPosition.POST_C

    if ipc == "Top_And_Left": return IndicPosition.ABOVE_C
    if ipc == "Top_And_Left_And_Right": return IndicPosition.POST_C
    if ipc == "Top_And_Right": return IndicPosition.POST_C

    if ipc == "Overstruck": return IndicPosition.AFTER_MAIN
    if ipc == "Visual_Order_Left": return IndicPosition.PRE_M

    return IndicPosition.END

matra_pos_left = { "Default": IndicPosition.PRE_M }
matra_pos_right = {
# Telu and Knda need special cases
    "Devanagari": IndicPosition.AFTER_SUB,
    "Bengali": IndicPosition.AFTER_POST,
    "Gurmukhi": IndicPosition.AFTER_POST,
    "Gujarati": IndicPosition.AFTER_POST,
    "Oriya": IndicPosition.AFTER_POST,
    "Tamil": IndicPosition.AFTER_POST,
    "Malayalam": IndicPosition.AFTER_POST,
    "Default": IndicPosition.AFTER_SUB
}
matra_pos_top = {
    "Devanagari": IndicPosition.AFTER_SUB,
    "Gurmukhi": IndicPosition.AFTER_POST,
    "Gujarati": IndicPosition.AFTER_SUB,
    "Oriya": IndicPosition.AFTER_MAIN,
    "Tamil": IndicPosition.AFTER_SUB,
    "Telugu": IndicPosition.BEFORE_SUB,
    "Kannada": IndicPosition.BEFORE_SUB,
    "Sinhala": IndicPosition.AFTER_SUB,
    "Default": IndicPosition.AFTER_SUB
}
matra_pos_bottom = {
    "Devanagari": IndicPosition.AFTER_SUB,
    "Bengali": IndicPosition. AFTER_SUB,
    "Gurmukhi": IndicPosition.AFTER_POST,
    "Gujarati": IndicPosition.AFTER_POST,
    "Oriya": IndicPosition.AFTER_SUB,
    "Tamil": IndicPosition.AFTER_POST,
    "Telugu": IndicPosition.BEFORE_SUB,
    "Malayalam": IndicPosition.AFTER_POST,
    "Sinhala": IndicPosition.AFTER_SUB,
    "Default": IndicPosition.AFTER_SUB
}

def set_matra_position(item):
    script = ucd_data(item.codepoint)["Script"]
    u = item.codepoint
    if item.syllabic_position == IndicPosition.PRE_C:
        selector = matra_pos_left
    elif item.syllabic_position == IndicPosition.POST_C:
        selector = matra_pos_right
        if script == "Telugu":
            if u <= 0x0C42:
                item.syllabic_position = IndicPosition.BEFORE_SUB
            else:
                item.syllabic_position = IndicPosition.AFTER_SUB
            return
        if script == "Kannada":
            if u < 0x0CC3 or u > 0xCD6:
                item.syllabic_position = IndicPosition.BEFORE_SUB
            else:
                item.syllabic_position = IndicPosition.AFTER_SUB
            return
    elif item.syllabic_position == IndicPosition.ABOVE_C:
        selector = matra_pos_top
    elif item.syllabic_position == IndicPosition.BELOW_C:
        selector = matra_pos_bottom
    else:
        return
    item.syllabic_position = selector.get(script, selector["Default"])

def reassign_category_and_position_indic(item):
    cp = item.codepoint
    if 0x0953 <= cp <= 0x0954:
        item.syllabic_category = "SM"
    elif 0x0A72 <= cp <= 0x0A73 or 0x1CF5 <= cp <= 0x1CF6:
        item.syllabic_category = "C"
    elif 0x1CE2 <= cp <= 0x1CE8 or cp == 0x1CED:
        item.syllabic_category = "A"
    elif 0xA8F2 <= cp <= 0xA8F7 or 0x1CE9 <= cp <= 0x1CEC or 0x1CEE <= cp <= 0x1CF1:
        item.syllabic_category = "Symbol"
    elif cp == 0x0A51: # https://github.com/harfbuzz/harfbuzz/issues/524
        item.syllabic_category = "M"
        item.syllabic_position = IndicPosition.BELOW_C
    elif cp == 0x11301 or cp == 0x11303:
        item.syllabic_category = "SM"
    elif cp == 0x1133B or cp == 0x1133C:
        item.syllabic_category = "N"
    elif cp == 0x0AFB:
        item.syllabic_category = "N"
    elif cp == 0x0980 or cp == 0x09FC or cp == 0x0C80 or cp == 0x2010 or cp == 0x2011:
        item.syllabic_category = "PLACEHOLDER"
    elif cp == 0x25CC:
        item.syllabic_category = "DOTTEDCIRCLE"

    isc = item.syllabic_category

    is_medial = isc == "CM"
    is_consonant = isc in ["C", "CS", "Ra", "V", "PLACEHOLDER", "DOTTEDCIRCLE"] or is_medial

    if is_consonant:
        item.syllabic_position = IndicPosition.BASE_C
        if is_ra(cp):
            item.syllabic_category = "Ra"
    elif isc == "M":
        set_matra_position(item)
    elif isc in ["SM", "A", "Symbol"]:
        item.syllabic_position = IndicPosition.SMVD
    if cp == 0x0B01:
        item.syllabic_position = IndicPosition.BEFORE_SUB
