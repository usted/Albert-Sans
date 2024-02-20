from babelfont import *
from babelfont.convertors.designspace import Designspace
from fontTools.designspaceLib import DesignSpaceDocument, SourceDescriptor
import ufoLib2


class UFO(Designspace):
    suffix = ".ufo"

    @classmethod
    def load(cls, convertor):
        self = cls()
        self.ufo = ufoLib2.Font.open(convertor.filename)
        # Wrap it in a DS
        self.ds = DesignSpaceDocument()
        s1 = SourceDescriptor()
        s1.path = convertor.filename
        s1.font = self.ufo
        s1.name = "master.ufo1"
        s1.familyName = self.ufo.info.familyName
        s1.styleName = self.ufo.info.styleName
        self.ds.addSource(s1)
        self.font = Font()
        return self._load()
