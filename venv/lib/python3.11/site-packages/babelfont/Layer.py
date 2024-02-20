from dataclasses import dataclass, field
from functools import cached_property

from fontTools.ufoLib.pointPen import PointToSegmentPen, SegmentToPointPen, AbstractPointPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen

from .BaseObject import BaseObject, Color
from .Guide import Guide
from .Anchor import Anchor
from .Node import Node
from .Shape import Shape
import uuid


@dataclass
class _LayerFields:
    width: int = 0
    name: str = None
    _master: str = None
    id: str = field(default_factory = lambda: str(uuid.uuid1()))
    guides: [Guide] = field(default_factory = list, repr=False)
    shapes: [Shape] = field(default_factory=list, repr=False, metadata={"separate_items": True})
    anchors: [Anchor] = field(default_factory = list, repr=False)
    color: Color = None
    layerIndex: int = 0
    # hints: [Hint]
    _background: str = field(default=None,repr=False)
    isBackground: bool = field(default=False,repr=False)
    location: [float] = None
    _font: object = field(
        default=None, repr=False, metadata={"python_only": True}
    )  # Can't type Font because of circularity


@dataclass
class Layer(BaseObject, _LayerFields):
    @property
    def master(self):
        assert self._font
        return self._font.master(self._master)

    @property
    def paths(self):
        return [x for x in self.shapes if x.is_path]

    @property
    def components(self):
        return [x for x in self.shapes if x.is_component]

    def recursiveComponentSet(self):
        mine = set([x.ref for x in self.components])
        theirs = set()
        for c in mine:
            theirs |= self.master.get_glyph_layer(c).recursiveComponentSet()
        return mine | theirs

    @cached_property
    def bounds(self):
        glyphset = {}
        for c in list(self.recursiveComponentSet()):
            glyphset[c] = self.master.get_glyph_layer(c)
        pen = BoundsPen(glyphset)
        self.draw(pen)
        return pen.bounds

    @property
    def lsb(self):
        if not self.bounds:  # Space glyph
            return 0
        return self.bounds[0]

    @property
    def rsb(self):
        if not self.bounds:  # Space glyph
            return 0
        return self.width - self.bounds[2]

    @property
    def valid(self):
        if not self._font:
            return False
        return True

    @property
    def anchors_dict(self):
        return { a.name: a for a in self.anchors }

    # Pen protocol support...

    def draw(self, pen):
        pen = PointToSegmentPen(pen)
        return self.drawPoints(pen)

    def drawPoints(self, pen):
        for path in self.paths:
            pen.beginPath()
            for node in path.nodes:
                pen.addPoint(
                    pt=(node.x, node.y),
                    segmentType=node.pen_type,
                    smooth=node.is_smooth,
                )
            pen.endPath()
        for component in self.components:
            pen.addComponent(component.ref, component.transform)

    def clearContours(self):
        self.shapes = []

    def getPen(self):
        return SegmentToPointPen(LayerPen(self))

    def _nestedComponentDict(self):
        result = {}
        todo = [x.ref for x in self.components]
        while todo:
            current = todo.pop()
            if current in result:
                continue
            result[current] = self.master.get_glyph_layer(current)
            todo.extend([x.ref for x in result[current].components])
        return result

    def decompose(self):
        pen = DecomposingRecordingPen(self._nestedComponentDict())
        self.draw(pen)
        self.clearContours()
        pen.replay(self.getPen())


class LayerPen(AbstractPointPen):
    def __init__(self, target):
        self.target = target
        self.curPath = []

    def beginPath(self, identifier=None, **kwargs):
        self.curPath = []

    def endPath(self):
        """End the current sub path."""
        self.target.shapes.append(Shape(nodes=self.curPath))

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 identifier=None, **kwargs):
        ourtype = Node._from_pen_type[segmentType]
        if smooth:
            ourtype = ourtype + "s"
        self.curPath.append(Node(pt[0], pt[1], ourtype))

    def addComponent(self, baseGlyphName, transformation, identifier=None,
                     **kwargs):
        self.target.shapes.append(Shape(ref=baseGlyphName, transform=transformation))
