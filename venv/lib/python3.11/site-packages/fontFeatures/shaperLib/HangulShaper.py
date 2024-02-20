from .BaseShaper import BaseShaper
from fontFeatures.shaperLib.Buffer import BufferItem
import unicodedata

LBase = 0x1100
VBase = 0x1161
TBase = 0x11A7
LCount = 19
VCount = 21
TCount = 28
SBase = 0xAC00
NCount = (VCount * TCount)
SCount = (LCount * NCount)

def isCombiningL(u):
    return LBase <= u <= LBase+LCount-1
def isCombiningV(u):
    return VBase <= u <= VBase+VCount-1
def isCombiningT(u):
    return TBase+1 <= u <= TBase+TCount-1
def isCombinedS(u):
    return SBase <= u <= SBase+SCount-1

def isL(u):
    return 0x1100 <= u <= 0x115F or 0xA960 <= u <= 0xA97C
def isV(u):
    return 0x1160 <= u <= 0x11A7 or 0xD7B0 <= u <= 0xD7C6
def isT(u):
    return 0x11A8 <= u <= 0x11FF or 0xD7CB <= u <= 0xD7FB

def isHangulTone(u):
    return 0x302E <= u <= 0x302F

class HangulShaper(BaseShaper):
    def collect_features(self, shaper):
        shaper.add_features("ljmo", "vjmo", "tjmo")

    def override_features(self, shaper):
        shaper.disable_feature("calt")

    def preprocess_text(self):
        def cp(i): return self.buffer.items[i].codepoint
        def has_glyph(u): return self.font.unicode_map.get(u, None)

        # Setup masks here too
        for i in self.buffer.items:
            i.feature_masks["ljmo"] = False
            i.feature_masks["vjmo"] = False
            i.feature_masks["tjmo"] = False
        start, end, processed = 0, 0, 0
        count = len(self.buffer.items)
        for i in range(count):
            u = cp(i)
            if isHangulTone(u):
                if start < end and end == processed:
                    if not self.is_zero_width_char(u):
                        # merge out clusters?

                        # Move end to start
                        l = self.buffer.items
                        l.insert(start, l.pop(end))
                else:
                    if has_glyph(0x25CC):
                        if self.is_zero_width_char(u):
                            l.insert(i+1, BufferItem.new_unicode(0x25CC))
                        else:
                            l.insert(i, BufferItem.new_unicode(0x25CC))
                start = end = i
                continue
            start = i
            if isL(u) and i + 1 < count:
                l = u
                v = cp(i+1)
                if isV(v):
                    # <L,V> or <L,V,T>
                    t, tindex = 0,0
                    if i +2 < count:
                        t = cp(i+2)
                        if isT(t):
                            tindex = t - TBase
                        else:
                            t = 0
                    # Unsafe to break
                    if isCombiningL(l) and isCombiningV(v) and (not t or isCombiningT(t)):
                        s = SBase + (l - LBase) * NCount + (v - VBase) * TCount + tindex;
                        if has_glyph(s):
                            # Combine
                            if t:
                                self.buffer.items[i:i+3] = [BufferItem.new_unicode(s)]
                            else:
                                self.buffer.items[i:i+2] = [BufferItem.new_unicode(s)]
                            end = start + 1
                            continue
                    # Didn't compose
                    self.buffer.items[i].feature_masks["ljmo"] = True
                    self.buffer.items[i+1].feature_masks["vjmo"] = True
                    if t:
                        self.buffer.items[i+2].feature_masks["tjmo"] = True
                        end = start + 3
                    else:
                        end = start + 2
                    continue
            elif isCombinedS(u):
                s = u
                has_glyph_s = has_glyph(s)
                lindex = (s - SBase) // NCount
                nindex = (s - SBase) % NCount
                vindex = nindex // TCount
                tindex = nindex % TCount
                if not tindex and i + 1 < count and isCombiningT(self.buffer.items[i+1].codepoint):
                    # <LV,T>
                    new_tindex = cp(i+1) - TBase
                    new_s = s + new_tindex
                    if has_glyph(new_s):
                        self.buffer.items[i:i+2] = [BufferItem.new_unicode(new_s)]
                        end = start + 1
                        continue
                    else:
                        # unsafe to break
                        pass
                if not has_glyph or (not tindex and i + 1 < count and isT(cp(i+1))):
                    decomposed = [LBase  + lindex, VBase + vindex, TBase + tindex]
                    if has_glyph(decomposed[0]) and has_glyph(decomposed[1]) and (not tindex or has_glyph(decomposed[2])):
                        if not tindex:
                            decomposed.pop()
                        s_len = len(decomposed)
                        self.buffer.items[i:i+s_len] = [BufferItem.new_unicode(u) for u in decomposed]
                        if has_glyph_s and not tindex:
                            i = i + 1
                            s_len = s_len + 1
                        end = start + s_len
                        self.buffer.items[start+1].feature_masks["ljmo"] = True
                        self.buffer.items[start+2].feature_masks["vjmo"] = True
                        if start + 3 < end:
                            self.buffer.items[start+3].feature_masks["tjmo"] = True
                        # merge out clusters
                        continue
                    elif not tindex and i + 1 < count and isT(cp(i+1)):
                        # Mark unsafe to break
                        pass





