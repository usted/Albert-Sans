from collidoscope import Collidoscope
from argparse import ArgumentParser, FileType
import tqdm


parser = ArgumentParser()
parser.add_argument("input",
                    help="font file to process", metavar="OTF")
parser.add_argument('-c', type=int, default=3, dest="context",
                    help="number of glyphs to process", metavar="CONTEXT")
parser.add_argument('--no-faraway', action='store_false', dest="faraway",
                    help="don't check for interactions between non-adjacent glyphs")
parser.add_argument('--no-marks', action='store_false', dest="marks",
                    help="don't check for interactions between marks")
parser.add_argument('--no-bases', action='store_false', dest="bases",
                    help="don't check for interactions between bases")
parser.add_argument('--no-adjacent-clusters', action='store_false', dest="adjacent_clusters",
                    help="don't check for interactions between glyphs in adjacent clusters")
parser.add_argument('--cursive', action='store_true', dest="cursive",
                    help="check for interactions between paths without anchors")
parser.add_argument('--area', type=int, default=0, dest="area",
                    help="check for interactions of size >=area%% between paths")
parser.add_argument('--scale-factor', dest="scale_factor",
                    help="Scale glyphs before checking", metavar="SCALE", default=1.0)

parser.add_argument('-r', dest="range",
                    help="Comma-separated list of Unicode ranges", metavar="RANGE")

parser.add_argument('-t', dest="text",
                    help="Text to check", metavar="TEXT")

parser.add_argument('-f', dest="file", type=FileType('r'),
                    help="File of lines to check", metavar="FILE")

parser.add_argument('-o', dest="output", type=FileType('w'), default="report.html",
                    help="Output report file", metavar="FILE")


args = parser.parse_args()

report = args.output

fontfilename = args.input

c = Collidoscope(fontfilename, {
        "faraway": args.faraway,
        "adjacent_clusters": args.adjacent_clusters,
        "cursive": args.cursive,
        "area":    args.area / 100,
        "marks":   args.marks,
        "bases":   args.bases
    },
    scale_factor = float(args.scale_factor)
)


import itertools

report.write('''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"> 
    <title></title>
<style>
        .cards {
display: grid;
grid-template-columns: repeat(auto-fill, 250px);
grid-auto-rows: auto;
grid-gap: 1rem;
font-family:'%s'; font-size:50pt;
}
        svg { transform: scaleY(-1); }
 
.card {
border: 2px solid #e7e7e7;
border-radius: 4px;
padding: .5rem;
}</style>
</head>

<body>
<h2>Collision Report</h2>
<div class="cards">
''' %  c.ttfont["name"].getDebugName(1))

codepoints = c.ttfont.getBestCmap().keys()
codepointfilter = []


counter = 0

def gen_texts(codepoints):
    print("Generating text...")
    combinations = []
    texts = []

    count = 1
    for i in range(0,args.context):
        combinations.append(codepoints)
        count = count * len(codepoints)

    for element in itertools.product(*combinations):
        text = "".join(map(chr, element))
        texts.append(text)
    print("Done")
    return texts

if args.text:
    texts = [args.text]
elif args.file:
    texts = [ x.rtrim() for x in args.file.readlines()]
elif args.range:
    for r in args.range.split(","):
        if "-" in r:
            first, last = r.split("-")
            codepointfilter.extend(range(int(first, 16),int(last,16)+1))
        else:
            codepointfilter.append(int(r,16))
    codepoints = list(filter(lambda x: x in codepointfilter, codepoints))
    texts = gen_texts(codepoints)
else:
    print("Testing ALL GLYPHS AGAINST ALL GLYPHS - you may want to specify a -r range e.g. -r 0620-064A")
    texts = gen_texts(codepoints)

c.prep_shaper()

pbar = tqdm.tqdm(texts)
for text in pbar:
    pbar.set_description(text)
    glyphs = c.get_glyphs(text)
    cols = c.has_collisions(glyphs)
    if cols:
        cols = c.draw_overlaps(glyphs, cols, "preserveAspectRatio=\"xMidYMax\" width=300 height=200")
        report.write("<div class=\"card\"> %s %s</div> \n" % (text, cols))
        report.flush()
    counter = counter + 1

report.write('''
</div>
</body>
</html>
''')

print("Output written on %s" % args.output.name)
# hbfont = prep_shaper(fontfilename)
# glyphs = get_glyphs(hbfont, font, "ۍ", anchors)
# print(has_collisions(glyphs, 1, {
#         "faraway": False,
#         "cursive": False,
#         "area":    0.4
#     }))
