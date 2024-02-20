from babelfont import *
from babelfont.convertors import BaseConvertor
from fontTools.designspaceLib import DesignSpaceDocument
import ufoLib2
import uuid
import logging


log = logging.getLogger(__name__)


class Designspace(BaseConvertor):
    suffix = ".designspace"

    @classmethod
    def load(cls, convertor):
        self = cls()
        self.ds = DesignSpaceDocument.fromfile(convertor.filename)
        self.ds.loadSourceFonts(ufoLib2.Font.open)
        self.font = Font()
        return self._load()

    def _load(self):
        self._load_axes()

        for source in self.ds.sources:
            source._babelfont_master = self._load_master(source)
            self.font.masters.append(source._babelfont_master)

        for instance in self.ds.instances:
            self.font.instances.append(self._load_instance(instance))

        firstmaster = self.ds.sources[0].font
        self._load_metadata(firstmaster)
        glyphs_dict = self._load_glyphs(firstmaster)

        # Right, let's find all the layers. This will be messy.
        for source in self.ds.sources:
            for ufo_layer in source.font.layers:
                for g in source.font.glyphOrder:
                    if g not in glyphs_dict:
                        log.warn(
                            "Incompatible glyph set: %s appears in %s but is not in default"
                            % (g, source.filename)
                        )
                        continue
                    if g not in ufo_layer:
                        continue
                    glyphs_dict[g].layers.append(self._load_layer(source, ufo_layer, g))
        self._fixup_glyph_exported(self.ds.sources[0].font)
        return self.font

    def _fixup_glyph_exported(self, ufo):
        for glyph in ufo.lib.get("public.skipExportGlyphs", []):
            self.font.glyphs[glyph].exported = False

    def _load_glyphs(self, master):
        glyphs_dict = {}
        for g in master.glyphOrder:
            glyphs_dict[g] = self._load_glyph(master[g])
            self.font.glyphs.append(glyphs_dict[g])
        return glyphs_dict

    def _load_axes(self):
        for a in self.ds.axes:
            self.font.axes.append(
                Axis(
                    name=a.name,
                    tag=a.tag,
                    min=a.minimum,
                    max=a.maximum,
                    default=a.default,
                    map=a.map,
                )
            )

    def _load_master(self, source):
        i = source.font.info
        master = Master(
            name=source.name,
            id=(source.name or uuid.uuid1()),
        )
        for metric in Master.CORE_METRICS:
            master.metrics[metric] = getattr(i, metric)
        _axis_name_to_id = {a.name.get_default(): a.tag for a in self.font.axes}
        # italic angle
        # names XXX
        # guidelines
        master.guides = [self._load_guide(g) for g in (i.guidelines or [])]
        master.location = {_axis_name_to_id[k]: v for k, v in source.location.items()}
        master.font = self.font
        master.kerning = self._load_kerning(source)
        self._load_groups(source.name, source.font.groups)
        assert master.valid
        return master

    def _load_groups(self, sourcename, groups):
        for name, value in groups.items():
            if (
                name in self.font.features.namedClasses
                and self.font.features.namedClasses[name] != value
            ):
                log.warn(
                    "Inconsistent definition of glyph class @%s found in %s"
                 % (name, sourcename))
            self.font.features.namedClasses[name] = value

    def _load_guide(self, ufo_guide):
        return Guide(
            pos=[ufo_guide.x, ufo_guide.y, ufo_guide.angle],
            name=ufo_guide.name,
            color=ufo_guide.color,
        )

    def _load_kerning(self, source):
        kerning = {}
        for (l, r), value in source.font.kerning.items():
            if l.startswith("public.kern"):
                l = "@" + l
            if r.startswith("public.kern"):
                r = "@" + r
            kerning[(l, r)] = value
        return kerning

    def _load_glyph(self, ufo_glyph):
        cp = ufo_glyph.unicodes or [ufo_glyph.unicode]
        lib = self.ds.sources[0].font.lib
        category = lib.get("public.openTypeCategories", {}).get(ufo_glyph.name, "base")
        g = Glyph(name=ufo_glyph.name, codepoints=cp, category=category)
        if "public.postscriptNames" in lib and g.name in lib["public.postscriptNames"]:
            g.production_name = lib["public.postscriptNames"][g.name]
        return g

    def _load_layer(self, source, ufo_layer, glyphname):
        ufo_glyph = ufo_layer[glyphname]
        width = ufo_glyph.width
        l = Layer(width=width, id=uuid.uuid1())
        l._master = source._babelfont_master.id
        l._font = self.font
        for contour in ufo_glyph:
            l.shapes.append(self._load_contour(contour))
        for component in ufo_glyph.components:
            l.shapes.append(self._load_component(component))
        for anchor in ufo_glyph.anchors:
            l.anchors.append(self._load_anchor(anchor))
        assert l.valid
        return l

    def _load_component(self, shape):
        c = Shape(ref=shape.baseGlyph, transform=shape.transformation)
        return c

    def _load_anchor(self, anchor):
        return Anchor(name=anchor.name, x=int(anchor.x), y=int(anchor.y))

    def _load_contour(self, contour):
        shape = Shape()
        shape.nodes = []
        for p in contour:
            segtype = p.segmentType
            if p.segmentType == "move":
                segtype = "line"
            ourtype = Node._from_pen_type[segtype]
            if p.smooth:
                ourtype = ourtype + "s"
            shape.nodes.append(Node(p.x, p.y, ourtype))
        return shape

    def _load_instance(self, ufo_instance):
        _axis_tag = {axis.name.get_default(): axis.tag for axis in self.font.axes}
        location = {_axis_tag[k]: v for k, v in ufo_instance.location.items()}
        instance = Instance(name=ufo_instance.name, location=location)
        return instance

    names_dict = {
        "designer": "openTypeNameDesigner",
        "designerURL": "openTypeNameDesignerURL",
        "manufacturer": "openTypeNameManufacturer",
        "manufacturerURL": "openTypeNameManufacturerURL",
        "license": "openTypeNameLicense",
        "licenseURL": "openTypeNameLicenseURL",
        "version": "openTypeNameVersion",
        "uniqueID": "openTypeNameUniqueID",
        "description": "openTypeNameDescription",
        "compatibleFullName": "openTypeNameCompatibleFullName",
        "sampleText": "openTypeNameSampleText",
        "WWSFamilyName": "openTypeNameWWSFamilyName",
        "WWSSubfamilyName": "openTypeNameWWSSubfamilyName",
        "copyright": "copyright",
        "styleMapFamilyName": "styleMapFamilyName",
        "familyName": "familyName",
        "trademark": "trademark",
    }

    def _load_metadata(self, ufo):
        firstfontinfo = ufo.info
        self.font.upm = firstfontinfo.unitsPerEm
        self.font.version = (firstfontinfo.versionMajor, firstfontinfo.versionMinor)
        self.font.note = firstfontinfo.note
        for ours, theirs in self.names_dict.items():
            their_value = getattr(firstfontinfo, theirs)
            if their_value:
                getattr(self.font.names, ours).set_default(their_value)
