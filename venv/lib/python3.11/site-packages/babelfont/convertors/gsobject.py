from datetime import datetime
from babelfont import *
import openstep_plist
from fontTools.misc.transform import Transform
from fontFeatures.feaLib import FeaParser
from babelfont.convertors import BaseConvertor
import re
import math
import uuid
from collections import OrderedDict
from glyphsLib.glyphdata import get_glyph
from fontTools.misc.filenames import userNameToFileName
import os


opentype_custom_parameters = {
    "typoAscender": ("OS/2", "sTypoAscender"),
    "typoDescender": ("OS/2", "sTypoDescender"),
    "typoLineGap": ("OS/2", "sTypoLineGap"),
    "winAscent": ("OS/2", "usWinAscent"),
    "winDescent": ("OS/2", "usWinDescent"),
    "hheaAscender": ("hhea", "ascent"),
    "hheaDescender": ("hhea", "descent"),
    "hheaLineGap": ("hhea", "lineGap"),
    "underlinePosition": ("post", "underlinePosition"),
    "underlineThickness": ("post", "underlineThickness"),
}

_rename_metrics = {"x-height": "xHeight", "cap height": "capHeight"}
_reverse_rename_metrics = {v: k for k, v in _rename_metrics.items()}


def _glyphs_metrics_to_ours(k):
    return _rename_metrics.get(k, k)


def _our_metrics_to_glyphs(k):
    return _reverse_rename_metrics.get(k, k)


class GSObject(BaseConvertor):
    @classmethod
    def can_load(cls, convertor):
        return "gsfont" in convertor.scratch

    def _load(self):
        self.gsfont = self.scratch["gsfont"]
        self.customParameters = {}
        for param in self.gsfont.customParameters:
            self.customParameters[param.name] = param.value
        self._load_axes()
        self._load_kern_groups(self.gsfont.glyphs)

        for gmaster in self.gsfont.masters:
            self.font.masters.append(self._load_master(gmaster))
        self._fixup_axes()

        for gglyph in self.gsfont.glyphs:
            g = self._load_glyph(gglyph)
            self.font.glyphs.append(g)

        for ginstance in self.gsfont.instances:
            self.font.instances.append(self._load_instance(ginstance))

        self._fixup_axis_mappings()

        self._load_metadata()
        self._load_features()
        return self.font

    def _fixup_axes(self):
        for master in self.font.masters:
            for axis in self.font.axes:
                thisLoc = master.location[axis.tag]
                if axis.min is None or thisLoc < axis.min:
                    axis.min = thisLoc
                if master.id == self._default_master_id():
                    axis.default = master.location[axis.tag]
                if axis.max is None or thisLoc > axis.max:
                    axis.max = thisLoc

    def _fixup_axis_mappings(self):
        for axis in self.font.axes:
            if not axis.map:
                continue
            axis.map = list(sorted(set(axis.map)))
            axis.min, axis.max, axis.default = (
                axis.map_backward(axis.min),
                axis.map_backward(axis.max),
                axis.map_backward(axis.default),
            )

    def _custom_parameter(self, thing, name):
        for param in (thing.customParameters or []):
            if param.name == name:
                return param.value
        return None

    def _default_master_id(self):
        # The default master in glyphs is either the first master or the
        # one selected by the Variable Font Origin custom parameter
        return (
            self._custom_parameter(self.gsfont, "Variable Font Origin")
            or self.gsfont.masters[0].id
        )

    def _load_axes(self):
        self.axis_name_map = {}
        for gaxis in self.gsfont.axes:
            axis = Axis(name=gaxis.name, tag=gaxis.axisTag)
            self.axis_name_map[gaxis.name] = axis
            _maybesetformatspecific(axis, gaxis, "hidden")
            self.font.axes.append(axis)

    def _load_master(self, gmaster):
        location = gmaster.axes
        metrics = self.gsfont.metrics()
        master = Master(name=gmaster.name, id=gmaster.id, font=self.font)
        metric_types = [m.name or m.typeName() for m in metrics]
        for k, v in zip(metric_types, gmaster.metrics()):
            master.metrics[_glyphs_metrics_to_ours(k)] = v.position
            if v.overshoot:
                master.metrics["%s overshoot" % _glyphs_metrics_to_ours(k)] = v.overshoot

        master.location = {k.tag: v for k, v in zip(self.font.axes, location)}
        master.guides = [self._load_guide(x) for x in gmaster.guides]
        kerntable = self.gsfont.kerning.get(master.id, {})
        master.kerning = self._load_kerning(kerntable)
        # XXX support RTL kerning etc.

        # _maybesetformatspecific(master, gmaster, "customParameters") # XXX
        _maybesetformatspecific(master, gmaster, "iconName")
        _maybesetformatspecific(master, gmaster, "numberValues")
        _maybesetformatspecific(master, gmaster, "stemValues")
        _maybesetformatspecific(master, gmaster, "properties")
        _maybesetformatspecific(master, gmaster, "userData")
        _maybesetformatspecific(master, gmaster, "visible")
        assert master.valid
        return master

    def _get_codepoint(self, gglyph):
        if gglyph.unicodes:
            return [int(x,16) for x in gglyph.unicodes]
        return []

    def _load_glyph(self, gglyph):
        name = gglyph.name
        c = gglyph.category
        sc = gglyph.subCategory
        if sc == "Ligature":
            category = "ligature"
        if c == "Mark":
            category = "mark"
        else:
            category = "base"
        cp = self._get_codepoint(gglyph)
        g = Glyph(
            name=name,
            codepoints=cp,
            category=category,
            exported=gglyph.export,
        )
        g.production_name = gglyph.productionName or get_glyph(name).production_name
        for entry in [
            "case",
            "category",
            "subCategory",
            "color",
            "direction",
            "locked",
            "partsSettings",
            "script",
            "tags",
        ]:
            _maybesetformatspecific(g, gglyph, entry)

        for layer in gglyph.layers:
            g.layers.extend(self._load_layer(layer))

        return g

    def _load_layer(self, layer, width=None):
        if width is None:
            width = layer.width
        l = Layer(width=width, id=str(layer.layerId), _font=self.font)
        l.name = layer.name
        if [x for x in self.font.masters if x.id == l.id]:
            l._master = l.id
        else:
            l._master = layer.associatedMasterId
        l.guides = [self._load_guide(x) for x in layer.guides]
        l.shapes = []
        for shape in layer.shapes:
            l.shapes.append(self._load_shape(shape))
        for anchor in layer.anchors:
            l.anchors.append(self._load_anchor(anchor))

        _maybesetformatspecific(l, layer, "hints")
        _maybesetformatspecific(l, layer, "partSelection")
        _maybesetformatspecific(l, layer, "visible")
        _maybesetformatspecific(l, layer, "attr")
        returns = [l]
        if "Background" not in str(type(layer)) and layer.background:
            (background,) = self._load_layer(layer.background, width=l.width)
            # If it doesn't have an ID, we need to generate one
            background.id = str(uuid.uuid1())
            # XXX
            # For some INSANE REASON orjson is serializing this to `True` in json,
            # not `true`.
            #background.isBackground = True
            del(background._master)

            l._background = background.id
            returns.append(background)
        # TODO backgroundImage, metricTop/Bottom/etc, vertOrigin, vertWidth.
        for r in returns:
            assert r.valid
        return returns

    def _load_guide(self, gguide):
        pos = gguide.position
        return Guide(pos=[int(pos[0]), int(pos[1]), int(gguide.angle)])

    def _load_anchor(self, ganchor):
        pos = ganchor.position
        return Anchor(name=ganchor.name, x=float(pos[0]), y=float(pos[1]))

    def _load_instance(self, ginstance):
        if ginstance.axes:
            location = ginstance.axes
            instance_location = {k.tag: v for k, v in zip(self.font.axes, location)}
        elif ginstance.instanceInterpolations:
            # All right then.
            instance_location = {k.tag: 0 for k in self.font.axes}
            for mId, factor in ginstance.instanceInterpolations.items():
                master_loc = self.font.master(mId).location
                for k in self.font.axes:
                    instance_location[k.tag] += master_loc[k.tag] * factor
        else:
            raise ValueError("Need to Synthesize location")
        i = Instance(
            name=ginstance.name,
            styleName=ginstance.name,
            location=instance_location,
        )
        c = self._custom_parameter(ginstance, "Axis Location") or []
        for loc in c:
            ax = self.axis_name_map[loc["Axis"]]
            if not ax.map:
                ax.map = []
            ax.map.append(
                (
                    int(loc["Location"]),
                    instance_location[ax.tag],
                )
            )

        # _maybesetformatspecific(i, ginstance, "customParameters") # XXX
        return i

    def _load_component(self, shape):
        glyphname = shape.componentName
        transform = shape.transform
        c = Shape(ref=glyphname)
        c.transform = transform
        for entry in [
            "alignment",
            "anchorTo",
            "attr",
            "locked",
            "orientation",
            "piece",
            "userData",
        ]:
            _maybesetformatspecific(c, shape, entry)
        return c

    def _load_kerning(self, kerndict):
        return {
            (l, r): value
            for l, level2 in kerndict.items()
            for r, value in level2.items()
        }

    def _load_metadata(self):
        self.font.upm = self.gsfont.upm
        self.font.version = (self.gsfont.versionMajor, self.gsfont.versionMinor)
        self.font.names.familyName.set_default(self.gsfont.familyName)

        # This is very glyphs 3
        props = {}
        for prop in self.gsfont.properties:
            if hasattr(prop, "value"):
                props[prop.key] = prop.value
            else:
                props[prop.key] = {p.languageTag: p.value for p in prop.values}

        if props:
            interestingProps = {
                "copyrights": "copyright",
                "designer": "designer",
                "designerURL": "designerURL",
            }  # Etc
            for glyphsname, attrname in interestingProps.items():
                thing = props.get(glyphsname, "")
                if hasattr(thing, dict):
                    getattr(self.font.names, attrname).copy_in(thing)
                else:
                    getattr(self.font.names, attrname).set_default(thing)
            # Do other properties here

        # Any customparameters in the default master which look like
        # custom OT values need to move there.
        cp = self.font.default_master._formatspecific.get("com.glyphsapp", {}).get(
            "customParameters", {}
        )
        for param in cp:
            ot_param = opentype_custom_parameters.get(param.name)
            if not ot_param:
                continue
            self.font.customOpenTypeValues.append(
                OTValue(ot_param[0], ot_param[1], param.value)
            )

        self.font.note = self.gsfont.note
        self.font.date = self.gsfont.date

        _maybesetformatspecific(self.font, self.gsfont, ".appVersion")
        _maybesetformatspecific(self.font, self.gsfont, ".formatVersion")
        _maybesetformatspecific(self.font, self.gsfont, "DisplayStrings")
        _maybesetformatspecific(self.font, self.gsfont, "customParameters")
        _maybesetformatspecific(self.font, self.gsfont, "settings")
        _maybesetformatspecific(self.font, self.gsfont, "numbers")
        _maybesetformatspecific(self.font, self.gsfont, "stems")
        _maybesetformatspecific(self.font, self.gsfont, "userData")
        _maybesetformatspecific(self.font, self.gsfont, "metrics")

    def _load_features(self):
        for c in self.gsfont.classes:
            self.font.features.namedClasses[c.name] = tuple(c.code.split())

        featurefile = ""
        for f in self.gsfont.featurePrefixes:
            featurefile = featurefile + f.code
        for f in self.gsfont.features:
            tag = f.name
            feacode = "feature %s { %s\n} %s;" % (tag, f.code, tag)
            featurefile = featurefile + feacode

        try:
            feaparser = FeaParser(featurefile)
            ast = feaparser.parser.ast
            for name, members in self.font.features.namedClasses.items():
                glyphclass = ast.GlyphClassDefinition(
                    name, ast.GlyphClass([m for m in members])
                )
                feaparser.parser.glyphclasses_.define(name, glyphclass)
            feaparser.parse()
        except Exception as e:
            pass

    def _load_shape(self, shape):
        if hasattr(shape, "nodes"):  # It's a path
            return self._load_path(shape)
        else:
            return self._load_component(shape)

    def _load_path(self, path):
        shape = Shape()
        shape.nodes = [Node(n.position.x, n.position.y, n.type[0]) for n in path.nodes]
        shape.closed = path.closed
        return shape

    def _load_kern_groups(self, glyphs):
        kerngroups = {}
        for g in glyphs:
            if g.leftKerningGroup:
                kerngroups.setdefault("MMK_L_" + g.leftKerningGroup, []).append(
                    g.name
                )
            if g.rightKerningGroup:
                kerngroups.setdefault("MMK_R_" + g.rightKerningGroup, []).append(
                    g.name
                )
        for k, v in kerngroups.items():
            self.font.features.namedClasses[k] = tuple(v)


def _maybesetformatspecific(item, glyphs, key):
    if hasattr(glyphs, key):
        if "com.glyphsapp" not in item._formatspecific:
            item._formatspecific["com.glyphsapp"] = {}
        value = getattr(glyphs, key) # XXX
        try:
            orjson.dumps(value)
            item._formatspecific["com.glyphsapp"][key] = value
        except Exception as e:
            print("%s.%s cannot be serialized!" % (glyphs, key))


def _moveformatspecific(item):
    rv = {}
    if "com.glyphsapp" in item._formatspecific:
        rv = {**item._formatspecific.get("com.glyphsapp", {})}
    return rv


def _copyattrs(src, dst, attrs):
    for a in attrs:
        v = getattr(src, a)
        if isinstance(v, I18NDictionary):
            v = v.get_default()
        if v:
            dst[a] = v
