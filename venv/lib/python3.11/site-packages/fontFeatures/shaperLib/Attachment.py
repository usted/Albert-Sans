import logging
from fontFeatures import Rule


def shaper_inputs(self):
    """Returns a list of potential glyphs to determine whether to test if this
    rule applies at a given point."""
    return [self.bases.keys(), self.marks.keys()]

def find_base_backwards(self, buf, ix):
    """Looks backwards in a buffer from index ``ix`` to find the nearest base."""
    start_ix = ix
    ix = ix - 1
    while ix >= 0:
        if buf[ix].glyph in self.bases.keys():
            # Check for unhelpful stuff in between
            my_category = buf[ix].category[0]
            for i in range(ix+1, start_ix):
                if buf[i].category[0] == my_category or buf[i].category[0] == "unknown":
                    # Oops, we skipped over another %s to get here
                    return None
            return ix
        ix = ix - 1
    return None

def would_apply_at_position(self, buf, ix, namedclasses={}):
    """Tests to see if this rule would apply at position ``ix`` of the buffer."""
    from fontFeatures.shaperLib.Rule import _expand_slot

    logging.getLogger("fontFeatures.shaperLib").debug("Testing if rule would apply at position %i" % (ix))
    if namedclasses:
        marks = _expand_slot(self.marks.keys(), namedclasses)
        bases = _expand_slot(self.bases.keys(), namedclasses)
    else:
        marks = self.marks.keys()
        bases = self.bases.keys()

    if self.is_cursive:
        if ix == 0:
            logging.getLogger("fontFeatures.shaperLib").debug(" * No, it has no adjacent glyph")
            return False
        # We will sort it out later
        # logging.getLogger("fontFeatures.shaperLib").debug(" * Yes, %s/%s is a pair" % (buf[ix].glyph, buf[ix-1].glyph))
        return True



    # Mark to base is a bit different, as multiple marks can attach to a base
    # so we search backwards for the preceding base glyph
    # XXX mark to mark
    if buf[ix].glyph not in marks:
        logging.getLogger("fontFeatures.shaperLib").debug(" * No, %s is not in our mark list" % (buf[ix].glyph))
        return False
    base_ix = find_base_backwards(self, buf, ix)
    if base_ix is None:
        logging.getLogger("fontFeatures.shaperLib").debug(" * No, I couldn't find a base glyph")
        return False
    if buf[base_ix].glyph not in bases:
        logging.getLogger("fontFeatures.shaperLib").debug(" * No, %s is not in our base list" % buf[base_ix].glyph)
        return False
    logging.getLogger("fontFeatures.shaperLib").debug(" * Yes, attaching mark %s/%i to %s/%i" % (buf[ix].glyph, ix, buf[base_ix].glyph, base_ix))
    return True

def _do_apply_cursive(self, buf, ix):
    this_record = buf[ix]
    prev_record = buf[ix-1]

    mark = prev_record.glyph
    base = this_record.glyph

    if mark not in self.marks or base not in self.bases:
        return
    exit_x, exit_y = self.marks.get(mark, (0,0))
    entry_x, entry_y = self.bases.get(base, (0,0))

    i = ix-1
    j = ix

    if buf.direction == "LTR":
        buf[i].position.xAdvance = exit_x + (buf[i].position.xPlacement or 0)
        d = entry_x + (buf[j].position.xPlacement or 0)
        buf[j].position.xAdvance = (buf[j].position.xAdvance or 0) - d
        buf[j].position.xPlacement = (buf[j].position.xPlacement or 0) - d
    elif buf.direction == "RTL":
        d = exit_x + (buf[i].position.xPlacement or 0)
        logging.getLogger("fontFeatures.shaperLib").debug("Adjusting advance of %s by %i" % (buf[i].glyph, -d))
        buf[i].position.xAdvance = (buf[i].position.xAdvance or 0) - d
        buf[i].position.xPlacement = (buf[i].position.xPlacement or 0) - d

        buf[j].position.xAdvance = entry_x + (buf[j].position.xPlacement or 0)

    child = i
    parent = j
    x_offset = entry_x - exit_x
    y_offset = entry_y - exit_y
    if not (self.flags & 1):
        parent, child = child, parent
        x_offset = -x_offset
        y_offset = -y_offset
    buf[child].position.yPlacement = y_offset
    this_record.attach_type = "cursive"
    this_record.attach_chain = parent - child


def _do_apply(self, buf, ix, namedclasses={}):
    if self.is_cursive:
        return _do_apply_cursive(self, buf, ix)
    from fontFeatures import ValueRecord
    base_ix = find_base_backwards(self, buf, ix)
    mark = buf[ix].glyph
    base = buf[base_ix].glyph
    xpos = self.bases[base][0] - self.marks[mark][0]
    ypos = self.bases[base][1] - self.marks[mark][1]
    buf[ix].position.xPlacement = xpos
    buf[ix].position.yPlacement = ypos
    buf[ix].attach_type = "mark"
    buf[ix].attach_chain = base_ix - ix
