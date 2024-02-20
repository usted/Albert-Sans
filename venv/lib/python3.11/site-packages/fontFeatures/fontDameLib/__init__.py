import re
from fontFeatures import *
from fontFeatures.optimizer import Optimizer
from fontTools.ttLib import TTFont
from collections import OrderedDict
from fontTools.feaLib.ast import ValueRecord
import warnings


class FontDameParser:
    """Convert layout files in Monotype's FontDame format to fontFeatures.

    Args:
        lines: An array of strings containing the FontDame file, one line per string.
        config: A dictionary of glyph class names.
        glyphset: A list of glyph names in the font.
    """
    def __init__(self, lines, config={}, glyphset=()):
        self.all_languages = []
        self.lines = lines
        self.script_applications = {}
        self.features = {}
        self.lookups = OrderedDict()
        self.dependencies = {}
        self.classes = []
        self.config = config
        self.glyphset = glyphset
        self.current_lookup = None
        self.state = "doing_nothing"
        self.ff = FontFeatures()
        self.resetContexts()

    def resetContexts(self):
        self.classContexts = {}
        self.backtrackclassContexts = {}
        self.lookaheadclassContexts = {}

    def parse(self):
        """Parses the font file, creating a fontFeatures object.

        Returns: A fontFeatures object containing the rules in the FontDame file."""
        # Parse lookups
        for line in self.lines:
            self.parse_line(line)

        # Tidy up lookups
        for lid, lu in self.lookups.items():
            for rule in lu.rules:
                if not isinstance(rule, Chaining):
                    continue
                pretendlookups = rule.lookups
                reallookups = [None] * len(rule.input)
                for i in pretendlookups:
                    m = re.match("\\s*(\\S+),\\s*(\\S+)", i)
                    if not m:
                        raise ValueError("Unparsable lookup chain %s" % i)
                    if not lid in self.dependencies:
                        self.dependencies[lid] = []
                    self.dependencies[lid].append(m[2])
                    if not reallookups[int(m[1]) - 1]:
                        reallookups[int(m[1]) - 1] = []
                    reallookups[int(m[1]) - 1].append(self.lookups[m[2]])
                rule.lookups = reallookups

        # Tie features to languages
        for k, v in self.features.items():
            v["languages_and_scripts"] = self.script_applications[int(k)]

        # Rearrange into features
        self.base_lu_for_feature = {}
        self.toplevel_lookups = set()
        for i in sorted(self.features.keys()):
            feat = self.features[i]
            tag = feat["tag"]
            if "DFLT/default" in feat["languages_and_scripts"]:
                self.base_lu_for_feature[tag] = set(feat["lookups"])
                lookups = [self.lookups[x] for x in feat["lookups"]]
            else:
                # Set difference
                if tag in self.base_lu_for_feature:
                    feat["lookups"] = [
                        item
                        for item in feat["lookups"]
                        if item not in self.base_lu_for_feature[tag]
                    ]
                lookups = [self.lookups[x] for x in feat["lookups"]]
                langcode = [
                    self.format_langcode(x.split("/"))
                    for x in feat["languages_and_scripts"]
                ]
                # Clone the routines just in case
                lookups = [
                    Routine(languages=langcode, rules=lu.rules, flags=lu.flags)
                    for lu in lookups
                ]

            self.ff.addFeature(tag, lookups)
            for lu in feat["lookups"]:
                self.toplevel_lookups.add(lu)

        # Delete toplevel lookups from lookup table
        for l in self.toplevel_lookups:
            del self.lookups[l]

        # Rearrange lookups into dependency order
        done = {}

        def dolookup(lid):
            if lid in done:
                return
            if lid in self.dependencies:
                for x in self.dependencies[lid]:
                    dolookup(x)
            self.ff.routines.append(self.lookups[lid])
            done[lid] = True

        for i in self.lookups.keys():
            dolookup(i)
        return self.ff

    def format_langcode(self, code):
        script, lang = code
        if lang == "default":
            return (script, "dflt")
        return (script, lang)

    def parse_line(self, line):
        if line == "\n":
            return
        elif line == "script table begin\n":
            self.state = "reading_script_table"
            return
        elif line == "feature table begin\n":
            self.state = "reading_feature_table"
            return
        elif line == "class definition begin\n":
            self.state = "reading_class_definition"
            return
        elif line == "backtrackclass definition begin\n":
            self.state = "reading_backtrackclass_definition"
            return
        elif line == "lookaheadclass definition begin\n":
            self.state = "reading_lookaheadclass_definition"
            return

        elif line == "class definition end\n":
            self.state = "parsing_lookup"
            return
        elif line == "feature table end\n":
            self.state = "doing_nothing"
            return
        elif line.startswith("lookup end"):
            self.end_lookup()
            self.state = "doing_nothing"
            return
        elif line == "script table end\n":
            self.state = "doing_nothing"
            return
        elif line.startswith("lookup"):
            self.parse_lookup_header(line)
            self.state = "parsing_lookup"
            return
        if line.startswith("#") or line.startswith("%"):
            return

        if self.state == "reading_script_table":
            self.add_to_script_table(line)
        elif self.state == "reading_feature_table":
            self.add_to_feature_table(line)
        elif self.state == "parsing_lookup":
            self.add_to_lookup(line)
        elif self.state == "reading_class_definition":
            self.add_to_class_definition("class", line)
        elif self.state == "reading_backtrackclass_definition":
            self.add_to_class_definition("backtrackclass", line)
        elif self.state == "reading_lookaheadclass_definition":
            self.add_to_class_definition("lookaheadclass", line)

    def add_to_script_table(self, line):
        m = re.match("^(\\w+)\\s+(\\w+)\\s+(.*)$", line)
        lang = m[1] + "/" + m[2]
        self.all_languages.append(lang)
        for f in re.split(r",\s*", m[3]):
            f = int(f)
            if not (f in self.script_applications):
                self.script_applications[f] = []
            self.script_applications[f].append(lang)

    def add_to_feature_table(self, line):
        m = re.match("^(\w+)\s+(\w+)\s+(.*)$", line)
        self.features[int(m[1])] = {
            "tag": m[2],
            "lookups": re.split(r",\s*", m[3]),
        }

    def end_lookup(self):
        # print("Parsed lookup %s" % self.current_lookup.name)
        # Optimizer().optimize_routine(self.current_lookup)
        self.current_lookup = None
        self.resetContexts()

    def parse_lookup_header(self, line):
        m = re.match("^lookup\s+([\\w-]+)\s+(.*)$", line)
        if not m:
            raise ValueError("Unparsable lookup header: |%s|" % line)
        self.current_lookup = Routine(name="lookup_%s" % m[1])
        self.lookups[m[1]] = self.current_lookup
        self.current_lookup_type = m[2]

    def get_class(self, cid, lookup):
        res = lookup["classes"][cid]
        if len(res) == 1:
            return res[0]
        if len(res) > 5:
            if not tuple(res) in self.classes:
                self.classes.append(tuple(res))
            classname = "@class%i" % self.classes.index(tuple(res))
            if classname in self.config:
                return self.config[classname]
            return classname

        return res

    def append_lookup_flag(self, flag):
        if flag == "IgnoreMarks":
            parsedflag = 8
        elif flag == "IgnoreLigatures":
            parsedflag = 4
        elif flag == "IgnoreBaseGlyphs":
            parsedflag = 2
        elif flag == "RightToLeft":
            parsedflag = 1
        elif re.match("^mat(\\d+)$", flag):
            parsedflag = int(flag[3:]) << 8
        else:
            print("Unknown flag %s" % flag)
        self.current_lookup.flags = self.current_lookup.flags | parsedflag

    def add_subst(self, in_, out_):
        self.current_lookup.addRule(Substitution(in_, out_))

    def add_chain_simple(self, context, lookups):
        self.current_lookup.addRule(Chaining(context, lookups=lookups))

    def add_cursive(self, entryexit, glyph, pos):
        if len(self.current_lookup.rules) == 0:
            self.current_lookup.addRule(Attachment("cursive_entry", ""))
        rule = self.current_lookup.rules[-1]
        if entryexit == "entry":
            rule.bases[glyph] = pos
        else:
            rule.marks[glyph] = pos

    def add_single_pos_x(self, glyph, xa):
        self.current_lookup.addRule(Positioning([[glyph]], [ValueRecord(xAdvance=xa)]))
    def add_single_pos_x_placement(self, glyph, xp):
        self.current_lookup.addRule(Positioning([[glyph]], [ValueRecord(xPlacement=xp)]))
    def add_single_pos_y_placement(self, glyph, yp):
        self.current_lookup.addRule(Positioning([[glyph]], [ValueRecord(xPlacement=yp)]))

    def add_pair(self, glyph1, glyph2, xa):
        self.current_lookup.addRule(Positioning([[glyph1], [glyph2]], [ValueRecord(xPlacement=xa),ValueRecord()]))

    def add_attach(self, entryexit, glyph, pos):
        if len(self.current_lookup.rules) == 0:
            self.current_lookup.addRule(
                Attachment(
                    self.current_lookup.name + "_BS", self.current_lookup.name + "_MK"
                )
            )
        rule = self.current_lookup.rules[-1]
        if entryexit == "base":
            rule.bases[glyph] = pos
        else:
            rule.marks[glyph] = pos

    def add_to_lookup(self, line):
        m = re.match("(\w+)\s+(yes|no)", line)
        if m:
            if m[2] == "yes":
                self.append_lookup_flag(m[1])
            return
        m = re.match("MarkAttachmentType\s+(\d+)", line, flags=re.IGNORECASE)
        if m:
            self.append_lookup_flag("mat" + m[1])
            return

        if self.current_lookup_type == "single":
            m = re.match(r"x advance\s+([\w\.-]+)\s+(-?\d+)\n", line)
            if m:
                self.add_single_pos_x(m[1], int(m[2]))
                return
            m = re.match(r"y placement\s+([\w\.-]+)\s+(-?\d+)\n", line)
            if m:
                self.add_single_pos_y_placement(m[1], int(m[2]))
                return
            m = re.match(r"x placement\s+([\w\.-]+)\s+(-?\d+)\n", line)
            if m:
                self.add_single_pos_x_placement(m[1], int(m[2]))
                return
            m = re.match("([\\w\\.-]+)\s+([\\w\\.-]+)\n", line)
            if not m:
                warnings.warn("Odd single lookup: %s" % line)
            #     import code

            #     code.interact(local=locals())
            else:
                self.add_subst([[m[1]]], [[m[2]]])
        elif self.current_lookup_type == "pair":
            m = re.match(r"left x advance\s+([\w\.-]+)\s+([\w\.-]+)\s+(-?\d+)\n", line)
            if not m:
                warnings.warn("Odd pair lookup: %s" % line)
            else:
                self.add_pair(m[1], m[2], int(m[3]))

        elif self.current_lookup_type == "multiple":
            m = re.match("([\\w\\.-]+)\s+(.*)\n", line)
            self.add_subst([[m[1]]], [[x] for x in m[2].split("\t")])

        elif self.current_lookup_type == "ligature":
            m = re.match("([\\w\\.-]+)\s(.*)\n", line)
            if not m:
                raise ValueError("Unparsable line '%s'" % line)
            self.add_subst([[m[2]]], [m[1].split("\t")])

        elif self.current_lookup_type == "cursive":
            m = re.match(r"(entry|exit)\s+(\S+)\s+(-?\d+),(-?\d+).*\n", line)
            if not m:
                raise ValueError("Unparsable cursive '%s'" % line)
            self.add_cursive(m[1], m[2], (int(m[3]), int(m[4])))

        elif (
            self.current_lookup_type == "mark to base"
            or self.current_lookup_type == "mark to mark"
        ):
            m = re.match(r"(mark|base)\s+(\S+)\s+\S+\s+(-?\d+),(-?\d+).*\n", line)
            if not m:
                raise ValueError("Unparsable mark '%s'" % line)
            self.add_attach(m[1], m[2], (int(m[3]), int(m[4])))

        elif self.current_lookup_type == "mark to ligature":
            warnings.warn("Mark to ligature not yet supported")

        elif self.current_lookup_type == "context":
            if line.startswith("glyph"):
                m = line.rstrip().split("\t")
                context = [[x] for x in re.split(r",\s*", m[1])]
                self.add_chain_simple(context, m[2:])
            elif line.startswith("class"):
                m = line.rstrip().split("\t")
                m[1] = m[1].replace(" ", "")
                context = self.make_context(re.split(r",\s*", m[1]), self.classContexts)
                self.add_chain_simple(context, m[2:])
        elif self.current_lookup_type == "chained":
            if line.startswith("class-chain"):
                m = re.match("class-chain\t([^\t]*)\t([^\t]*)\t([^\t]*)\t(.*)$", line)
                precontext = []
                if m[1]:
                    precontext = self.make_context(
                        re.split(r",\s*", m[1]), self.backtrackclassContexts
                    )
                    precontext = list(reversed(precontext))
                context = self.make_context(re.split(r",\s*", m[2]), self.classContexts)
                postcontext = []
                if m[3]:
                    postcontext = self.make_context(
                        re.split(r",\s*", m[3]), self.lookaheadclassContexts
                    )
                lookups = m[4].rstrip().split("\t")
                # print("Lookup %s, lookups = %s" % (self.current_lookup.name, lookups))
                self.current_lookup.addRule(
                    Chaining(
                        context,
                        precontext=precontext,
                        postcontext=postcontext,
                        lookups=lookups,
                    )
                )
            elif line.startswith("glyph"):
                raise ValueError("GSUB6.1 not supported yet")
        else:
            raise ValueError("Unsupported lookup type |%s|" % self.current_lookup_type)

    def make_context(self, classlist, which):
        context = []
        for x in classlist:
            x = x.strip()
            if x == "0":
                if not self.glyphset:
                    raise ValueError(
                        "Class 0 in contextual (%s) but I don't know the glyphset"
                        % self.current_lookup.name
                    )
                else:
                    # Class 0 is everything that's not mentioned elsewhere
                    members = set(self.glyphset)
                    for c in which.values():
                        members = members - set(c)
            else:
                if not x in which:
                    print(
                        "Couldn't find a class definition for class %s in lookup %s"
                        % (x, self.current_lookup.name)
                    )
                members = which[x]
            context.append(members)
        return context

    def add_to_class_definition(self, which, line):
        m = re.match("([\w\.]+)\s+(\d+)", line)
        if not m:
            raise ValueError("Unparsable line '%s'" % line)
        if which == "class":
            which = self.classContexts
        elif which == "backtrackclass":
            which = self.backtrackclassContexts
        elif which == "lookaheadclass":
            which = self.lookaheadclassContexts

        if not m[2] in which:
            which[m[2]] = []
        which[m[2]].append(m[1])


def unparse(filename, config={}, font=None):
    if config:
        import json

        with open(config) as f:
            config = json.load(f)
    else:
        config = {}
    if font:
        glyphset = TTFont(font).getGlyphSet().keys()
    else:
        glyphset = ()
    with open(filename) as file_in:
        parser = FontDameParser(file_in, config, glyphset)
        parser.parse()
    output = ""
    done = {}

    return parser.ff
