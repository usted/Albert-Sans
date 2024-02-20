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


class GlyphsTwo(BaseConvertor):
    suffix = ".glyphs"

    @classmethod
    def is_suitable_plist(cls, convertor):
        return (
            ".formatVersion" not in convertor.scratch["plist"]
            or convertor.scratch["plist"][".formatVersion"] < 3
        )

    @classmethod
    def can_save(cls, convertor, **kwargs):
        if not super().can_save(convertor, **kwargs):
            return False
        if "format" in kwargs:
            return kwargs["format"] == 2
        return True

    @classmethod
    def can_load(cls, convertor):
        if not super().can_load(convertor):
            return False
        if not "plist" in convertor.scratch:
            convertor.scratch["plist"] = openstep_plist.load(
                open(convertor.filename, "r"), use_numbers=True
            )
        return cls.is_suitable_plist(convertor)

    def _load(self):
        self.glyphs = self.scratch["plist"]
        self.customParameters = {}
        for param in self.glyphs.get("customParameters", []):
            self.customParameters[param["name"]] = param["value"]
        self._load_axes()

        self._load_kern_groups(self.glyphs["glyphs"])

        for gmaster in self.glyphs["fontMaster"]:
            self.font.masters.append(self._load_master(gmaster))
        self._fixup_axes()
        if not self.font.default_master:
            raise ValueError("Cannot identify default master")

        for gglyph in self.glyphs["glyphs"]:
            g = self._load_glyph(gglyph)
            self.font.glyphs.append(g)

        for ginstance in self.glyphs.get("instances", []):
            self.font.instances.append(self._load_instance(ginstance))

        self._fixup_axis_mappings()

        self._load_metadata()
        self._load_features()
        return self.font

    def _load_axes(self):
        self.axis_name_map = {}
        if "Axes" in self.customParameters:
            for ax in self.customParameters["Axes"]:
                self.font.axes.append(Axis(name=ax["Name"], tag=ax["Tag"]))
                self.axis_name_map[ax["Name"]] = self.font.axes[-1]
        else:
            self.font.axes.append(Axis(name="Weight", tag="wght"))
            self.font.axes.append(Axis(name="Width", tag="wdth"))
            self.axis_name_map = {
                "Weight": self.font.axes[-1],
                "Width": self.font.axes[-1],
            }

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
        for param in thing.get("customParameters", []):
            if param["name"] == name:
                return param["value"]
        return None

    def _default_master_id(self):
        # The default master in glyphs is either the first master or the
        # one selected by the Variable Font Origin custom parameter
        vfo = self._custom_parameter(self.glyphs, "Variable Font Origin")
        if vfo and vfo in self.font._master_map:
            return vfo
        return self.glyphs["fontMaster"][0]["id"]

    def _get_master_name(self, gmaster):
        if gmaster.get("name"):
            return gmaster["name"]
        cname = self._custom_parameter(gmaster, "Master Name")
        if cname:
            return cname
        # Remove None and empty string
        names = list(filter(None, [
            gmaster.get("width", "Regular"),
            gmaster.get("weight", "Regular"),
            gmaster.get("custom", "")]))

        # Remove redundant occurences of 'Regular'
        while len(names) > 1 and "Regular" in names:
            names.remove("Regular")
        if gmaster.get("italicAngle"):
            if names == ["Regular"]:
                return "Italic"
            if "Italic" not in gmaster.get("custom", ""):
                names.append("Italic")
        return " ".join(names)

    def _load_master(self, gmaster):
        # location = gmaster.get("axesValues", [])
        master = Master(
            name=self._get_master_name(gmaster),
            id=gmaster.get("id"),
        )
        for metric in Master.CORE_METRICS:
            master.metrics[metric] = gmaster.get(_glyphs_metrics_to_ours(metric))
        # Check for metrics in custom parameters

        master.font = self.font

        axisloc = self._custom_parameter(gmaster, "Axis Location")
        if axisloc:
            # I dunno, use that? Needs mapping? Check we are using tags/IDs
            location = axisloc
        else:
            potential_locations = [
                gmaster.get("weightValue", 100),
                gmaster.get("widthValue", 100),
                gmaster.get("customValue", 0),
                gmaster.get("customValue1", 0),
                gmaster.get("customValue2", 0),
                gmaster.get("customValue3", 0),
            ]
            location = {}
            for k, loc in zip(self.font.axes, potential_locations):
                location[k.tag] = loc
        master.location = location

        master.guides = [self._load_guide(x) for x in gmaster.get("guides", [])]

        kernmaster = None
        if self._custom_parameter(gmaster, "Link Metrics With First Master"):
            kernmaster = self.glyphs["fontMaster"][0]["id"]
        elif self._custom_parameter(gmaster, "Link Metrics With Master"):
            kernmaster_name = self._custom_parameter(gmaster, "Link Metrics With Master")
            for m in self.glyphs["fontMaster"]:
                name = self._get_master_name(m)
                if name == kernmaster_name:
                    kernmaster = m["id"]
        else:
            kernmaster = master.id
        kerntable = self.glyphs.get("kerning", {}).get(kernmaster, {})
        master.kerning = self._load_kerning(kerntable)

        _maybesetformatspecific(master, gmaster, "customParameters")
        _maybesetformatspecific(master, gmaster, "iconName")
        _maybesetformatspecific(master, gmaster, "id")
        _maybesetformatspecific(master, gmaster, "numberValues")
        _maybesetformatspecific(master, gmaster, "stemValues")
        _maybesetformatspecific(master, gmaster, "properties")
        _maybesetformatspecific(master, gmaster, "userData")
        _maybesetformatspecific(master, gmaster, "visible")
        return master

    def _get_codepoint(self, gglyph):
        cp = gglyph.get("unicode")
        if not cp:
            return []
        if isinstance(cp, int):
            return [int("%04i" % cp, 16)]
        return [int(x, 16) for x in cp.split(",")]

    def _load_glyph(self, gglyph):
        name = gglyph["glyphname"]
        c = gglyph.get("category")
        sc = gglyph.get("subCategory")
        if sc == "Ligature":
            category = "ligature"
        if c == "Mark":
            category = "mark"
        else:
            category = "base"
        cp = self._get_codepoint(gglyph)
        exported = True
        if "export" in gglyph and gglyph["export"] == 0:
            exported = False
        g = Glyph(
            name=name,
            codepoints=cp or [],
            category=category,
            exported=exported
        )
        g.production_name = gglyph.get("production", get_glyph(name).production_name)
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
            "userData"
        ]:
            _maybesetformatspecific(g, gglyph, entry)

        for layer in gglyph.get("layers"):
            g.layers.extend(self._load_layer(layer))

        return g

    def _load_layer(self, layer, width=None):
        if width is None:
            width = layer["width"]
        l = Layer(width=width, id=layer.get("layerId"), _font=self.font)
        l.name = layer.get("name")
        if [x for x in self.font.masters if x.id == l.id]:
            l._master = l.id
        else:
            l._master = layer.get("associatedMasterId")
        l.guides = [
            self._load_guide(x)
            for x in layer.get("guideLines", layer.get("guides", []))
        ]
        l.shapes = []
        for shape in layer.get("shapes", []):
            l.shapes.append(self._load_shape(shape))
        for shape in layer.get("paths", []):
            l.shapes.append(self._load_path(shape))
        for shape in layer.get("components", []):
            l.shapes.append(self._load_component(shape))
        for anchor in layer.get("anchors", []):
            l.anchors.append(self._load_anchor(anchor))

        _maybesetformatspecific(l, layer, "hints")
        _maybesetformatspecific(l, layer, "partSelection")
        _maybesetformatspecific(l, layer, "visible")
        _maybesetformatspecific(l, layer, "attr")
        _maybesetformatspecific(l, layer, "vertOrigin")
        _maybesetformatspecific(l, layer, "vertWidth")
        _maybesetformatspecific(l, layer, "metricTop")
        _maybesetformatspecific(l, layer, "metricBottom")
        _maybesetformatspecific(l, layer, "metricLeft")
        _maybesetformatspecific(l, layer, "metricRight")
        returns = [l]
        if "background" in layer:
            (background,) = self._load_layer(layer["background"], width=l.width)
            # If it doesn't have an ID, we need to generate one
            background.id = background.id or str(uuid.uuid1())
            background.isBackground = True

            l._background = background.id
            returns.append(background)
        # TODO backgroundImage, metricTop/Bottom/etc, vertOrigin, vertWidth.
        for r in returns:
            assert r.valid
        return returns

    def _load_guide(self, gguide):
        pos = gguide.get("position", "{0, 0}")
        m = re.match(r"^\{(\S+), (\S+)\}", pos)
        return Guide(pos=[int(m[1]), int(m[2]), int(gguide.get("angle", 0))])

    def _load_anchor(self, ganchor):
        pos = ganchor.get("position", "{0, 0}")
        m = re.match(r"^\{(\S+), (\S+)\}", pos)
        return Anchor(name=ganchor["name"], x=float(m[1]), y=float(m[2]))

    def _load_instance(self, ginstance):
        if "axesValues" in ginstance:
            location = ginstance["axesValues"]
            instance_location = {k.tag: v for k, v in zip(self.font.axes, location)}
        elif "instanceInterpolations" in ginstance:
            # All right then.
            instance_location = {k.tag: 0 for k in self.font.axes}
            for mId, factor in ginstance["instanceInterpolations"].items():
                master_loc = self.font.master(mId).location
                for k in self.font.axes:
                    instance_location[k.tag] += master_loc[k.tag] * factor
        else:
            raise ValueError("Need to Synthesize location")
        i = Instance(
            name=ginstance["name"],
            styleName=ginstance["name"],
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

        _maybesetformatspecific(i, ginstance, "customParameters")
        return i

    def _load_path(self, path):
        shape = Shape()
        shape.nodes = []
        for n in path["nodes"]:
            m = re.match(r"(\S+) (\S+) (\S+)( SMOOTH)?(.*)", n)
            ntype = m[3][0].lower()
            if m[4]:
                ntype = ntype + "s"
            n = Node(x=float(m[1]), y=float(m[2]), type=ntype)
            shape.nodes.append(n)
        shape.closed = bool(path["closed"])
        _maybesetformatspecific(shape, path, "attr")
        return shape

    def _load_component(self, shape):
        glyphname = shape.get("ref", shape.get("name"))
        transform = shape.get("transform")
        if isinstance(transform, str):
            m = re.match(r"^\{(\S+), (\S+), (\S+), (\S+), (\S+), (\S+)\}", transform)
            transform = Transform(*[float(g) for g in m.groups()])
        c = Shape(ref=glyphname)

        if not transform:
            translate = Transform().translate(*shape.get("pos", (0, 0)))
            scale = Transform().scale(*shape.get("scale", (1, 1)))
            rotation = Transform().rotate(math.radians(shape.get("angle", 0)))
            # Compute transform...
            transform = translate.transform(scale).transform(rotation)

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

    def _load_kern_groups(self, glyphs):
        kerngroups = {}
        for g in glyphs:
            l_class = g.get("leftKerningGroup", g["glyphname"])
            r_class = g.get("rightKerningGroup", g["glyphname"])
            # DAMMIT GLYPHS
            kerngroups.setdefault("MMK_R_" + l_class, []).append(g["glyphname"])
            kerngroups.setdefault("MMK_L_" + r_class, []).append(g["glyphname"])
        for k, v in kerngroups.items():
            self.font.features.namedClasses[k] = tuple(v)

    def _load_kerning(self, kerndict):
        return {
            (l, r): value
            for l, level2 in kerndict.items()
            for r, value in level2.items()
        }

    def _load_metadata(self):
        self.font.upm = self.glyphs["unitsPerEm"]
        self.font.version = (self.glyphs["versionMajor"], self.glyphs["versionMinor"])
        self.font.names.familyName.set_default(self.glyphs["familyName"])

        # This is very glyphs 3
        props = {}
        for prop in self.glyphs.get("properties", []):
            if "value" in prop:
                props[prop["key"]] = prop["value"]
            else:
                props[prop["key"]] = {p["language"]: p["value"] for p in prop["values"]}

        if props:
            interestingProps = {
                "copyrights": "copyright",
                "designer": "designer",
                "designerURL": "designerURL",
            }  # Etc
            for glyphsname, attrname in interestingProps.items():
                thing = props.get(glyphsname, "")
                if isinstance(thing, dict):
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
            ot_param = opentype_custom_parameters.get(param["name"])
            if not ot_param:
                continue
            self.font.customOpenTypeValues.append(
                OTValue(ot_param[0], ot_param[1], param["value"])
            )

        self.font.note = self.glyphs.get("note")
        self.font.date = datetime.strptime(
            self.glyphs.get("date"), "%Y-%m-%d %H:%M:%S +0000"
        )
        _maybesetformatspecific(self.font, self.glyphs, ".appVersion")
        _maybesetformatspecific(self.font, self.glyphs, ".formatVersion")
        _maybesetformatspecific(self.font, self.glyphs, "DisplayStrings")
        _maybesetformatspecific(self.font, self.glyphs, "customParameters")
        _maybesetformatspecific(self.font, self.glyphs, "settings")
        _maybesetformatspecific(self.font, self.glyphs, "numbers")
        _maybesetformatspecific(self.font, self.glyphs, "stems")
        _maybesetformatspecific(self.font, self.glyphs, "userData")
        _maybesetformatspecific(self.font, self.glyphs, "metrics")
        _maybesetformatspecific(self.font, self.glyphs, "properties")

    def _load_features(self):
        for c in self.glyphs.get("classes", []):
            self.font.features.namedClasses[c["name"]] = tuple(c["code"].split())

        featurefile = ""
        for f in self.glyphs.get("featurePrefixes", []):
            featurefile = featurefile + f.get("code")
        for f in self.glyphs.get("features", []):
            tag = f.get("tag", f.get("name", ""))
            feacode = "feature %s { %s\n} %s;" % (tag, f["code"], tag)
            featurefile = featurefile + feacode

        feaparser = FeaParser(featurefile)
        ast = feaparser.parser.ast
        for name, members in self.font.features.namedClasses.items():
            glyphclass = ast.GlyphClassDefinition(
                name, ast.GlyphClass([m for m in members])
            )
            feaparser.parser.glyphclasses_.define(name, glyphclass)
        feaparser.parse()
        self.font.features += feaparser.ff


class GlyphsThree(GlyphsTwo):
    @classmethod
    def is_suitable_plist(cls, convertor):
        return (
            ".formatVersion" in convertor.scratch["plist"]
            and convertor.scratch["plist"][".formatVersion"] >= 3
        )

    @classmethod
    def can_save(cls, convertor, **kwargs):
        if not convertor.filename.endswith(".glyphs"):
            return False
        if "format" in kwargs:
            return kwargs["format"] == 3
        return True

    def _load_axes(self):
        self.axis_name_map = {}
        for gaxis in self.glyphs.get("axes", []):
            axis = Axis(name=gaxis["name"], tag=gaxis["tag"])
            self.axis_name_map[gaxis["name"]] = axis
            _maybesetformatspecific(axis, gaxis, "hidden")
            self.font.axes.append(axis)

    def _get_master_name(self, gmaster):
        return gmaster["name"]

    def _load_master(self, gmaster):
        location = gmaster.get("axesValues", [])
        metrics = self.glyphs["metrics"]
        master = Master(name=gmaster["name"], id=gmaster["id"], font=self.font)
        metric_types = [m.get("type", m.get("name", "")) for m in metrics]
        for k, v in zip(metric_types, gmaster["metricValues"]):
            pos = v.get("pos", 0)
            master.metrics[_glyphs_metrics_to_ours(k)] = pos
            if v.get("over"):
                master.metrics["%s overshoot" % _glyphs_metrics_to_ours(k)] = v["over"]

        master.location = {k.tag: v for k, v in zip(self.font.axes, location)}
        master.guides = [self._load_guide(x) for x in gmaster.get("guides", [])]
        if self._custom_parameter(gmaster, "Link Metrics With First Master"):
            kernmaster = self.glyphs["fontMaster"][0]["id"]
        elif self._custom_parameter(gmaster, "Link Metrics With Master"):
            kernmaster_name = self._custom_parameter(gmaster, "Link Metrics With Master")
            for m in self.glyphs["fontMaster"]:
                name = self._get_master_name(m)
                if name == kernmaster_name:
                    kernmaster = m["id"]
        else:
            kernmaster = master.id
        kerntable = self.glyphs.get("kerningLTR", {}).get(kernmaster, {})

        master.kerning = self._load_kerning(kerntable)
        # XXX support RTL kerning etc.

        _maybesetformatspecific(master, gmaster, "customParameters")
        _maybesetformatspecific(master, gmaster, "iconName")
        _maybesetformatspecific(master, gmaster, "numberValues")
        _maybesetformatspecific(master, gmaster, "stemValues")
        _maybesetformatspecific(master, gmaster, "properties")
        _maybesetformatspecific(master, gmaster, "userData")
        _maybesetformatspecific(master, gmaster, "visible")
        assert master.valid
        return master

    def _load_guide(self, gguide):
        g = Guide(pos=[*gguide.get("pos", (0, 0)), gguide.get("angle", 0)])
        _maybesetformatspecific(g, gguide, "lockAngle")
        _maybesetformatspecific(g, gguide, "locked")
        _maybesetformatspecific(g, gguide, "showMeasurement")
        return g

    def _load_anchor(self, ganchor):
        x, y = ganchor.get("pos", (0, 0))
        return Anchor(name=ganchor["name"], x=x, y=y)

    def _load_shape(self, shape):
        if "nodes" in shape:  # It's a path
            return self._load_path(shape)
        else:
            return self._load_component(shape)

    def _load_path(self, path):
        shape = Shape()
        shape.nodes = [Node(*n[0:3]) for n in path["nodes"]]
        shape.closed = path["closed"]
        _maybesetformatspecific(shape, path, "attr")
        return shape

    def _get_codepoint(self, gglyph):
        cp = gglyph.get("unicode")
        if cp and not isinstance(cp, list):
            cp = [cp]
        if cp:
            return [int(x) for x in cp]

    def _load_kern_groups(self, glyphs):
        kerngroups = {}
        for g in glyphs:
            if "kernLeft" in g:
                kerngroups.setdefault("MMK_L_" + g["kernLeft"], []).append(
                    g["glyphname"]
                )
            if "kernRight" in g:
                kerngroups.setdefault("MMK_R_" + g["kernRight"], []).append(
                    g["glyphname"]
                )
        for k, v in kerngroups.items():
            self.font.features.namedClasses[k] = tuple(v)

    def _save(self):
        font = self.font
        out = _moveformatspecific(font)
        out["versionMajor"], out["versionMinor"] = font.version
        out[".formatVersion"] = 3
        out["unitsPerEm"] = font.upm
        if font.note:
            out["note"] = font.note
        if font.date:
            out["date"] = font.date.strftime("%Y-%m-%d %H:%M:%S +0000")
        out["familyName"] = font.names.familyName.default_or_dict()
        out["axes"] = [self._save_axis(ax) for ax in self.font.axes]

        # Sort out the metrics order, using "my" names
        metrics_order = []
        if "com.glyphsapp" in font._formatspecific:
            metrics_order = font._formatspecific["com.glyphsapp"].get("metrics", [])
            metrics_order = [
                _reverse_rename_metrics.get(x["type"], x["type"]) for x in metrics_order
            ]
        # Ensure we have all the metrics
        for m in font.masters:
            for k in m.metrics.keys():
                if k.endswith(" overshoot"):
                    continue  # We'll write it into the other metric
                if _our_metrics_to_glyphs(k) not in metrics_order:
                    metrics_order.append(_our_metrics_to_glyphs(k))
        # Now inject missing ones into the "metrics" dict, using Glyphs names
        if not "metrics" in out:
            out["metrics"] = []
        their_metrics = [x["type"] for x in out["metrics"]]
        for our_metric in metrics_order:
            their_name_for_our_metric = _our_metrics_to_glyphs(our_metric)
            if their_name_for_our_metric not in their_metrics:
                out["metrics"].append({"type": their_name_for_our_metric})
        # Use this later when outputting metric values
        self.metrics_order = metrics_order
        out["fontMaster"] = [self._save_master(m) for m in self.font.masters]
        out["glyphs"] = [self._save_glyph(g) for g in self.font.glyphs]
        kerntables = OrderedDict()
        for master in self.font.masters:
            table = self._save_kerning(master.kerning)
            if table:
                kerntables[master.id] = table
        if kerntables:
            out["kerningLTR"] = kerntables
        with open(self.filename, "wb") as file:
            openstep_plist.dump(out, file, indent=0, single_line_tuples=True)
            file.write(b"\n")

    def _save_axis(self, axis):
        gaxis = _moveformatspecific(axis)
        _copyattrs(axis, gaxis, ["name", "tag"])
        return gaxis

    def _save_kerning(self, kerntable):
        newtable = {}
        for (l,r), val in kerntable.items():
            newtable.setdefault(l,{})[r] = val
        return newtable

    def _save_master(self, master):
        gmaster = _moveformatspecific(master)
        gmaster["axesValues"] = list(master.location.values())
        gmaster["metricValues"] = []
        for k in self.metrics_order:
            metric = {}
            pos = master.metrics.get(_glyphs_metrics_to_ours(k))
            over = master.metrics.get(_glyphs_metrics_to_ours(k) + " overshoot")
            if pos:
                metric["pos"] = pos
            if over:
                metric["over"] = over
            gmaster["metricValues"].append(metric)
        if master.guides:
            gmaster["guides"] = [self._save_guide(g) for g in master.guides]
        _copyattrs(master, gmaster, ["name", "id"], convertor=str)
        return gmaster

    def _save_guide(self, guide):
        gguide = _moveformatspecific(guide)
        gguide["pos"] = tuple(guide.pos[0:2])
        if guide.pos[2]:
            gguide["angle"] = guide.pos[2]
        return gguide

    def _save_glyph(self, glyph):
        gglyph = _moveformatspecific(glyph)
        gglyph["glyphname"] = glyph.name
        if len(glyph.codepoints) == 1:
            if glyph.codepoints[0] < 256:
                gglyph["unicode"] = glyph.codepoints[0]
            else:
                gglyph["unicode"] = "%04x" % glyph.codepoints[0]
        elif len(glyph.codepoints) > 1:
            gglyph["unicode"] = glyph.codepoints
        gglyph["layers"] = [self._save_layer(l) for l in glyph.layers]
        if glyph.production_name != glyph.name:
            gglyph["production"] = glyph.production_name
        if not glyph.exported:
            gglyph["export"] = 0
        return gglyph

    def _save_layer(self, layer):
        glayer = _moveformatspecific(layer)
        _copyattrs(layer, glayer, ["width", "name"])
        glayer["layerId"] = str(layer.id)
        if layer.guides:
            glayer["guides"] = [self._save_guide(g) for g in layer.guides]
        if layer.shapes:
            glayer["shapes"] = [self._save_shape(s) for s in layer.shapes]
        if layer._master and layer._master != layer.id:
            glayer["associatedMasterId"] = layer._master
        return glayer

    def _save_shape(self, shape):
        gshape = _moveformatspecific(shape)
        if shape.is_path:
            gshape["closed"] = shape.closed
            gshape["nodes"] = [self._save_node(n) for n in shape.nodes]
        else:
            _copyattrs(shape, gshape, ["ref", "angle"])
            if shape.pos != (0,0):
                _copyattrs(shape, gshape, ["pos"])
            if shape.scale != (1,1):
                _copyattrs(shape, gshape, ["scale"])
        return gshape

    def _save_node(self, node):
        return (node.x, node.y, node.type)


class GlyphsPackage(GlyphsThree):
    suffix = ".glyphspackage"

    @classmethod
    def can_save(cls, convertor, **kwargs):
        return False

    @classmethod
    def can_load(self, other, **kwargs):
        return other.filename.endswith(self.suffix)

    def _load(self):
        infofile = os.path.join(self.filename, "fontinfo.plist")
        orderfile = os.path.join(self.filename, "order.plist")
        glyphorder = openstep_plist.load(open(orderfile, "r"))
        self.scratch["plist"] = openstep_plist.load(
            open(infofile, "r"), use_numbers=True
        )
        self.scratch["plist"]["glyphs"] = []
        for g in glyphorder:
            glyphname = userNameToFileName(g) + ".glyph"
            glyphfile = os.path.join(self.filename, "glyphs", glyphname)
            self.scratch["plist"]["glyphs"].append(
                openstep_plist.load(open(glyphfile, "r"), use_numbers=True)
            )

        return super()._load()


def _maybesetformatspecific(item, glyphs, key):
    if glyphs.get(key):
        if "com.glyphsapp" not in item._formatspecific:
            item._formatspecific["com.glyphsapp"] = {}
        item._formatspecific["com.glyphsapp"][key] = glyphs.get(key)


def _moveformatspecific(item):
    rv = {}
    if "com.glyphsapp" in item._formatspecific:
        rv = {**item._formatspecific.get("com.glyphsapp", {})}
    return rv


def _copyattrs(src, dst, attrs, convertor = lambda x:x):
    for a in attrs:
        v = getattr(src, a)
        if isinstance(v, I18NDictionary):
            v = v.get_default()
        if v:
            dst[a] = convertor(v)
