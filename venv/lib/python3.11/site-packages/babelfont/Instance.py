from dataclasses import dataclass, field
from .BaseObject import BaseObject, I18NDictionary


@dataclass
class _InstanceFields:
    name: I18NDictionary = field(metadata={"description": "The name of this instance."})
    location: dict = field(
        metadata={
            "description": """A dictionary mapping axis tags to coordinates in order to locate this instance in the design space."""
        }
    )
    styleName: I18NDictionary = field(default_factory=I18NDictionary,
        metadata={"description": "The style name of this instance."})



@dataclass
class Instance(BaseObject, _InstanceFields):
    """An object representing a named or static instance."""

    _write_one_line = True


    def __post_init__(self):
        # If they smacked my name with a bare string, replace with I18NDict
        if isinstance(self.name, str):
            self.name = I18NDictionary.with_default(self.name)
        if isinstance(self.styleName, str):
            self.styleName = I18NDictionary.with_default(self.styleName)
        super().__post_init__()

    @property
    def localisedStyleName(self):
        return self.styleName.as_fonttools_dict or self.name.as_fonttools_dict

    @property
    def postScriptFontName(self):
        return None
