from .BaseObject import BaseObject, I18NDictionary
from dataclasses import dataclass, asdict


@dataclass
class Names(BaseObject):
    """A table of global, localizable names for the font."""
    familyName: I18NDictionary = None
    designer: I18NDictionary = None
    designerURL: I18NDictionary = None
    manufacturer: I18NDictionary = None
    manufacturerURL: I18NDictionary = None
    license: I18NDictionary = None
    licenseURL: I18NDictionary = None
    version: I18NDictionary = None
    uniqueID: I18NDictionary = None
    description: I18NDictionary = None
    typographicFamily: I18NDictionary = None
    typographicSubfamily: I18NDictionary = None
    compatibleFullName: I18NDictionary = None
    sampleText: I18NDictionary = None
    WWSFamilyName: I18NDictionary = None
    WWSSubfamilyName: I18NDictionary = None
    copyright: I18NDictionary = None
    styleMapFamilyName: I18NDictionary = None
    trademark: I18NDictionary = None

    def __post_init__(self):
        for k in self.__dataclass_fields__.keys():
            if not getattr(self, k):
                setattr(self, k, I18NDictionary())

    def as_nametable_dict(self):
        rv = {}
        for k,v in asdict(self).items():
            if not v:
                continue
            rv[k] = v.default_or_dict()
        return rv
