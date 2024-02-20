from datetime import datetime
from babelfont import *
from fontTools.misc.transform import Transform
from babelfont.convertors import BaseConvertor
from pathlib import Path
from lxml import etree
from fontFeatures import FontFeatures
import orjson
import os


# One would hope this would be easy.


class Babelfont(BaseConvertor):
    suffix = ".babelfont"

    def _load_file(self, filename):
        contents = open(os.path.join(self.filename, filename), "r").read()
        return orjson.loads(contents)

    def _load(self):
        names = self._load_file("names.json")
        info = self._load_file("info.json")
        glyphs = self._load_file("glyphs.json")
        self.font._formatspecific = info["_"]
        for k, v in names.items():
            if k in self.font.names.__dataclass_fields__:
                getattr(self.font.names, k).copy_in(v)
            elif k == "_":
                self.font.names._formatspecific = v

        self.font.axes = [Axis(**j) for j in info.get("axes", [])]
        self.font.instances = [Instance(**j) for j in info.get("instances", [])]

        self._load_masters(info.get("masters", []))

        for g in glyphs:
            glyph = Glyph(**g)
            self.font.glyphs.append(glyph)
            for json_layer in self._load_file(glyph.babelfont_filename):
                layer = self._inflate_layer(json_layer)
                glyph.layers.append(layer)

        self._load_metadata(info)
        self._load_features()
        return self.font

    def _load_masters(self, masters):
        for json_master in masters:
            if "kerning" in json_master:
                json_master["kerning"] = {
                    tuple(k.split("//")): v for k, v in json_master["kerning"].items()
                }
            master = Master(**json_master)
            master.font = self.font
            master.guides = [Guide(**m) for m in master.guides]
            self.font.masters.append(master)

    def _inflate_layer(self, json_layer):
        layer = Layer(**json_layer)
        layer.guides = [Guide(**m) for m in layer.guides]
        layer.anchors = [Anchor(**m) for m in layer.anchors]
        layer._font = self.font
        layer.shapes = [self._inflate_shape(layer, s) for s in layer.shapes]
        return layer

    def _inflate_shape(self, layer, s):
        shape = Shape(**s)
        if shape.nodes:
            shape.nodes = [self._inflate_node(n) for n in shape.nodes]
        return shape

    def _inflate_node(self, n):
        return Node(*n)

    def _load_metadata(self, info):
        for k in ["note", "upm", "version", "date", "customOpenTypeValues"]:
            if k in info:
                setattr(self.font, k, info[k])
        self.font.date = datetime.strptime(self.font.date, "%Y-%m-%d %H:%M:%S")

    def _load_features(self):
        path = os.path.join(self.filename, "features.xml")
        if os.path.isfile(path):
            f = open(path, "r")
            xml = etree.parse(f)
            self.font.features = FontFeatures.fromXML(xml.getroot())

    def _save(self):
        path = Path(self.filename)
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "info.json", "wb") as f:
            self.font.write(stream=f)

        with open(path / "names.json", "wb") as f:
            self.font._write_value(f, "glyphs", self.font.names)

        with open(path / "features.xml", "wb") as f:
            f.write(etree.tostring(self.font.features.toXML(), pretty_print=True))

        with open(path / "glyphs.json", "wb") as f:
            for g in self.font.glyphs:
                glyphpath = path / "glyphs"
                glyphpath.mkdir(parents=True, exist_ok=True)
                with open(path / g.babelfont_filename, "wb") as f2:
                    g._write_value(f2, "layers", g.layers)
            self.font._write_value(f, "glyphs", self.font.glyphs)
