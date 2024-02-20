from youseedee import ucd_data
from .BaseShaper import BaseShaper
import re
from fontFeatures.shaperLib.Buffer import BufferItem
from fontFeatures.shaperLib.VowelConstraints import preprocess_text_vowel_constraints
from .IndicShaperData import script_config, syllabic_category_map, IndicPositionalCategory2IndicPosition, IndicPosition
import unicodedata

DOTTED_CIRCLE = 0x25CC

class SyllabicShaper(BaseShaper):

    basic_features = ['nukt', 'akhn', 'rphf', 'rkrf', 'pref', 'blwf', 'abvf', 'half', 'pstf', 'vatu', 'cjct']
    after_syllable_features = [ "ccmp", "locl" ]
    other_features = [ "init", "pres", "abvs", "blws", "psts", "haln", "calt", "clig" ]
    repha = "Repha"

    def collect_features(self, shaper):
        shaper.add_pause(self.setup_syllables)
        shaper.add_features(*self.after_syllable_features)
        shaper.add_pause(self.initial_reordering)
        for i in self.basic_features:
            shaper.add_features(i)
            shaper.add_pause()
        shaper.add_pause(self.final_reordering)
        shaper.add_features(*self.other_features)

    def preprocess_text(self):
        preprocess_text_vowel_constraints(self.buffer)

    def reassign_category(self, item):
        pass

    def assign_category(self, item):
        # Base behavior is Indic
        ucd = ucd_data(item.codepoint)
        item.syllabic_category = syllabic_category_map.get(ucd.get("Indic_Syllabic_Category", "Other"),"X")
        item.positional_category = ucd.get("Indic_Positional_Category", "x")
        item.syllabic_position = IndicPositionalCategory2IndicPosition(item.positional_category)
        self.reassign_category(item)

    def assign_categories(self):
        serialized = []
        for ix,item in enumerate(self.buffer.items):
            self.assign_category(item)
            serialized.append("<"+item.syllabic_category+">("+item.positional_category+")="+str(ix))
        return "".join(serialized)

    def setup_syllables(self, shaper):
        syllable_index = 0
        category_string = self.assign_categories()
        self.plan.msg("Set up syllables: "+category_string)
        while len(category_string) > 0:
            state, end, matched_type = None, None, None
            for syllable_type in self.syllable_types:
                m = re.match(self.syllable_machine[syllable_type], category_string)
                if m and len(m[0]):
                    matched_type = syllable_type
                    category_string = category_string[len(m[0]):]
                    indexes = re.findall("=(\\d+)", m[0])
                    start, end = int(indexes[0]), int(indexes[-1])
                    break
            assert(matched_type)
            for i in range(start, end+1):
                self.buffer.items[i].syllable_index = syllable_index
                self.buffer.items[i].syllable = syllable_type
            syllable_index = syllable_index+1
        self.plan.msg("Syllables", self.buffer, ["syllable_index", "syllable"])

    def iterate_syllables(self):
        ix = 0
        while ix < len(self.buffer.items):
            syll_type = self.buffer.items[ix].syllable
            index = self.buffer.items[ix].syllable_index
            start = ix
            while ix < len(self.buffer.items) and self.buffer.items[ix].syllable_index == index:
                ix = ix + 1
                end = ix
            yield index, syll_type, start, end

    def insert_dotted_circles(self, repha):
        for ix,i in enumerate(self.buffer.items):
            if i.syllable == "broken_cluster" and (ix == 0 or i.syllable_index != self.buffer.items[ix-1].syllable_index):
                # Need to insert dotted circle.
                dotted_circle = BufferItem.new_unicode(DOTTED_CIRCLE)
                dotted_circle.syllable_index = i.syllable_index
                dotted_circle.syllable = i.syllable
                self.assign_category(dotted_circle)
                dotted_circle.map_to_glyph(self.buffer.font)
                if self.repha is not None and i.syllabic_category == repha:
                    self.buffer.items.insert(ix+1, dotted_circle)
                else:
                    self.buffer.items.insert(ix, dotted_circle)

    def initial_reordering_pre(self):
        pass

    def initial_reordering(self, shaper):
        self.initial_reordering_pre()
        self.insert_dotted_circles(self.repha)
        for index,syll_type,start,end in self.iterate_syllables():
            reorder = self.initial_reordering_syllable.get(syll_type, None)
            if reorder:
                reorder(self, start,end)
        self.plan.msg("After initial reordering", self.buffer, ["syllable_index", "syllable"])

    def final_reordering(self, shaper):
        for index,syll_type,start,end in self.iterate_syllables():
            self.final_reordering_syllable(start,end)

    def final_reordering_syllable(self, start, end):
        pass

