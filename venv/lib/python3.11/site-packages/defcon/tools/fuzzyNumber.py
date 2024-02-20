class FuzzyNumber(object):

    def __init__(self, value, threshold):
        self.value = value
        self.threshold = threshold

    def __repr__(self):
        return "[%f %f]" % (self.value, self.threshold)

    def __lt__(self, other):
        if hasattr(other, "value"):
            if abs(self.value - other.value) < self.threshold:
                return False
            else:
                return self.value < other.value
        return self.value < other

    def __eq__(self, other):
        if hasattr(other, "value"):
            return abs(self.value - other.value) < self.threshold
        return self.value == other

    def __hash__(self):
        return hash((self.value, self.threshold))
