def shaper_inputs(self):
    return self.glyphs


def _do_apply(self, buf, ix, namedclasses={}):
    coverage = buf[ix : ix + len(self.glyphs)]
    for glyph, vr in zip(coverage, self.valuerecords):
    	glyph.add_position(vr)
    if not self.valuerecords[-1]: # A special case!
        return
    return len(self.glyphs) - 1
