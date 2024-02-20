import copy

def shaper_inputs(self):
    return self.input


def _do_apply(self, buf, ix, namedclasses={}):
    from fontFeatures.shaperLib.Rule import _expand_slot

    coverage = buf[ix : ix + len(self.input)]
    newstuff = []
    # Handle single subst first
    if len(self.input) == 1 and len(self.replacement) == 1:
        replacements = _expand_slot(self.replacement[0], namedclasses)
        if len(replacements) == 1:
            buf[ix].glyph = replacements[0]
        else:
            inputs = _expand_slot(self.input[0], namedclasses)
            buf[ix].glyph = replacements[inputs.index(buf[ix].glyph)]
        buf[ix].prep_glyph(buf.font)
        return

    delta = len(self.replacement) - 1
    for g in self.replacement:
        new_glyph = copy.copy(buf[ix])
        new_glyph.glyph = g[0]
        new_glyph.prep_glyph(buf.font)
        new_glyph.substituted = True
        if len(self.replacement) > 1 and len(coverage) == 1:
            new_glyph.multiplied = True
        if len(self.replacement) == 1 and len(coverage) > 1:
            new_glyph.ligated = True
        newstuff.append(new_glyph)
    buf[ix : ix + len(self.input)] = newstuff
    if delta > 0:
        return delta
