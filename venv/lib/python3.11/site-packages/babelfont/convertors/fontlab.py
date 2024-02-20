from datetime import datetime
from babelfont import *
import orjson
from fontTools.misc.transform import Transform
from babelfont.convertors import BaseConvertor
import uuid
import re


class Fontlab(BaseConvertor):
    suffix = ".vfj"

    def _load(self):
        self.fontlab = orjson.loads(open(self.filename).read())["font"]
        self.known_transforms = {}
        self._load_axes()
        self._load_masters()
        if "defaultMaster" in self.fontlab:
            default = self.font.master(self.fontlab["defaultMaster"])
            if self.font.axes:
                def_loc = self.font.map_backward(default.location)
                for axis in self.font.axes:
                    if axis.tag in default.location:
                        axis.default = def_loc[axis.tag]
            assert self.font.default_master
        for g in self.fontlab.get("glyphs", []):
            glyph = self._load_thing(g, self.glyph_loader)
            self.font.glyphs.append(glyph)
        self.font.upm = self.fontlab.get("upm", 1000)
        return self.font

    axis_loader = (
        Axis,
        {
            "name": "name",
            "tag": "tag",
            "minimum": "min",
            "maximum": "max",
            "default": "default",
            "axisGraph": ("map", lambda _, x: [(v, int(k)) for k, v in x.items()]),
        },
    )

    def _load_kerning(self, flkerning):
        for kclass in flkerning.get("kerningClasses", []):
            self.font.features.namedClasses[kclass["name"]] = kclass["names"]
        kerning = {}
        for left, rvalue in flkerning.get("pairs", {}).items():
            for right, value in rvalue.items():
                kerning[(left, right)] = int(value)
        return kerning

    def _convert_color(_, col):
        r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
        return Color(r, g, b, 0)

    def _convert_shapes(self, flshapes):
        shapes = []
        for shape in flshapes:
            transform_j = shape.get("transform", {})
            if "id" in transform_j:
                self.known_transforms[transform_j["id"]] = transform_j
            if isinstance(transform_j, str):
                transform_j = self.known_transforms[transform_j]
            transform = Transform().translate(
                            transform_j.get("xOffset", 0),
                            transform_j.get("yOffset", 0),
                        )
            if "component" in shape:
                shapes.append(
                    Shape(
                        ref=shape["component"]["glyphName"],
                        transform=transform,
                        _=shape["component"],
                    )
                )
            else:
                for flcontour in shape["elementData"].get("contours",[]):
                    contour = Shape(nodes=[])
                    for n in flcontour["nodes"]:
                        contour.nodes.extend(self._load_node(n))
                    shapes.append(contour)
        return shapes

    def _load_node(self, input_):
        stuff = input_.split("  ")
        rv = []
        for ix, node in enumerate(stuff):
            m = re.match(r"(-?[\d\.]+) (-?[\d\.]+)( s)?", node)
            if not m:
                raise ValueError("Can't understand nodestring %s" % node)
            if len(stuff) == 1:
                ntyp = "l"
            elif len(stuff) == 3 and ix == 2:
                ntyp = "c"
                if m[3]:
                    ntyp = ntyp + "s"
            elif len(stuff) == 2 and ix == 1:
                ntyp = "q"
                if m[3]:
                    ntyp = ntyp + "s"
            else:
                ntyp = "o"
            rv.append(Node(x=float(m[1]), y=float(m[2]), type=ntyp))
        return rv

    master_loader = (
        Master,
        {
            "name": ["id", "name"],
            "kerning": ("kerning", _load_kerning),
            "location": (
                "location",
                lambda s, x: {s.axis_name_map[k].tag: v for k, v in x.items()},
            ),
        },
    )

    _layer_loader = (
        Layer,
        {
            "advanceWidth": "width",
            "name": ["name", "_master"],
            "color": ("color", _convert_color),
            "elements": ("shapes", _convert_shapes),
        },
    )

    glyph_loader = (
        Glyph,
        {
            "name": "name",
            "unicode": (
                "codepoints",
                lambda _, x: [int(cp, 16) for cp in x.split(",")],
            ),
            "layers": ("layers", _layer_loader),
            "elements": None,
        },
    )

    def _load_thing(self, thing, handler):
        kwargs = {}
        kwargs["_"] = {}
        cls, mapping = handler
        for k, v in thing.items():
            if k not in mapping:
                kwargs["_"][k] = v
            elif mapping[k] is None:
                continue
            elif isinstance(mapping[k], list):
                for newname in mapping[k]:
                    kwargs[newname] = v
            elif isinstance(mapping[k], str):
                kwargs[mapping[k]] = v
            elif isinstance(mapping[k], tuple) and callable(mapping[k][1]):
                newName, convertor = mapping[k]
                kwargs[newName] = convertor(self, v)
            else:
                newName, convertor = mapping[k]
                if isinstance(v, list):
                    kwargs[newName] = [self._load_thing(v1, convertor) for v1 in v]
                else:
                    kwargs[newName] = self._load_thing(v, convertor)
        obj = cls(**kwargs)
        obj._font = self.font
        return obj

    def _load_axes(self):
        self.axis_name_map = {}
        for ax in self.fontlab.get("axes", []):
            axis = self._load_thing(ax, self.axis_loader)
            self.axis_name_map[ax["shortName"]] = axis
            self.font.axes.append(axis)

    def _load_masters(self):
        for m in self.fontlab.get("masters", []):
            fl_master = m["fontMaster"]
            metric_dict = {}
            for metric in [
                "ascender",
                "descender",
                "xHeight",
                "capsHeight",
                "measurement",
                "underlineThickness",
                "underlinePosition",
            ]:
                if metric not in fl_master:
                    continue
                value = fl_master[metric]
                del fl_master[metric]
                if metric == "capsHeight":
                    metric = "capHeight"
                metric_dict[metric] = value
            master = self._load_thing(fl_master, self.master_loader)
            master.metrics = metric_dict
            master.font = self.font
            self.font.masters.append(master)
