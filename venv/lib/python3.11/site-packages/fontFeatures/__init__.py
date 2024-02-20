"""
The FontFeatures class is a way of representing the transformations -
substitutions and positionings - going on inside a font at a semantically
high level. It aims to be independent of and unconstrained by the OpenType
representation, with the assumption that these high-level objects can be
either "compiled down" into AFDKO feature code or directly written to the
GSUB/GPOS tables of a font.

FontFeatures aims to marshal data between OTF binary representations,
AFDKO feature code, FontDame, and can power other representations such as the
FEZ language (see the 'fez' library).

A FontFeatures representation of a font will make use of two other top-level
concepts: Features and Routines. Routines are collections of rules; they play
a similar function to the AFDKO concept of a lookup, but unlike lookups,
Routines do not need to be comprised of rules of the same type. You can think
of them as functions that are called on a glyph string.

Here is an example of constructing a simple feature file using fontFeatures::

    ff = FontFeatures()

    liga_ffi = Substitution( [ ["f"], ["f"], ["i"] ], replacement=[["f_f_i"]] )
    liga_ffl = Substitution( [ ["f"], ["f"], ["l"] ], replacement=[["f_f_l"]] )
    liga_fi = Substitution( [ ["f"], ["i"] ], replacement=[["fi"]] )
    liga_ff = Substitution( [ ["f"], ["f"] ], replacement=[["f_f"]] )
    liga_routine = Routine(rules=[liga_ffi, liga_ffl, liga_fi, liga_ff])

    ff.addFeature("liga", [liga_routine])

    # Export Adobe syntax
    print(ff.asFea())

    font = TTFont("Test.ttf")
    ff.buildBinaryFeatures(font)
    font.save("Test-liga.ttf")
"""

from collections import OrderedDict, namedtuple
from fontTools.feaLib.ast import ValueRecord as feaLibValueRecord
from fontTools.feaLib.variableScalar import VariableScalar
from itertools import chain
from copy import copy


class FontFeatures:
    """An object representing the layout rules in a font.

    The initializer has no parameters."""

    def __init__(self):
        self.namedClasses = {}  #: A mapping of named classes to a list of glyph names which make up the class.
        self.routines = []  #: All of the layout routines used in this font.
        self.features = OrderedDict()  #: An ordered dictionary mapping feature tags to a list of routine references.
        self.anchors = {}  #: A dictionary mapping glyph names to a dictionary of anchor names / positions.
        self.symbols = {}
        self.glyphclasses = {}  #: A dictionary mapping glyph names to their categories.
        self.scratch = {}  #: Space for items to communicate context to each other.
        self.doneUsageMarking = False

    def __add__(self, other):
        """Combine two FontFeatures objects together."""
        combined = FontFeatures()
        for k in ["namedClasses", "routines", "features", "anchors", "symbols", "glyphclasses"]:
            if isinstance(getattr(combined, k), dict):
                getattr(combined, k).update(getattr(self, k))
                getattr(combined, k).update(getattr(other, k))
            else:
                setattr(combined, k, getattr(self, k) + getattr(other, k))
        return combined

    def gensym(self, category):
        """Generate a new unique symbol (used for labeling unlabeled data).

        Args:
            category (str): The category for this symbol

        Returns: a string representing a unique label."""
        if not category in self.symbols:
            self.symbols[category] = 0
        self.symbols[category] += 1
        return f"{category}{self.symbols[category]}"

    def routineNamed(self, name):
        """Finds a routine with the given name.

        Args:
            name (str): The name to find

        Returns: a :py:class:`Routine` object if the named routine was found
          in the features object. Raises a ``ValueError`` if not."""
        for r in self.routines:
            if r.name == name:
                return r
        raise ValueError("Can't find routine '%s'" % name)

    def referenceRoutine(self, r, do_usecount=True):
        """Store a routine and return a reference to it.

        Args:
            r: A :py:class:`Routine` object.
        """
        assert isinstance(r, Routine)

        if r not in self.routines:
            self.routines.append(r)
        r.parent = self
        if do_usecount:
            r.usecount = r.usecount + 1
        return RoutineReference(routine=r)

    def getNamedClassFor(self, glyphs, name):
        """Find and optionally stores a named class of glyphs

        Args:
            glyphs: A sequence of glyph names.
            name: A name for this glyph class if it does not exist.

        Returns:
            The name of a glyph class. If the exact same set of glyphs
            was already stored as a glyph class, then the name of that
            class will be returned. If not, then the class will be stored
            and the name provided as the ``name`` argument will be returned.
        """
        for k,v in self.namedClasses.items():
            if sorted(glyphs) == sorted(v):
                return k
        self.namedClasses[name] = glyphs
        return name

    def addFeature(self, name, rs):
        """Add Routines to a named feature.

        Args:
            name: The feature name.
            rs: A sequence of :py:class:`Routine` or :py:class:`RoutineReference` objects.
        """
        if not name in self.features:
            self.features[name] = []
        for r in rs:
            r.parent = self
            if isinstance(r, Routine):
                r = self.referenceRoutine(r)
            self.features[name].append(r)


    def allRules(self, ruletype=None):
        """Return all rules in the font, optionally filtered by type

        Args:
            ruletype: A class (``Positioning``, ``Substitution`` etc)
                to filter the results.

        Returns:
            Routines stored in the preamble and within features.
        """

        rules = []
        for r in self.routines:
            rules.extend(r.rules)

        if ruletype:
            rules = filter(lambda x: isinstance(x, ruletype), rules)
        return rules

    def markRoutineUseInChains(self):
        """Annotate routines which are used in chaining rules.

        Generally used when converting the fontFeatures object to another
        format; allows routines to know where they are being used by annotating
        them with the ``.usedin`` property for optimization purposes.
        """
        if self.doneUsageMarking:
            return
        for r in self.routines:
            r.usedin = set()
        for chain in self.allRules(Chaining):
            for routinelist in chain.lookups:
                if not routinelist:
                    continue
                for routine in routinelist:
                    # Using a set here so it is safe to call more than once
                    if isinstance(routine, RoutineReference):
                        routine.resolve(self)
                        routine.routine.usedin.add(chain)
                    else:
                        routine.usedin.add(chain)
        self.doneUsageMarking = True

    def hoist_languages(self):
        """Sort routines into scripts and languages and resolve wildcards."""
        scripts = OrderedDict()
        count = 0

        def add_language(p):
            nonlocal scripts
            nonlocal count
            s, l = p
            if not s in scripts:
                scripts[s] = []
            if l == "*":
                return
            if not l in scripts[s]:
                count = count + 1
                scripts[s].append(l)

        for k in self.routines:
            if k.languages:
                for l in k.languages:
                    add_language(l)
            else:
                for r in k.rules:
                    for l in (r.languages or []):
                        add_language(l)

        # if count > 0 and not "DFLT" in scripts:
        #     scripts["DFLT"] = []
        #     scripts.move_to_end("DFLT", last=False)
        # if count > 0 and not "dflt" in scripts["DFLT"]:
        #     scripts["DFLT"].insert(0, "dflt")

        self.scripts_and_languages = scripts

    def hasScriptSupport(self, script):
        """Check if the features object has support for a particular script.

        Args:
            script (str): A four-character OpenType script code.

        Returns: boolean
        """
        self.hoist_languages()
        return script in self.scripts_and_languages

    def resolveAllRoutines(self):
        """Resolve reference use in chains.

        Checks that all routines referenced in chain rules can actually
        be found within the object, and adds pointers to match named routine
        references with the relevant :py:class:`Routine` object.
        """
        for routine in self.routines:
            for r in routine.rules:
                if not isinstance(r, Chaining):
                    continue
                for lookuplistIx in range(len(r.lookups)):
                    r.lookups[lookuplistIx] = self.ensureLookupsAreReferences(
                        r.lookups[lookuplistIx]
                    )

    def ensureLookupsAreReferences(self, lookuplist):
        """Ensures that all references are lookups.

        Naughty people might put :py:class:`Routine` objects directly into
        :py:class:`Chain` lookups. This tidies them up."""
        rv = []
        if not lookuplist:
            return None
        for r in lookuplist:
            if isinstance(r, RoutineReference):
                r.resolve(self)
            else:
                r = self.referenceRoutine(r)
            assert r.routine in self.routines
            rv.append(r)
        return rv

    def setGlyphClassesFromFont(self, font):
        """Loads glyph classes from the font."""
        for g in font.exportedGlyphs():
            if hasattr(font, "glyphs"):
                self.glyphclasses[g] = font.glyphs[g].category
            else:
                self.glyphclasses[g] = font[g].category

    def partitionRoutine(self, routine, factor):
        """Splits a routine based on a predicate.

        This method applies a function to each rule in the routine and creates
        distinct routines, each containing rules with the same return value
        from the function. This is useful, for example, when exporting to
        OpenType, to ensure that all rules in a routine must have the same type,
        same flags, etc.

        Args:
            routine: A :py:class:`Routine` object.
            factor: A function applied to each of the :py:class:`Rule` objects.

        Returns: A list of :py:class:`Routine` objects. Additionally, modifies
        the ``.routines`` list of the FontFeatures object."""
        if not routine.rules:
            return
        self.doneUsageMarking = False
        self.markRoutineUseInChains()

        split_routines = {}
        split_rules = {}
        # The first rule stays in the original
        split_routines[factor(routine.rules[0])] = (routine, [routine.rules[0]])
        for rule in routine.rules[1:]:
            thisfactor = factor(rule)
            if thisfactor not in split_routines:
                rulelist = []
                newroutine = copy(routine)
                newroutine.rules = rulelist
                split_routines[thisfactor] = (newroutine, rulelist)
            split_routines[thisfactor][1].append(rule)

        # Alter the first rule's routine's rulelist (we couldn't alter it on
        # the fly because we were iterating over it).
        routine_with_first_rule, rulelist = split_routines[factor(routine.rules[0])]
        routine_with_first_rule.rules = rulelist

        allroutines = [x[0] for x in split_routines.values()]
        return self.replaceRoutineWithSplitList(routine, allroutines)

    def replaceRoutineWithSplitList(self, routine, allroutines):
        self.markRoutineUseInChains()
        index = self.routines.index(routine)
        usedin = routine.usedin
        self.routines[index : index + 1] = allroutines
        for user in usedin:
            for lookuplist in user.lookups:
                if lookuplist is None:
                    continue
                i = 0
                while i < len(lookuplist):
                    lookup = lookuplist[i]
                    if lookup == routine or (
                        isinstance(lookup, RoutineReference)
                        and lookup.routine == routine
                    ):
                        lookuplist[i : i + 1] = [
                            RoutineReference(routine=r) for r in allroutines
                        ]
                    i = i + 1
        # Same trick for features
        for lookuplist in self.features.values():
            if lookuplist is None:
                continue
            i = 0
            while i < len(lookuplist):
                lookup = lookuplist[i]
                if lookup == routine or (
                    isinstance(lookup, RoutineReference) and lookup.routine == routine
                ):
                    lookuplist[i : i + 1] = [
                        RoutineReference(routine=r) for r in allroutines
                    ]
                i = i + 1
        return allroutines

    from .feaLib.FontFeatures import asFea, asFeaAST
    from .xmlLib.FontFeatures import toXML, fromXML
    from .ttLib.FontFeatures import buildBinaryFeatures


class Routine:
    """Represent a Routine (similar to OT Lookup).

    A routine is a set of rules, sometimes but not always with an explicit name.
    It can apply to a set of language/script pairs.
    """

    def __init__(
        self,
        name="",
        rules=None,
        address=None,
        inlined=False,
        languages=None,
        parent=None,
        flags=0,
        markFilteringSet=None,
        markAttachmentSet=None,
    ):
        self.name = name
        self.usecount = 0
        self.usedin = set()
        if rules:
            self.rules = rules
        else:
            self.rules = []
        self.address = address
        self.comments = []
        self.inlined = inlined
        self.languages = languages or []
        self.parent = parent
        self.flags = flags
        self.markFilteringSet = markFilteringSet
        self.markAttachmentSet = markAttachmentSet

    def addRule(self, rule):
        """Adds a rule to a Routine.

        Args:
            rule: A ``Substitution``, ``Positioning``, etc. object.
        """
        assert isinstance(rule, Rule)
        self.rules.append(rule)

    def addComment(self, comment):
        """Adds a comment to a Routine.

        Comments are emitted when the Routine is converted to text formats
        such as AFDKO.

        Args:
            comment: A string comment.
        """
        self.comments.append(comment)

    @property
    def involved_glyphs(self):
        """Returns the names of all of the glyphs involved in this Routine."""
        return set().union(*(r.involved_glyphs for r in self.rules))

    @property
    def stage(self):
        """Returns which shaping stage this routine is used in.

        Returns: ``sub`` for substitution stage, ``pos`` for positioning stage."""
        for r in self.rules:
            if isinstance(r, Substitution):
                return "sub"
            if isinstance(r, Positioning):
                return "pos"
            if isinstance(r, Attachment):
                return "pos"
            if isinstance(r, Chaining):
                return r.stage

    @property
    def dependencies(self):
        """Returns a list of :py:class:`Routine` objects called as lookups in
        this Routine."""
        deps = []
        for r in self.rules:
            deps.extend(r.dependencies)
        return deps

    from .feaLib.Routine import asFea, asFeaAST, feaPreamble
    from .shaperLib.Routine import apply_to_buffer
    from .xmlLib.Routine import toXML, fromXML
    from .ttLib.Routine import toOTLookup


class ExtensionRoutine(Routine):
    """OpenType-specific concept: A routine which contains other routines."""
    def __init__(self, **kwargs):
        if "routines" in kwargs:
            self.routines = kwargs["routines"]
            del kwargs["routines"]
        super().__init__(**kwargs)

    def apply_to_buffer(self, buf, stage=None, feature=None):
        """Applies shaping rules from this routine to a buffer.

        Args:
            buf: A :py:class:`fontFeatures.shaperLib.Buffer` object.
            stage (str): Shaping stage - ``sub`` or ``pos``.
            feature (str): The feature being processed. (For debugging.)

        Modifies the ``buf`` object.
        """
        for r in self.routines:
            r.apply_to_buffer(buf, stage, feature)

    def asFeaAST(self):
        """Returns this extension routine as ``fontTools.feaLib.ast`` objects."""
        import fontTools.feaLib.ast as feaast

        f = feaast.Block()
        for r in self.routines:
            f.statements.append(r.asFeaAST())
        return f

    @property
    def stage(self):
        """Returns which shaping stage this routine is used in.

        Returns: ``sub`` for substitution stage, ``pos`` for positioning stage."""
        return self.routines[0].stage

    @property
    def rules(self):
        """All rules under this extension.

        Returns: A flattened list of :py:class:`Rule` objects."""
        return list(chain(*[routine.rules for routine in self.routines]))

    @rules.setter
    def rules(self, foo):
        """Does nothing. Don't set rules here."""
        pass


class RoutineReference:
    """A reference to a Routine object, used in a lookup.

    Routines can be referenced either by name (for example, when loaded from a
    textual representation), in which case they will be resolved at a later time,
    or by providing a pointer to the :py:class:`Routine` object."""
    def __init__(self, name=None, routine=None):
        self.routine = routine
        if self.routine:
            self.name = routine.name
        if name:
            self.name = name

    def resolve(self, ff):
        """Resolves the reference in the context of a :py:class:`FontFeatures`
        object.

        Raises a ``ValueError`` if a named routine cannot be found.
        """
        if not self.routine:
            self.routine = ff.routineNamed(self.name)
            if not self.routine:
                raise ValueError("Could not resolve routine")
        if not self.name:
            self.name = self.routine.name

    @property
    def stage(self):
        """Returns which shaping stage this routine is used in.

        Returns: ``sub`` for substitution stage, ``pos`` for positioning stage."""
        if not self.routine:
            raise ValueError("Routine reference not resolved")
        return self.routine.stage

    from .xmlLib.RoutineReference import fromXML, toXML
    from .feaLib.RoutineReference import asFeaAST, feaPreamble

    def asFea(self):
        """Returns this Rule as a string of AFDKO feature text."""
        return self.asFeaAST().asFea()

class Rule:
    """A base class for all rules."""
    def asFea(self):
        """Returns this Rule as a string of AFDKO feature text."""
        return self.asFeaAST().asFea()

    def feaPreamble(self, ff):
        """Computes any text that needs to go in the feature file header."""
        return []

    from .shaperLib.Rule import would_apply_at_position, pre_post_context_matches
    from .xmlLib.Rule import fromXML, toXML, _makeglyphslots, _slotArray

    @property
    def has_context(self):
        """Does this rule have any pre- or post-context defined?"""
        return len(self.precontext) or len(self.postcontext)

    @property
    def dependencies(self):
        """Returns a list of :py:class:`Routine` objects called as lookups in
        this Routine."""
        return []


class Substitution(Rule):
    """Represents a Substitution rule.

    A substitution represents any kind of exchange of one set of glyphs for
    another: single substitutions, multiple substitutions and ligatures are all
    substitutions. Optionally, substitutions may be followed by precontext and
    postcontext.

    Args:
        input_: A list of lists. The outer list represents the positions in
            the glyph stream to substitute, with the inner list representing
            the glyph names at each position.
        replacement: A list of glyph names.
        precontext: A list of list of glyphs which must appear before the input
            sequence.
        postcontext: A list of list of glyphs which must appear before the input
            sequence.
        lookups: A list of list of lookups to be applied to the glyph sequence.
            The outer list represents the positions in the input sequence, with
            the inner list containing Routines to apply.
        reverse: Boolean representing if the substitutions should take place from
            the end of the string.
        force_alt: Force this substitution to be interpreted as an alternate
            substitution.

    Examples::

        lig = Substitution(
            [ ["f"], ["i"] ],
            ["f_i"]
        ) # sub f i by f_i;

        contextual = Substitution(
            [ ["dotbelow"] ],
            [ ["dotbelow.post"] ],
            precontext = [["ra-myanmar", "ra-myanmar.bt1", "ra-myanmar.bt2"]]
        ) # sub [ra-myanmar ra-myanmar.bt1 ra-myanmar.bt2] dotbelow-myanmar'
          # by dotbelow-myanmar.post;
    """

    def __init__(
        self,
        input_,
        replacement,
        precontext=None,
        postcontext=None,
        address=None,
        languages=None,
        lookups=None,
        reverse=False,
        flags=0,
        force_alt=False
    ):
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        self.input = input_
        self.replacement = replacement
        self.address = address
        self.lookups = lookups or []
        self.languages = languages
        self.flags = flags
        self.reverse = reverse
        self.stage = "sub"
        self.force_alt = force_alt

    @property
    def involved_glyphs(self):
        """Returns a set of all glyphs involved in this rule."""
        i = set(chain.from_iterable(self.input))
        o = set(chain.from_iterable(self.replacement))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | o | b | a

    from .feaLib.Substitution import asFeaAST
    from .shaperLib.Substitution import shaper_inputs, _do_apply
    from .xmlLib.Substitution import _toXML, fromXML
    from .ttLib.Substitution import lookup_type


class Chaining(Rule):
    """Represents a Chain rule.

    A Chain rule represents the operation of calling another Routine when
    a particular input context is met.

    Args:
        input_: A list of lists. The outer list represents the positions in
            the glyph stream to substitute, with the inner list representing
            the glyph names at each position.
        precontext: A list of list of glyphs which must appear before the input
            sequence.
        postcontext: A list of list of glyphs which must appear before the input
            sequence.
        lookups: A list of list of lookups to be applied to the glyph sequence.
            The outer list represents the positions in the input sequence, with
            the inner list containing Routines to apply.

    Example::

        sub_Qu = Routine(rules=[
            Substitute([["Q"]], [["Q.beforeu"]])
        ])

        chain = Chain(
            [["Q"]],
            postcontext = [ ["u", "v", "u.sc", "v.sc"] ],
            lookups = [ [sub_Qu] ]
        ) # sub Q' lookup sub_Qu [u v u.sc v.sc];
    """

    def __init__(
        self,
        input_,
        precontext=None,
        postcontext=None,
        address=None,
        languages=None,
        lookups=None,
        flags=0,
    ):
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        self.input = input_
        self.address = address
        self.lookups = lookups or []
        self.languages = languages
        self.flags = flags

    @property
    def stage(self):
        """Returns which shaping stage this routine is used in.

        Returns: ``sub`` for substitution stage, ``pos`` for positioning stage."""
        for l in self.lookups:
            if not l:
                continue
            for aLookup in l:
                if not aLookup:
                    continue
                return aLookup.stage

    @property
    def involved_glyphs(self):
        """Returns a set of all glyphs involved in this rule."""
        i = set(chain.from_iterable(self.input))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | b | a

    @property
    def dependencies(self):
        """Returns a list of :py:class:`Routine` objects called as lookups in
        this Routine."""
        deps = []
        for l in self.lookups:
            for aLookup in (l or []):
                if isinstance(aLookup, RoutineReference):
                    deps.append(aLookup.routine)
                else:
                    deps.append(aLookup)
        return deps

    from .feaLib.Chaining import asFeaAST, feaPreamble
    from .shaperLib.Chaining import shaper_inputs, _do_apply
    from .xmlLib.Chaining import _toXML, fromXML
    from .ttLib.Chaining import lookup_type


class ValueRecord(feaLibValueRecord):
    """A value record for representing positional changes in advance and placement.

    See :py:class:`fontTools.feaLib.ValueRecord`, from which this inherits.
    """
    from .ttLib.ValueRecord import toOTValueRecord

    @property
    def is_variable(self):
        """Returns true if any of the elements of the value record are a
        :py:class:`fontTools.feaLib.VariableScalar`."""
        return any(
            isinstance(x, VariableScalar)
            for x in [
                self.xPlacement,
                self.yPlacement,
                self.xAdvance,
                self.yAdvance,
            ]
        )


class Positioning(Rule):
    """Represents a Positioning rule.

    Args:
        input_: A list of lists. The outer list represents the positions in
            the glyph stream to position, with the inner list representing
            the glyph names at each glyph stream position.
        valuerecords: A list of ``ValueRecord`` objects to be applied at each
            glyph stream position.
        precontext: A list of list of glyphs which must appear before the input
            sequence.
        postcontext: A list of list of glyphs which must appear before the input
            sequence.

    Example::

        open_up_behs = Positioning(
            [
                ["BEi1", "BEi2"],
                ["sda", "sdb", "dda", "ddb"]
            ],
            [
                ValueRecord(xAdvance=200),
                ValueRecord(xPlacement=50),
            ]
            postcontext = [ medis_finas ]
        )
        # pos [BEi1 BEi2]' <0 0 200 0> [sda sdb dda ddb]' <0 50 0 0> @medis_finas;
    """

    def __init__(
        self,
        glyphs,
        valuerecords,
        precontext=None,
        postcontext=None,
        address=None,
        languages=None,
        flags=0,
    ):
        self.precontext = precontext or []
        self.postcontext = postcontext or []
        assert len(glyphs) == len(valuerecords)
        self.glyphs = glyphs
        self.valuerecords = valuerecords
        self.address = address
        self.languages = languages
        self.flags = flags
        self.stage = "pos"

    @property
    def involved_glyphs(self):
        """Returns a set of all glyphs involved in this rule."""
        i = set(chain.from_iterable(self.glyphs))
        b = set(chain.from_iterable(self.precontext))
        a = set(chain.from_iterable(self.postcontext))
        return i | b | a

    from .feaLib.Positioning import asFeaAST
    from .shaperLib.Positioning import shaper_inputs, _do_apply
    from .xmlLib.Positioning import _toXML, fromXML
    from .ttLib.Positioning import lookup_type


class Attachment(Rule):
    """Represents an Attachment rule.

    Args:
        base_name: Name of the base class.
        mark_name: Name of the mark class.
        bases: Dictionary. They keys are names of glyphs to act as bases to
            the attachment (this may be categorized as mark glyphs if the
            attachment is a mark-to-mark operation); the associated values are
            a two-element tuple with the coordinates of the anchor.
        marks: Dictionary. They keys are names of glyphs to act as marks;
            the associated values are a two-element tuple with the coordinates
            of the anchor.
        force_markmark: boolean. If true, force this to be interpreted as a
            mark-to-mark operation

    Whether this is a mark-to-base or mark-to-mark operation will be determined
    by the glyph category of the glyphs involved in the `bases` dictionary and
    the value of the `force_markmark` argument.

    Examples::

        ff.anchors = {
            "a": { "top": (250, 603) },
            "acutecomb": { "_top": (56, 0) }
        }

        top_bases = {}
        top_marks = {}
        for glyphname, anchors in ff.anchors.items():
            for anchorname, position in anchors.items():
                if anchorname == "top":
                    top_bases[glyphname] = position
                if anchorname == "_top":
                    top_marks[glyphname] = position

        # top_bases = { "a": (260,603) }
        # top_marks = { "acutecomb": (56,0) }

        tops = Attachment("top", "_top", top_bases, top_marks)
    """

    def __init__(
        self,
        base_name,
        mark_name,
        bases=None,
        marks=None,
        flags=0,
        address=None,
        font=None,
        languages=None,
        force_markmark=False
    ):
        self.base_name = base_name
        self.mark_name = mark_name
        self.bases = bases or {}
        self.marks = marks or {}
        self.flags = flags
        self.address = address
        self.font = font
        self.stage = "pos"
        self.languages = languages or []
        self.force_markmark = force_markmark

    @property
    def is_cursive(self):
        """Returns true if this is a cursive attachment rule."""
        return self.base_name == "cursive_entry" or self.base_name == "entry"  # XXX

    from .feaLib.Attachment import asFeaAST, feaPreamble
    from .shaperLib.Attachment import shaper_inputs, _do_apply, would_apply_at_position
    from .xmlLib.Attachment import _toXML, fromXML
    from .ttLib.Attachment import lookup_type

    @property
    def involved_glyphs(self):
        """Returns a set of all glyphs involved in this rule."""
        b = set(self.bases.keys())
        m = set(self.marks.keys())
        return b | m
