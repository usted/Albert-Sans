"""ttLib.Chaining: Converting Chaining rules to TrueType."""

def lookup_type(self):
    """Mixin to determine the GSUB/GPOS lookup type of a fontFeatures.Chaining object

    Returns: integer GSUB/GPOS lookup type."""
    if self.stage == "pos":
        return 8
    else:
        return 6
