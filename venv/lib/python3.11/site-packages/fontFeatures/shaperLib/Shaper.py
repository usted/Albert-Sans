"""A Python Unicode Shaping Engine."""

from fontFeatures import FontFeatures
import unicodedata
from fontFeatures.shaperLib import Buffer
from .BaseShaper import BaseShaper
from .ArabicShaper import ArabicShaper
from .IndicShaper import IndicShaper
from .MyanmarShaper import MyanmarShaper
from .HangulShaper import HangulShaper
from .KhmerShaper import KhmerShaper
from .USEShaper import USEShaper
import logging
import re


class Shaper:
    """Initialize a shaping engine.

    Args:
        ff: A :py:class:`fontFeatures.FontFeatures` object.
        font: A ``Babelfont`` font object.
        message_function: A function called with a message and buffer object.
    """
    def __init__(self, ff, font, message_function=None):
        assert isinstance(ff, FontFeatures)
        self.fontfeatures = ff
        self.babelfont = font
        if message_function:
            self.msg = message_function
        else:
            self.msg = self.default_message_function

    def execute(self, buf, features=[]):
        """Run the shaper on a given buffer.

        Args:
            buf: :py:class:`fontFeatures.shaperLib.buffer.Buffer` object.
            features: either a list of feature tags or a feature string ("+foox,-barx")
        """
        # Choose complex shaper
        self.complexshaper = self.categorize(buf)(self, self.babelfont, buf, features)
        self.msg("Using %s" % type(self.complexshaper).__name__)
        self.stages = [[]]
        if isinstance(features, str):
            self.user_features = self._parse_user_feature_string(features)
        else:
            self.user_features = features
        self.collect_features(buf)
        self.complexshaper.shape()
        buf.clear_mask()
        return buf

    def default_message_function(self, msg, buffer=None, serialize_options=None):
        """A logger function to be used if one is not provided in the constructor.

        By default, debugging and informational log messages are reported to the
        ``fontFeatures.shaperLib`` facility."""
        ser = ""
        if buffer:
            ser = buffer.serialize(additional=serialize_options)
            msg = msg + " : " + ser
        logging.getLogger("fontFeatures.shaperLib").info(msg)

    def _parse_user_feature_string(self, features):
        features = features.split(",")
        outfeat = []
        for f in features:
            f = f.rstrip()
            m = re.match(r"^([+\-]?)(\w+)", f)
            if m:
                outfeat.append({"tag": m[2], "value": m[1] != "-"})
                continue
            m = re.match(r"^(\w+)=([10])", f)
            if m:
                outfeat.append({"tag": m[1], "value": m[2] == "1"})
            else:
                outfeat.append({"tag": f, "value": True})
        return outfeat

    def add_pause(self, thing = None):
        """Add a pause in the shaping stage. Used internally."""
        if thing:
            self.stages.append(thing)
        self.stages.append([])

    def add_features(self, *tags):
        """Adds feature tags to the current shaping stage."""
        for t in tags:
            if any([isinstance(x, list) and t in x for x in self.stages]):
                continue
            self.stages[-1].append(t)

    def disable_feature(self, tag):
        """Removes a feature from processing."""
        for s in self.stages:
            if isinstance(s, list) and tag in s:
                s.remove(tag)

    def collect_features(self, buf):
        """Determine the features, and their order, to process the buffer."""
        self.add_features("rvrn")
        self.add_pause()
        if buf.direction == "LTR":
            self.add_features("ltra", "ltrm")
        elif buf.direction == "RTL":
            self.add_features("rtla", "rtlm")
        self.add_features("frac", "numr", "dnom", "rand")
        # trak?
        self.complexshaper.collect_features(self)
        # common features
        self.add_features("abvm", "blwm", "ccmp", "locl", "mark", "mkmk", "rlig")
        if buf.direction == "LTR" or buf.direction == "RTL":
            self.add_features("calt", "clig", "curs", "dist", "kern", "liga", "rclt")
        else:
            self.add_features("vert")
        for uf in self.user_features:
            if not uf["value"]:  # Turn it off if it's already on
                self.disable_feature(uf["tag"])
            else:
                self.add_features(uf["tag"])
        if hasattr(self.complexshaper, "override_features"):
            self.complexshaper.override_features(self)

    def categorize(self, buf):
        """Returns the appropriate complex shaper class to shape this buffer."""
        if buf.script == "Arabic":
            return ArabicShaper

        connected_scripts = {
            "Mongolian": "mong",
            "Syriac": "syrc",
            "Nko": "nko ",
            "Phags_Pa": "phag",
            "Mandaic": "mand",
            "Manichaean": "mand",
            "Psalter_Pahlavi": "phlp",
            "Adlam": "adlm",
            "Hanifi_Rohingya": "rohg",
            "Sogdian": "sogd"
        }
        if buf.script in connected_scripts:
            if self.fontfeatures.hasScriptSupport(connected_scripts[buf.script]):
                return ArabicShaper
            else:
                return BaseShaper

        if buf.script in ["Thai", "Lao"]:
            return ThaiShaper
        if buf.script == "Hangul":
            return HangulShaper
        if buf.script == "Hebrew":
            return HebrewShaper
        if buf.script in [
            "Bengali",
            "Devanagari",
            "Gujarati",
            "Gurmukhi",
            "Kannada",
            "Malayalam",
            "Oriya",
            "Tamil",
            "Telugu",
            "Sinhala",
        ]:
            indic23map = {
                "Bengali": "bng",
                "Devanagari": "dev",
                "Gujarati": "gjr",
                "Gurmukhi": "gur",
                "Kannada": "knd",
                "Malayalam": "mlm",
                "Oriya": "ory",
                "Tamil": "tml",
                "Telugu": "tel",
            }
            # Sinhala is different
            if buf.script in indic23map and self.fontfeatures.hasScriptSupport(indic23map[buf.script] + "3"):
                return USEShaper
            else:
                return IndicShaper
        if buf.script == "Khmer":
            return KhmerShaper

        if buf.script == "Myanmar":
            if self.fontfeatures.hasScriptSupport("mymr"):
                return BaseShaper
            else:
                return MyanmarShaper

        # if buf.script = "Qaag": return MyanmarZawgyiShaper
        if buf.script in [
            "Tibetan",
            "Buhid",
            "Hanunoo",
            "Tagalog",
            "Tagbanwa",
            "Limbu",
            "Tai_Le",
            "Buginese",
            "Kharoshthi",
            "Syloti_Nagri",
            "Tifinagh",
            "Balinese",
            "Cham",
            "Kayah_Li",
            "Lepcha",
            "Rejang",
            "Saurashtra",
            "Sundanese",
            "Egyptian_Hieroglyphs",
            "Javanese",
            "Kaithi",
            "Meetei_Mayek",
            "Tai_Tham",
            "Tai_Viet",
            "Batak",
            "Brahmi",
            "Chakma",
            "Sharada",
            "Takri",
            "Duployan",
            "Grantha",
            "Khojki",
            "Khudawadi",
            "Mahajani",
            "Modi",
            "Pahawh_Hmong",
            "Siddham",
            "Tirhuta",
            "Ahom",
            "Bhaiksuki",
            "Marchen",
            "Newa",
            "Masaram_Gondi",
            "Soyombo",
            "Zanabazar_Square",
            "Dogra",
            "Gunjala_Gondi",
            "Makasar",
            "Nandinagari",
        ]:
            return USEShaper
        return BaseShaper

def _script_direction(script):
    if script in [
        "Arabic",
        "Hebrew",
        "Syriac",
        "Thaana",
        "Cypriot",
        "Kharoshthi",
        "Phoenician",
        "Nko",
        "Lydian",
        "Avestan",
        "Imperial_Aramaic",
        "Inscriptional_Parthian",
        "Inscriptional_Pahlavi",
        "Old_South_Arabian",
        "Old_Turkic",
        "Samaritan",
        "Mandaic",
        "Meroitic_Cursive",
        "Meroitic_Hieroglyphs",
        "Manichaean",
        "Mende_Kikakui",
        "Nabataean",
        "Old_North_Arabian",
        "Palmyrene",
        "Psalter_Pahlavi",
        "Hatran",
        "Adlam",
        "Hanifi_Rohingya",
        "Old_Sogdian",
        "Sogdian",
        "Elymaic",
        "Chorasmian",
        "Yezidi"]:
        return "RTL"
    if script in ["Old_Hungarian", "Old_Italic", "Runic"]:
        return "invalid"
    return "LTR"
