from .Routine import optimizations as routine_optimizations
from .FontFeatures import optimizations as overall_optimizations
import fontFeatures


class Optimizer:
    def __init__(self, ff):
        self.ff = ff

    def optimize(self, level=1):
        for r in self.ff.routines:
            self.optimize_routine(r, level)
            for k, v in self.ff.features.items():
                for n in v:
                    if isinstance(n, fontFeatures.Routine):
                        self.optimize_routine(n, level)

        for routinelist in self.ff.features.values():
            for r in routinelist:
                if isinstance(r, fontFeatures.Routine):
                    self.optimize_routine(r, level)

        for optimization in overall_optimizations:
            if level >= optimization.level:
                optimization().apply(self.ff)

    def optimize_routine(self, r, level):
        for optimization in routine_optimizations:
            if level >= optimization.level:
                optimization().apply(r, self.ff)
