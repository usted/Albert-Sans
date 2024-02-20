"""ttLib.Substitution: Converting Substitution rules to TrueType."""

def lookup_type(self, forFea=False):
    """Mixin to determine the GSUB lookup type of a fontFeatures.Substitution object

    Returns: integer GSUB lookup type."""
    if self.reverse:
        return 8
    if not self.replacement:
        return 2 # Deletion but treat as mult sub
    if (self.has_context and not forFea) or len(self.lookups) > 0 and any([x is not None for x in self.lookups]):
        return 6  # Chaining
    # if self.input == self.replacement: # It's an ignore
    # return 6
    if len(self.input) == 1 and len(self.replacement) == 1:
        if self.force_alt or (len(self.input[0]) == 1 and len(self.replacement[0]) > 1):
            return 3  # Alternate
        else:
            return 1  # Single
    if len(self.input) > 1 and len(self.replacement) == 1:
        return 4  # Ligature

    if len(self.input) > 1 and len(self.replacement) > 1:
        return 9  # Not directly expressible!

    if len(self.replacement) > 1:
        return 2
