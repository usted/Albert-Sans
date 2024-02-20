from datetime import datetime
from babelfont import *
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen
from cu2qu.ufo import glyphs_to_quadratic
from fontTools.misc.timeTools import epoch_diff, timestampSinceEpoch
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from babelfont.fontFilters.featureWriters import build_all_features
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib.iup import iup_delta_optimize
from fontTools.misc.fixedTools import otRound
import uuid
from itertools import chain


def _categorize_glyph(font,glyphname):
    if "GDEF" not in font: return None
    classdefs = font["GDEF"].table.GlyphClassDef.classDefs
    if glyphname not in classdefs:
        return None
    if classdefs[glyphname] == 1: return "base"
    if classdefs[glyphname] == 2: return "ligature"
    if classdefs[glyphname] == 3: return "mark"
    if classdefs[glyphname] == 4: return "component"

class TrueType(BaseConvertor):
    suffix = ".ttf"

    def _decompose_mixed_layer(self, layer, exportable):
        if (layer.paths and layer.components) or any(
            c.ref not in exportable for c in layer.components
        ):
            layer.decompose()

    def _load(self):
        self.tt = TTFont(self.filename)
        self._load_fvar()
        self._load_head()
        self._load_masters()
        self._load_names()
        self._load_glyphs()
        return self.font

    def _load_fvar(self):
        avar = self.tt.get("avar")
        if "fvar" in self.tt:
            for axis in self.tt["fvar"].axes:
                name = self.tt["name"].getDebugName(axis.axisNameID)  # XXX multilingual
                bb_axis = Axis(
                    tag=axis.axisTag,
                    min=axis.minValue,
                    max=axis.maxValue,
                    default=axis.defaultValue,
                    name=name,
                )
                self.font.axes.append(bb_axis)
                if avar:
                    segs = avar.segments[axis.axisTag]
                    mapping = {
                        bb_axis.denormalize_value(k): bb_axis.denormalize_value(v)
                        for k, v in segs.items()
                    }
                    bb_axis.map = mapping
            for instance in self.tt["fvar"].instances:
                self.font.instances.append(
                    Instance(
                        name=self.tt["name"].getDebugName(instance.subfamilyNameID),
                        location=instance.coordinates,
                    )
                )

    def _load_masters(self):
        m = Master(location={},name="Default", id=str(uuid.uuid1()) )
        # Metrics
        m.metrics = {
            "xHeight": self.tt["OS/2"].sxHeight,
            "capHeight": self.tt["OS/2"].sCapHeight,
            "ascender": self.tt["hhea"].ascender,
            "descender": self.tt["hhea"].descender
        }
        m.font = self.font
        self.font.masters = [m]
        if "fvar" in self.tt:
            m.location = {axis.tag: axis.default for axis in self.font.axes}
            all_masters = [frozenset(x.axes.items()) for x in chain(*self.tt["gvar"].variations.values())]
            all_masters = [{k:v[1] for k,v in dict(m1).items()} for m1 in all_masters]
            # Now denormalize.
            # XXX
            pass

    def _load_head(self):
        head = self.tt["head"]
        self.font.upm = head.unitsPerEm
        minor = head.fontRevision % 1
        while minor - int(minor) > 1e-4:
            minor *= 10
        self.font.version = (int(head.fontRevision), int(minor))
        self.font.date = datetime.fromtimestamp(self.tt["head"].created + epoch_diff)

    def _load_names(self):
        names = self.tt["name"]
        # XXX

    def _load_glyphs(self):
        mapping = self.tt["cmap"].buildReversed()
        glyphs_dict = {}
        for glyph in self.tt.getGlyphOrder():
            category = _categorize_glyph(self.tt, glyph) or "base"
            glyphs_dict[glyph] = Glyph(name=glyph, codepoints=list(mapping.get(glyph, [])), category=category)
            self.font.glyphs.append(glyphs_dict[glyph])
            glyphs_dict[glyph].layers = self._load_layers(glyph)
        return glyphs_dict

    def _load_layers(self, g):
        ttglyph = self.tt.getGlyphSet()[g]  # _TTGlyphGlyf object
        width = self.tt["hmtx"][g][0]
        # leftMargin = self.tt["hmtx"][g][1]
        layer = Layer(width=width, id=str(uuid.uuid1()) )
        layer._master = self.font.masters[0].id
        layer._font = self.font
        ttglyph.draw(layer.getPen())
        return [layer]


    def _load_contour(self, ttglyph, index):
        shape = Shape()
        shape.nodes = []
        endPt = ttglyph.endPtsOfContours[index]
        if index > 0:
            startPt = ttglyph.endPtsOfContours[index - 1] + 1
        else:
            startPt = 0
        points = []
        for j in range(startPt, endPt + 1):
            coords = (ttglyph.coordinates[j][0], ttglyph.coordinates[j][1])
            flags = ttglyph.flags[j] == 1
            t = "o"
            if flags == 1:
                if (j == startPt and ttglyph.flags[endPt] == 1) or (
                    j != startPt and points[-1].type != "o"
                ):
                    t = "l"
                else:
                    t = "q"
            else:
                if len(points) > 1 and points[-1].type == "o":
                    # Double offcurve. Insert implicit oncurve.
                    prevpoint = points[-1]
                    intermediate = Node(
                        x = (coords[0] + prevpoint.x) / 2,
                        y = (coords[1] + prevpoint.y) / 2,
                        type = "q"
                    )
                    points.append(intermediate)
            p = Node(x = coords[0], y=coords[1], type=t)
            points.append(p)
        shape.nodes = points
        return shape

    def _load_component(self, c):
        baseGlyph, transformation = c.getComponentInfo()
        component = Shape(ref=baseGlyph, transform=transformation)
        return component

    def _save(self):
        f = self.font
        fb = FontBuilder(f.upm, isTTF=True)

        metrics = {}
        all_outlines = {}

        # Find all exportable glyphs
        exportable = [k for k, v in f.glyphs.items() if v.exported]

        fb.setupGlyphOrder(exportable)
        fb.setupCharacterMap(
            {k: v for k, v in f.unicode_map.items() if v in exportable}
        )

        for g in exportable:
            all_outlines[g] = []
            layer = f.default_master.get_glyph_layer(g)
            metrics[g] = (layer.width, layer.lsb)

        fb.setupHorizontalMetrics(metrics)

        for m in f.masters:
            glyf = {}
            m.ttglyphset = {}

        done = {}

        def do_a_glyph(g):
            if g in done:
                return
            layer = f.default_master.get_glyph_layer(g)
            self._decompose_mixed_layer(layer, exportable)
            for c in layer.components:
                do_a_glyph(c.ref)

            for m in f.masters:
                layer = m.get_glyph_layer(g)
                self._decompose_mixed_layer(layer, exportable)
                all_outlines[g].append(layer)
            try:
                glyphs_to_quadratic(all_outlines[g], reverse_direction=True)
                for ix, m in enumerate(f.masters):
                    layer = m.get_glyph_layer(g)
                    pen = TTGlyphPen(m.ttglyphset)
                    layer.draw(pen)

                    m.ttglyphset[g] = pen.glyph()

            except Exception as e:
                print(
                    "Problem converting glyph %s to quadratic. (Probably incompatible) "
                    % g
                )
                for m in f.masters:
                    m.ttglyphset[g] = TTGlyphPen(m.ttglyphset).glyph()
            done[g] = True

        for g in exportable:
            do_a_glyph(g)

        fb.updateHead(
            fontRevision=f.version[0] + f.version[1] / 10 ** len(str(f.version[1])),
            created=timestampSinceEpoch(f.date.timestamp()),
            lowestRecPPEM=10,
        )
        fb.setupGlyf(f.default_master.ttglyphset)
        fb.setupHorizontalHeader(
            ascent=int(f.default_master.ascender),
            descent=int(f.default_master.descender),
        )

        f.names.typographicSubfamily = f.default_master.name
        f.names.typographicFamily = f.names.familyName
        fb.setupNameTable(f.names.as_nametable_dict())

        fb.setupOS2(
            sTypoAscender=int(f.default_master.ascender),
            sTypoDescender=int(f.default_master.descender),
            sCapHeight=int(f.default_master.capHeight),
            sxHeight=int(f.default_master.xHeight),
        )

        if f.axes:
            model = f.variation_model()
            axis_map = {}
            variations = {}
            for g in exportable:
                variations[g] = self.calculate_a_gvar(f, model, g, metrics[g][0])

            for ax in f.axes:
                ax.name = ax.name.as_fonttools_dict
                axis_map[ax.tag] = ax
            for instance in f.instances:
                instance.location = {
                    k: axis_map[k].map_backward(v) for k, v in instance.location.items()
                }
            fb.setupFvar(f.axes, f.instances)

            fb.setupGvar(variations)
            fb.setupAvar(f.axes)
        # Move glyph categories to fontfeatures
        for g in f.glyphs.values():
            if g.exported:
                f.features.glyphclasses[g.name] = g.category

        build_all_features(f, fb.font)
        fb.setupPost()

        for table, field, value in f.customOpenTypeValues:
            setattr(fb.font[table], field, value)

        fb.font.save(self.filename)

        # Rename to production
        rename_map = {g.name: g.production_name or g.name for g in f.glyphs}
        if rename_map:
            font = TTFont(self.filename)
            font.setGlyphOrder([rename_map.get(n, n) for n in font.getGlyphOrder()])
            if "post" in font and font["post"].formatType == 2.0:
                font["post"].extraNames = []
                font["post"].compile(font)
            font.save(self.filename)

    def calculate_a_gvar(self, f, model, g, default_width):
        master_layer = f.default_master.get_glyph_layer(g)
        if not g in f.default_master.ttglyphset:
            return None
        default_g = f.default_master.ttglyphset[g]
        all_coords = []
        for m in f.masters:
            layer = m.get_glyph_layer(g)
            basecoords = GlyphCoordinates(m.ttglyphset[g].coordinates)
            if m.ttglyphset[g].isComposite():
                component_point = GlyphCoordinates(
                    [
                        (otRound(layer_comp.pos[0]), otRound(layer_comp.pos[1]))
                        for layer_comp in layer.components
                    ]
                )
                basecoords.extend(component_point)
            phantomcoords = GlyphCoordinates([(0, 0), (otRound(layer.width), 0), (0, 0), (0, 0)])
            basecoords.extend(phantomcoords)
            all_coords.append(basecoords)
        for ix,c in enumerate(all_coords):
            all_ok = True
            if len(c) != len(all_coords[0]):
                print("Incompatible master %i in glyph %s" % (ix, g))
                all_ok = False
            if not all_ok:
                return []
        deltas = model.getDeltas(all_coords)
        gvar_entry = []
        if default_g.isComposite():
            endPts = list(range(len(default_g.components)))
        else:
            endPts = default_g.endPtsOfContours

        for delta, sup in zip(deltas, model.supports):
            if not sup:
                continue
            var = TupleVariation(sup, round(delta))
            # This assumes we do the default master first, which may not be true
            delta_opt = iup_delta_optimize(round(delta), round(deltas[0]), endPts, tolerance=0.5)
            if None in delta_opt:
                var = TupleVariation(sup, delta_opt)
            gvar_entry.append(var)
        return gvar_entry

    # import numpy as np
    # def calculate_a_gvar(self, f, model, g, default_width):
    #     if not g in f.default_master.ttglyphset._glyphs:
    #         return None

    #     all_coords = []
    #     master_ix = f.masters.index(f.default_master)

    #     for m in f.masters:
    #         coords = list(m.ttglyphset._glyphs[g].coordinates)
    #         layer = m.get_glyph_layer(g)
    #         if m.ttglyphset._glyphs[g].isComposite():
    #             coords.extend([c.pos for c in layer.components])
    #         coords.extend( [ (0,0), (layer.width,0), (0,0), (0,0) ] )
    #         all_coords.append(np.array(coords))
    #     stacked = np.array(all_coords)
    #     defaults = stacked[np.newaxis,master_ix,:,:].repeat(len(f.masters),axis=0)
    #     base_deltas = stacked-defaults
    #     x_deltas = np.apply_along_axis(model.getDeltas, 1, base_deltas[:,:,0].transpose())
    #     y_deltas = np.apply_along_axis(model.getDeltas, 1, base_deltas[:,:,1].transpose())
    #     alldeltas = np.array([x_deltas, y_deltas]).transpose()
    #     gvar_entry = []
    #     for deltaset, sup in zip(alldeltas, model.supports):
    #         gvar_entry.append(TupleVariation(sup, list(map(tuple, deltaset))))
    #     return gvar_entry

class OpenType(TrueType):
    suffix = ".otf"

    def _load_layers(self, g):
        ttglyph = self.tt.getGlyphSet()[g]
        width = self.tt["hmtx"][g][0]
        layer = Layer(width=width, id=str(uuid.uuid1()) )
        layer._master = self.font.masters[0].id
        layer._font = self.font
        pen = RecordingPen()
        ttglyph.draw(pen)
        contours = pen.value
        lastcontour = []
        startPt = (0,0)
        lastPt = (0,0)
        index = 0
        for operation, segment in contours:
            if operation == "moveTo":
                startPt = segment[0]
            elif operation == "closePath":
                if startPt != lastPt:
                    lastcontour.append(Node(x=startPt[0], y=startPt[1],type = "l"))
                contour = Shape()
                contour.nodes = lastcontour
                layer.shapes.append(contour)
                lastcontour = []
            elif operation == "curveTo":
                lastcontour.append(Node(x=segment[0][0],y=segment[0][1],type = "o"))
                lastcontour.append(Node(x=segment[1][0],y=segment[1][1],type = "o"))
                lastcontour.append(Node(x=segment[2][0],y=segment[2][1],type = "c"))
                lastPt = segment[2]
            elif operation == "lineTo":
                lastcontour.append(Node(x=segment[0][0],y=segment[0][1],type = "l"))
                lastPt = segment[0]
            elif operation == "qCurveTo":
                lastcontour.append(Node(x=segment[0][0],y=segment[0][1],type = "o"))
                lastcontour.append(Node(x=segment[1][0],y=segment[1][1],type = "q"))

        return [layer]
