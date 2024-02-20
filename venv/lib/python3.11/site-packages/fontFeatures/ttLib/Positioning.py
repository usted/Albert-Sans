"""ttLib.Positioning: Converting Positioning rules to TrueType."""

def lookup_type(self):
    """Mixin to determine the GPOS lookup type of a fontFeatures.Positioning object

    Returns: integer GPOS lookup type."""
    if not self.has_context:
        if len(self.glyphs) == 1:
            return 1
        if len(self.glyphs) == 2:
            return 2
    return 8

