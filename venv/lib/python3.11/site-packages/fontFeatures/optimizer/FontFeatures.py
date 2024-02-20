from fontFeatures import Substitution, Chaining, Routine
import logging


class MergeNonOverlappingRoutines:
    level = 2

    def apply(self, ff):
        logger = logging.getLogger("fontFeatures")
        deadRoutine = Routine(name="dead")

        def haschains(routine):
            for r in routine.rules:
                if isinstance(r, Chaining):
                    return True

        routinelist = ff.routines
        ff.markRoutineUseInChains()
        for lix, l in enumerate(routinelist):
            if haschains(l) or l == deadRoutine:
                continue
            for rix in range(lix + 1, len(routinelist)):
                r = routinelist[rix]
                if haschains(r) or r == deadRoutine:
                    continue
                if self.nonOverlapping(ff, l, r):
                    logger.info(
                        "Merging nonoverlapping routines %s , %s" % (l.name, r.name)
                    )
                    self.merge(l, r)
                    routinelist[rix] = deadRoutine
        ff.routines = list(filter(lambda r: r != deadRoutine, routinelist))

    def whatuses(self, routine, ff):
        # Compute the glyphs which are a context for a routine to be called
        return set.union(set([]), *[c.involved_glyphs for c in list(routine.usedin)])

    def replaceAllReferences(self, usedin, first, second):
        for i in usedin:
            for routinelist in i.lookups:
                if not routinelist:
                    continue
                for ix, routine in enumerate(routinelist):
                    if routine == first:
                        routinelist[ix] = second

    def merge(self, l, r):
        l.rules.extend(r.rules)
        if l.name and r.name:
            l.name = l.name + "_" + r.name
        elif r.name:
            l.name = r.name
        l.comments.extend(r.comments)
        l.usedin = set.union(l.usedin, r.usedin)
        self.replaceAllReferences(l.usedin, r, l)

    def nonOverlapping(self, ff, l, r):
        return (
            not (l.involved_glyphs & r.involved_glyphs)
            and not (self.whatuses(l, ff) & self.whatuses(r, ff))
            and self.compatibleRules(l, r)
        )

    def compatibleRules(self, l, r):
        from fontFeatures.feaLib.Routine import (
            arrange_by_type,
            arrange_by_lookup_type,
            arrange_by_flags,
        )

        testRoutine = Routine()
        testRoutine.rules.extend(l.rules)
        testRoutine.rules.extend(r.rules)
        if arrange_by_type(testRoutine):
            return False
        if arrange_by_lookup_type(testRoutine):
            return False
        if arrange_by_flags(testRoutine):
            return False
        return True


optimizations = [MergeNonOverlappingRoutines]
