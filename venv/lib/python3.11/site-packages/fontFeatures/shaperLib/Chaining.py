def shaper_inputs(self):
    return self.input

def __find_masked_ix(buf, ix):
    # This probably could be done better...
    for i in range(len(buf.items)):
        if buf.mask[i] == ix: return i
    return -1

def _do_apply(self, buf, ix, namedclasses={}):
    from fontFeatures import RoutineReference
    # Save buffer mask
    flags = buf.flags
    markFilteringSet = buf.markFilteringSet
    markAttachmentSet = buf.markAttachmentSet

    if ix + len(self.lookups) -1 > len(buf.mask):
        return

    old_unmasked_indexes = [ buf.mask[ix+i] for i in range(len(self.lookups)) ]
    for i,lookups in enumerate(self.lookups):
        if not lookups:
            continue
        for routine in lookups:
            assert isinstance(routine, RoutineReference)
            routine = routine.routine
            # Adjust mask and recompute index?
            unmasked_ix = old_unmasked_indexes[i]
            for rule in routine.rules:
                buf.set_mask(rule.flags, routine.markFilteringSet, routine.markAttachmentSet)
                newix = __find_masked_ix(buf, unmasked_ix)
                if rule.would_apply_at_position(buf,newix, namedclasses) and rule._do_apply(buf, newix):
                    break

    buf.set_mask(flags, markFilteringSet, markAttachmentSet)
    return len(self.input) - 1

