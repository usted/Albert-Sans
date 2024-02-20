import logging

__all__ = ["apply_to_buffer"]


def is_forward(rules):
    clearly_forward = False
    clearly_reverse = False
    for r in rules:
        if hasattr(r, "reverse") and r.reverse:
            clearly_reverse = True
        else:
            clearly_forward = True
    if clearly_forward and clearly_reverse:
        logging.getLogger("fontFeatures.shaperLib").warn("There were forward and reverse rules in the same routine!")
        return True
    return not clearly_reverse


def apply_to_buffer(self, buf, stage=None, feature=None, namedclasses={}):
    buf.set_mask(self.flags, self.markFilteringSet, self.markAttachmentSet)
    if feature:
        buf.set_feature_mask(feature)
    # XXX reverse sub routines must go backwards here
    if is_forward(self.rules):
        i = 0
        while i < len(buf): # (which may change!)
            for r in self.rules:
                if stage and r.stage != stage:
                    continue
                if r.flags:
                    buf.set_mask(r.flags, self.markFilteringSet, self.markAttachmentSet)
                if r.would_apply_at_position(buf, i,namedclasses=namedclasses):
                    logging.getLogger("fontFeatures.shaperLib").debug("Applying rule at position %i\n" % (i))
                    delta = r._do_apply(buf, i, namedclasses=namedclasses)
                    buf.update()
                    if delta:
                        i = i + delta
                    break
            i = i + 1
    else:
        i = len(buf)
        while i >= 0:
            for r in self.rules:
                if stage and r.stage != stage:
                    continue
                if r.flags:
                    buf.set_mask(r.flags, self.markFilteringSet, self.markAttachmentSet)
                if r.would_apply_at_position(buf, i,namedclasses=namedclasses):
                    logging.getLogger("fontFeatures.shaperLib").debug("Applying rule at position %i\n" % (i))
                    delta = r._do_apply(buf, i, namedclasses=namedclasses)
                    buf.update()
                    break
            i = i - 1
