## FontBakery report

fontbakery version: 0.12.9



## Experimental checks

These won't break the CI job for now, but will become effective after some time if nobody raises any concern.


<details><summary>[1] AlbertSans-Italic[wdth,wght].ttf</summary>
<div>
<details>
    <summary>⚠️ <b>WARN</b> Validate size, and resolution of article images, and ensure article page has minimum length and includes visual assets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.article.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>Family metadata at fonts/variable does not have an article.</p>
 [code: lacks-article]



</div>
</details>
</div>
</details>

<details><summary>[1] AlbertSans-Roman[wdth,wght].ttf</summary>
<div>
<details>
    <summary>⚠️ <b>WARN</b> Validate size, and resolution of article images, and ensure article page has minimum length and includes visual assets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.article.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>Family metadata at fonts/variable does not have an article.</p>
 [code: lacks-article]



</div>
</details>
</div>
</details>




## All other checks



<details><summary>[2] Family checks</summary>
<div>
<details>
    <summary>🔥 <b>FAIL</b> Ensure VFs have 'ital' STAT axis. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/opentype.stat.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>Italics missing a Roman counterpart, so couldn't check both Roman and Italic for 'ital' axis: fonts/variable/AlbertSans-Italic[wdth,wght].ttf</p>
 [code: missing-roman]



</div>
</details>

<details>
    <summary>🔥 <b>FAIL</b> Ensure Italic styles have Roman counterparts. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.family.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>Italics missing a Roman counterpart: fonts/variable/AlbertSans-Italic[wdth,wght].ttf</p>
 [code: missing-roman]



</div>
</details>
</div>
</details>

<details><summary>[13] AlbertSans-Italic[wdth,wght].ttf</summary>
<div>
<details>
    <summary>🔥 <b>FAIL</b> Ensure the font supports case swapping for all its glyphs. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.glyphset.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>The following glyphs lack their case-swapping counterparts:</p>
<table>
<thead>
<tr>
<th align="left">Glyph present in the font</th>
<th align="left">Missing case-swapping counterpart</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left">U+A732: LATIN CAPITAL LETTER AA</td>
<td align="left">U+A733: LATIN SMALL LETTER AA</td>
</tr>
</tbody>
</table>
 [code: missing-case-counterparts]



</div>
</details>

<details>
    <summary>🔥 <b>FAIL</b> Shapes languages in all GF glyphsets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.glyphset.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>GF_Latin_Core glyphset:</p>
<table>
<thead>
<tr>
<th align="left">Language</th>
<th align="left">FAIL messages</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left">nl_Latn (Dutch)</td>
<td align="left">Shaper didn't attach acutecomb to J</td>
</tr>
<tr>
<td align="left">^</td>
<td align="left">Shaper didn't attach acutecomb to uni0237</td>
</tr>
</tbody>
</table>
 [code: failed-language-shaping]



</div>
</details>

<details>
    <summary>🔥 <b>FAIL</b> Combined length of family and style must not exceed 32 characters. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.name.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>Variable font instance name 'Albert Sans Medium ExtraLight Italic' formed by space-separated concatenation of font family name (nameID 1) and instance subfamily nameID 283 exceeds 32 characters.</p>
<p>This has been found to cause shaping issues for some accented letters in Microsoft Word on Windows 10 and 11.</p>
 [code: instance-too-long]



* 🔥 **FAIL** <p>Variable font instance name 'Albert Sans Medium ExtraLight Italic' formed by space-separated concatenation of font family name (nameID 1) and instance subfamily nameID 283 exceeds 32 characters.</p>
<p>This has been found to cause shaping issues for some accented letters in Microsoft Word on Windows 10 and 11.</p>
 [code: instance-too-long]



* 🔥 **FAIL** <p>Variable font instance name 'Albert Sans Medium SemiBold Italic' formed by space-separated concatenation of font family name (nameID 1) and instance subfamily nameID 287 exceeds 32 characters.</p>
<p>This has been found to cause shaping issues for some accented letters in Microsoft Word on Windows 10 and 11.</p>
 [code: instance-too-long]



* 🔥 **FAIL** <p>Variable font instance name 'Albert Sans Medium SemiBold Italic' formed by space-separated concatenation of font family name (nameID 1) and instance subfamily nameID 287 exceeds 32 characters.</p>
<p>This has been found to cause shaping issues for some accented letters in Microsoft Word on Windows 10 and 11.</p>
 [code: instance-too-long]



* 🔥 **FAIL** <p>Variable font instance name 'Albert Sans Medium ExtraBold Italic' formed by space-separated concatenation of font family name (nameID 1) and instance subfamily nameID 289 exceeds 32 characters.</p>
<p>This has been found to cause shaping issues for some accented letters in Microsoft Word on Windows 10 and 11.</p>
 [code: instance-too-long]



* 🔥 **FAIL** <p>Variable font instance name 'Albert Sans Medium ExtraBold Italic' formed by space-separated concatenation of font family name (nameID 1) and instance subfamily nameID 289 exceeds 32 characters.</p>
<p>This has been found to cause shaping issues for some accented letters in Microsoft Word on Windows 10 and 11.</p>
 [code: instance-too-long]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check math signs have the same width. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The most common width is 596 among a set of 2 math glyphs.
The following math glyphs have a different width, though:</p>
<p>Width = 391:
greater, less</p>
<p>Width = 637:
equal, approxequal</p>
<p>Width = 665:
logicalnot</p>
<p>Width = 623:
plusminus</p>
<p>Width = 525:
multiply</p>
<p>Width = 491:
minus</p>
<p>Width = 645:
notequal</p>
<p>Width = 467:
greaterequal, lessequal</p>
 [code: width-outliers]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Does the font contain a soft hyphen? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.glyphset.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>This font has a 'Soft Hyphen' character.</p>
 [code: softhyphen]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check font contains no unreachable glyphs <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.glyphset.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The following glyphs could not be reached by codepoint or substitution rules:</p>
<pre><code>- uni030C.alt
</code></pre>
 [code: unreachable-glyphs]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Are there any misaligned on-curve points? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/outline.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The following glyphs have on-curve points which have potentially incorrect y coordinates:</p>
<pre><code>* Iogonek (U+012E): X=139.0,Y=1.0 (should be at baseline 0?)

* Lcaron (U+013D): X=440.0,Y=701.0 (should be at cap-height 700?)

* Lcaron (U+013D): X=546.0,Y=701.0 (should be at cap-height 700?)

* uni013B (U+013B): X=440.0,Y=701.0 (should be at cap-height 700?)

* uni013B (U+013B): X=546.0,Y=701.0 (should be at cap-height 700?)

* uni0162 (U+0162): X=318.0,Y=-248.0 (should be at descender -250?)

* uni013B.loclMAH: X=440.0,Y=701.0 (should be at cap-height 700?)

* uni013B.loclMAH: X=546.0,Y=701.0 (should be at cap-height 700?)

* abreve (U+0103): X=187.0,Y=698.0 (should be at cap-height 700?)

* aring (U+00E5): X=332.0,Y=702.0 (should be at cap-height 700?)

* ccedilla (U+00E7): X=300.0,Y=-248.0 (should be at descender -250?)

* ebreve (U+0115): X=213.0,Y=698.0 (should be at cap-height 700?)

* gbreve (U+011F): X=220.0,Y=698.0 (should be at cap-height 700?)

* obreve (U+014F): X=224.0,Y=698.0 (should be at cap-height 700?)

* scedilla (U+015F): X=248.0,Y=-248.0 (should be at descender -250?)

* t (U+0074): X=245.5,Y=-1.0 (should be at baseline 0?)

* tcaron (U+0165): X=245.5,Y=-1.0 (should be at baseline 0?)

* uni0163 (U+0163): X=245.5,Y=-1.0 (should be at baseline 0?)

* uni0163 (U+0163): X=211.0,Y=-248.0 (should be at descender -250?)

* uni021B (U+021B): X=245.5,Y=-1.0 (should be at baseline 0?)

* ubreve (U+016D): X=203.0,Y=698.0 (should be at cap-height 700?)

* uring (U+016F): X=348.0,Y=702.0 (should be at cap-height 700?)

* comma.ss01: X=112.0,Y=1.0 (should be at baseline 0?)

* ampersand (U+0026): X=574.0,Y=-1.0 (should be at baseline 0?)

* turkishlira (U+20BA): X=267.5,Y=-1.0 (should be at baseline 0?)

* arrowup (U+2191): X=309.0,Y=-1.0 (should be at baseline 0?)

* arrowup (U+2191): X=218.0,Y=-1.0 (should be at baseline 0?)

* uni0306 (U+0306): X=75.0,Y=698.0 (should be at cap-height 700?)

* uni030A (U+030A): X=184.0,Y=702.0 (should be at cap-height 700?)

* uni0327 (U+0327): X=99.0,Y=-248.0 (should be at descender -250?)

* breve (U+02D8): X=75.0,Y=698.0 (should be at cap-height 700?)

* ring (U+02DA): X=184.0,Y=702.0 (should be at cap-height 700?)

* cedilla (U+00B8): X=99.0,Y=-248.0 (should be at descender -250?)
</code></pre>
 [code: found-misalignments]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure dotted circle glyph is present and can attach marks. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/shaping.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>No dotted circle glyph present</p>
 [code: missing-dotted-circle]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure soft_dotted characters lose their dot when combined with marks that replace the dot. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/shaping.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The dot of soft dotted characters used in orthographies <em>must</em> disappear in the following strings: į̀ į́ į̂ į̃ į̄ į̌</p>
<p>The dot of soft dotted characters <em>should</em> disappear in other cases, for example: į̆ į̇ į̈ į̊ į̋ į̒ į̦̀ į̦́ į̦̂ į̦̃ į̦̄ į̦̆ į̦̇ į̦̈ į̦̊ į̦̋ į̦̌ į̦̒ į̧̀ į̧́</p>
<p>Your font fully covers the following languages that require the soft-dotted feature: Lithuanian (Latn, 2,357,094 speakers).</p>
<p>Your font does <em>not</em> cover the following languages that require the soft-dotted feature: Belarusian (Cyrl, 10,064,517 speakers), Ukrainian (Cyrl, 29,273,587 speakers), Kom (Latn, 360,685 speakers), Sar (Latn, 500,000 speakers), Basaa (Latn, 332,940 speakers), Zapotec (Latn, 490,000 speakers), Fur (Latn, 1,230,163 speakers), Ebira (Latn, 2,200,000 speakers), Kpelle, Guinea (Latn, 622,000 speakers), Bafut (Latn, 158,146 speakers), Southern Kisi (Latn, 360,000 speakers), Ma’di (Latn, 584,000 speakers), Ejagham (Latn, 120,000 speakers), Lugbara (Latn, 2,200,000 speakers), Ngbaka (Latn, 1,020,000 speakers), Mango (Latn, 77,000 speakers), Mfumte (Latn, 79,000 speakers), Vute (Latn, 21,000 speakers), Aghem (Latn, 38,843 speakers), Dii (Latn, 71,000 speakers), Igbo (Latn, 27,823,640 speakers), Nateni (Latn, 100,000 speakers), Avokaya (Latn, 100,000 speakers), Yala (Latn, 200,000 speakers), South Central Banda (Latn, 244,000 speakers), Ekpeye (Latn, 226,000 speakers), Koonzime (Latn, 40,000 speakers), Bete-Bendi (Latn, 100,000 speakers), Gulay (Latn, 250,478 speakers), Dutch (Latn, 31,709,104 speakers), Nzakara (Latn, 50,000 speakers), Ijo, Southeast (Latn, 2,471,000 speakers), Navajo (Latn, 166,319 speakers), Mundani (Latn, 34,000 speakers), Dan (Latn, 1,099,244 speakers), Cicipu (Latn, 44,000 speakers), Makaa (Latn, 221,000 speakers).</p>
 [code: soft-dotted]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check for codepoints not covered by METADATA subsets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.subsets.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The following codepoints supported by the font are not covered by
any subsets defined in the font's metadata file, and will never
be served. You can solve this by either manually adding additional
subset declarations to METADATA.pb, or by editing the glyphset
definitions.</p>
<ul>
<li>U+02C7 CARON: try adding one of: yi, canadian-aboriginal, tifinagh</li>
<li>U+02D8 BREVE: try adding one of: yi, canadian-aboriginal</li>
<li>U+02D9 DOT ABOVE: try adding one of: yi, canadian-aboriginal</li>
<li>U+02DB OGONEK: try adding one of: yi, canadian-aboriginal</li>
<li>U+02DD DOUBLE ACUTE ACCENT: not included in any glyphset definition</li>
<li>U+0302 COMBINING CIRCUMFLEX ACCENT: try adding one of: math, coptic, cherokee, tifinagh</li>
<li>U+0306 COMBINING BREVE: try adding one of: tifinagh, old-permic</li>
<li>U+0307 COMBINING DOT ABOVE: try adding one of: coptic, math, tai-le, tifinagh, syriac, canadian-aboriginal, malayalam, old-permic</li>
<li>U+030A COMBINING RING ABOVE: try adding syriac</li>
<li>U+030B COMBINING DOUBLE ACUTE ACCENT: try adding one of: cherokee, osage</li>
<li>U+030C COMBINING CARON: try adding one of: cherokee, tai-le</li>
<li>U+0312 COMBINING TURNED COMMA ABOVE: not included in any glyphset definition</li>
<li>U+0326 COMBINING COMMA BELOW: not included in any glyphset definition</li>
<li>U+0327 COMBINING CEDILLA: not included in any glyphset definition</li>
<li>U+0328 COMBINING OGONEK: not included in any glyphset definition</li>
<li>U+0335 COMBINING SHORT STROKE OVERLAY: not included in any glyphset definition</li>
<li>U+0336 COMBINING LONG STROKE OVERLAY: not included in any glyphset definition</li>
<li>U+0394 GREEK CAPITAL LETTER DELTA: try adding one of: math, greek, elbasan</li>
<li>U+03A9 GREEK CAPITAL LETTER OMEGA: try adding one of: math, greek, elbasan</li>
<li>U+03BC GREEK SMALL LETTER MU: try adding one of: math, greek</li>
<li>U+03C0 GREEK SMALL LETTER PI: try adding one of: math, yi, greek</li>
<li>U+1EBC LATIN CAPITAL LETTER E WITH TILDE: try adding vietnamese</li>
<li>U+1EBD LATIN SMALL LETTER E WITH TILDE: try adding vietnamese</li>
<li>U+2000 EN QUAD: not included in any glyphset definition</li>
<li>U+2001 EM QUAD: not included in any glyphset definition</li>
<li>U+2003 EM SPACE: try adding nushu</li>
<li>U+2004 THREE-PER-EM SPACE: not included in any glyphset definition</li>
<li>U+2005 FOUR-PER-EM SPACE: not included in any glyphset definition</li>
<li>U+2006 SIX-PER-EM SPACE: not included in any glyphset definition</li>
<li>U+2007 FIGURE SPACE: not included in any glyphset definition</li>
<li>U+2008 PUNCTUATION SPACE: not included in any glyphset definition</li>
<li>U+200A HAIR SPACE: not included in any glyphset definition</li>
<li>U+2021 DOUBLE DAGGER: try adding adlam</li>
<li>U+202F NARROW NO-BREAK SPACE: try adding one of: mongolian, yi</li>
<li>U+2030 PER MILLE SIGN: try adding adlam</li>
<li>U+205F MEDIUM MATHEMATICAL SPACE: not included in any glyphset definition</li>
<li>U+2070 SUPERSCRIPT ZERO: not included in any glyphset definition</li>
<li>U+2075 SUPERSCRIPT FIVE: not included in any glyphset definition</li>
<li>U+2076 SUPERSCRIPT SIX: not included in any glyphset definition</li>
<li>U+2077 SUPERSCRIPT SEVEN: not included in any glyphset definition</li>
<li>U+2078 SUPERSCRIPT EIGHT: not included in any glyphset definition</li>
<li>U+2079 SUPERSCRIPT NINE: not included in any glyphset definition</li>
<li>U+2080 SUBSCRIPT ZERO: not included in any glyphset definition</li>
<li>U+2081 SUBSCRIPT ONE: not included in any glyphset definition</li>
<li>U+2082 SUBSCRIPT TWO: not included in any glyphset definition</li>
<li>U+2083 SUBSCRIPT THREE: not included in any glyphset definition</li>
<li>U+2084 SUBSCRIPT FOUR: not included in any glyphset definition</li>
<li>U+2085 SUBSCRIPT FIVE: not included in any glyphset definition</li>
<li>U+2086 SUBSCRIPT SIX: not included in any glyphset definition</li>
<li>U+2087 SUBSCRIPT SEVEN: not included in any glyphset definition</li>
<li>U+2088 SUBSCRIPT EIGHT: not included in any glyphset definition</li>
<li>U+2089 SUBSCRIPT NINE: not included in any glyphset definition</li>
<li>U+2126 OHM SIGN: not included in any glyphset definition</li>
<li>U+212E ESTIMATED SYMBOL: not included in any glyphset definition</li>
<li>U+2150 VULGAR FRACTION ONE SEVENTH: not included in any glyphset definition</li>
<li>U+2151 VULGAR FRACTION ONE NINTH: not included in any glyphset definition</li>
<li>U+2152 VULGAR FRACTION ONE TENTH: not included in any glyphset definition</li>
<li>U+2153 VULGAR FRACTION ONE THIRD: not included in any glyphset definition</li>
<li>U+2154 VULGAR FRACTION TWO THIRDS: not included in any glyphset definition</li>
<li>U+2155 VULGAR FRACTION ONE FIFTH: not included in any glyphset definition</li>
<li>U+2156 VULGAR FRACTION TWO FIFTHS: not included in any glyphset definition</li>
<li>U+2157 VULGAR FRACTION THREE FIFTHS: not included in any glyphset definition</li>
<li>U+2158 VULGAR FRACTION FOUR FIFTHS: not included in any glyphset definition</li>
<li>U+2159 VULGAR FRACTION ONE SIXTH: not included in any glyphset definition</li>
<li>U+215A VULGAR FRACTION FIVE SIXTHS: not included in any glyphset definition</li>
<li>U+215B VULGAR FRACTION ONE EIGHTH: not included in any glyphset definition</li>
<li>U+215C VULGAR FRACTION THREE EIGHTHS: not included in any glyphset definition</li>
<li>U+215D VULGAR FRACTION FIVE EIGHTHS: not included in any glyphset definition</li>
<li>U+215E VULGAR FRACTION SEVEN EIGHTHS: not included in any glyphset definition</li>
<li>U+215F FRACTION NUMERATOR ONE: not included in any glyphset definition</li>
<li>U+2189 VULGAR FRACTION ZERO THIRDS: not included in any glyphset definition</li>
<li>U+2190 LEFTWARDS ARROW: try adding one of: math, symbols</li>
<li>U+2192 RIGHTWARDS ARROW: try adding one of: math, symbols</li>
<li>U+2194 LEFT RIGHT ARROW: try adding one of: math, symbols</li>
<li>U+2195 UP DOWN ARROW: try adding one of: math, symbols</li>
<li>U+2196 NORTH WEST ARROW: try adding one of: math, symbols</li>
<li>U+2197 NORTH EAST ARROW: try adding one of: math, symbols</li>
<li>U+2198 SOUTH EAST ARROW: try adding one of: math, symbols</li>
<li>U+2199 SOUTH WEST ARROW: try adding one of: math, symbols</li>
<li>U+2202 PARTIAL DIFFERENTIAL: try adding math</li>
<li>U+2206 INCREMENT: try adding math</li>
<li>U+220F N-ARY PRODUCT: try adding math</li>
<li>U+2211 N-ARY SUMMATION: try adding math</li>
<li>U+221A SQUARE ROOT: try adding math</li>
<li>U+221E INFINITY: try adding math</li>
<li>U+222B INTEGRAL: try adding math</li>
<li>U+2248 ALMOST EQUAL TO: try adding math</li>
<li>U+2260 NOT EQUAL TO: try adding math</li>
<li>U+2264 LESS-THAN OR EQUAL TO: try adding math</li>
<li>U+2265 GREATER-THAN OR EQUAL TO: try adding math</li>
<li>U+25CA LOZENGE: try adding one of: math, symbols</li>
<li>U+FB01 LATIN SMALL LIGATURE FI: not included in any glyphset definition</li>
</ul>
<p>Or you can add the above codepoints to one of the subsets supported by the font: <code>latin</code>, <code>latin-ext</code></p>
 [code: unreachable-subsetting]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Is there kerning info for non-ligated sequences? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.gpos.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>GPOS table lacks kerning info for the following non-ligated sequences:</p>
<pre><code>- f + i
</code></pre>
 [code: lacks-kern-info]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Are there caret positions declared for every ligature? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.gdef.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>This font lacks caret position values for ligature glyphs on its GDEF table.</p>
 [code: lacks-caret-pos]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure fonts have ScriptLangTags declared on the 'meta' table. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.meta.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>This font file does not have a 'meta' table.</p>
 [code: lacks-meta-table]



</div>
</details>
</div>
</details>

<details><summary>[13] AlbertSans-Roman[wdth,wght].ttf</summary>
<div>
<details>
    <summary>🔥 <b>FAIL</b> Ensure the font supports case swapping for all its glyphs. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.glyphset.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>The following glyphs lack their case-swapping counterparts:</p>
<table>
<thead>
<tr>
<th align="left">Glyph present in the font</th>
<th align="left">Missing case-swapping counterpart</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left">U+A732: LATIN CAPITAL LETTER AA</td>
<td align="left">U+A733: LATIN SMALL LETTER AA</td>
</tr>
</tbody>
</table>
 [code: missing-case-counterparts]



</div>
</details>

<details>
    <summary>🔥 <b>FAIL</b> Shapes languages in all GF glyphsets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.glyphset.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>GF_Latin_Core glyphset:</p>
<table>
<thead>
<tr>
<th align="left">Language</th>
<th align="left">FAIL messages</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left">nl_Latn (Dutch)</td>
<td align="left">Shaper didn't attach acutecomb to J</td>
</tr>
<tr>
<td align="left">^</td>
<td align="left">Shaper didn't attach acutecomb to uni0237</td>
</tr>
</tbody>
</table>
 [code: failed-language-shaping]



</div>
</details>

<details>
    <summary>🔥 <b>FAIL</b> Checking file is named canonically. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.html#"></a></summary>
    <div>







* 🔥 **FAIL** <p>Expected &quot;AlbertSans[wdth,wght].ttf. Got AlbertSans-Roman[wdth,wght].ttf.</p>
 [code: bad-filename]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check math signs have the same width. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The most common width is 596 among a set of 2 math glyphs.
The following math glyphs have a different width, though:</p>
<p>Width = 391:
greater, less</p>
<p>Width = 637:
equal, approxequal</p>
<p>Width = 665:
logicalnot</p>
<p>Width = 623:
plusminus</p>
<p>Width = 525:
multiply</p>
<p>Width = 491:
minus</p>
<p>Width = 645:
notequal</p>
<p>Width = 467:
greaterequal, lessequal</p>
 [code: width-outliers]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Does the font contain a soft hyphen? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.glyphset.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>This font has a 'Soft Hyphen' character.</p>
 [code: softhyphen]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check font contains no unreachable glyphs <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/universal.glyphset.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The following glyphs could not be reached by codepoint or substitution rules:</p>
<pre><code>- uni030C.alt
</code></pre>
 [code: unreachable-glyphs]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Are there any misaligned on-curve points? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/outline.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The following glyphs have on-curve points which have potentially incorrect y coordinates:</p>
<pre><code>* Iogonek (U+012E): X=181.0,Y=1.0 (should be at baseline 0?)

* Lcaron (U+013D): X=365.0,Y=701.0 (should be at cap-height 700?)

* Lcaron (U+013D): X=471.0,Y=701.0 (should be at cap-height 700?)

* uni013B (U+013B): X=365.0,Y=701.0 (should be at cap-height 700?)

* uni013B (U+013B): X=471.0,Y=701.0 (should be at cap-height 700?)

* uni0162 (U+0162): X=402.0,Y=-248.0 (should be at descender -250?)

* uni013B.loclMAH: X=365.0,Y=701.0 (should be at cap-height 700?)

* uni013B.loclMAH: X=471.0,Y=701.0 (should be at cap-height 700?)

* abreve (U+0103): X=112.0,Y=698.0 (should be at cap-height 700?)

* aring (U+00E5): X=256.0,Y=702.0 (should be at cap-height 700?)

* ccedilla (U+00E7): X=384.0,Y=-248.0 (should be at descender -250?)

* ebreve (U+0115): X=138.0,Y=698.0 (should be at cap-height 700?)

* gbreve (U+011F): X=145.0,Y=698.0 (should be at cap-height 700?)

* obreve (U+014F): X=149.0,Y=698.0 (should be at cap-height 700?)

* scedilla (U+015F): X=332.0,Y=-248.0 (should be at descender -250?)

* t (U+0074): X=287.5,Y=-1.0 (should be at baseline 0?)

* tcaron (U+0165): X=287.5,Y=-1.0 (should be at baseline 0?)

* uni0163 (U+0163): X=287.5,Y=-1.0 (should be at baseline 0?)

* uni0163 (U+0163): X=295.0,Y=-248.0 (should be at descender -250?)

* uni021B (U+021B): X=287.5,Y=-1.0 (should be at baseline 0?)

* ubreve (U+016D): X=128.0,Y=698.0 (should be at cap-height 700?)

* uring (U+016F): X=272.0,Y=702.0 (should be at cap-height 700?)

* comma.ss01: X=154.0,Y=1.0 (should be at baseline 0?)

* ampersand (U+0026): X=616.0,Y=-1.0 (should be at baseline 0?)

* turkishlira (U+20BA): X=309.5,Y=-1.0 (should be at baseline 0?)

* arrowup (U+2191): X=351.0,Y=-1.0 (should be at baseline 0?)

* arrowup (U+2191): X=260.0,Y=-1.0 (should be at baseline 0?)

* uni0306 (U+0306): X=0.0,Y=698.0 (should be at cap-height 700?)

* uni030A (U+030A): X=108.0,Y=702.0 (should be at cap-height 700?)

* uni0327 (U+0327): X=183.0,Y=-248.0 (should be at descender -250?)

* breve (U+02D8): X=0.0,Y=698.0 (should be at cap-height 700?)

* ring (U+02DA): X=108.0,Y=702.0 (should be at cap-height 700?)

* cedilla (U+00B8): X=183.0,Y=-248.0 (should be at descender -250?)
</code></pre>
 [code: found-misalignments]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure dotted circle glyph is present and can attach marks. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/shaping.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>No dotted circle glyph present</p>
 [code: missing-dotted-circle]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure soft_dotted characters lose their dot when combined with marks that replace the dot. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/shaping.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The dot of soft dotted characters used in orthographies <em>must</em> disappear in the following strings: į̀ į́ į̂ į̃ į̄ į̌</p>
<p>The dot of soft dotted characters <em>should</em> disappear in other cases, for example: į̆ į̇ į̈ į̊ į̋ į̒ į̦̀ į̦́ į̦̂ į̦̃ į̦̄ į̦̆ į̦̇ į̦̈ į̦̊ į̦̋ į̦̌ į̦̒ į̧̀ į̧́</p>
<p>Your font fully covers the following languages that require the soft-dotted feature: Lithuanian (Latn, 2,357,094 speakers).</p>
<p>Your font does <em>not</em> cover the following languages that require the soft-dotted feature: Belarusian (Cyrl, 10,064,517 speakers), Ukrainian (Cyrl, 29,273,587 speakers), Kom (Latn, 360,685 speakers), Sar (Latn, 500,000 speakers), Basaa (Latn, 332,940 speakers), Zapotec (Latn, 490,000 speakers), Fur (Latn, 1,230,163 speakers), Ebira (Latn, 2,200,000 speakers), Kpelle, Guinea (Latn, 622,000 speakers), Bafut (Latn, 158,146 speakers), Southern Kisi (Latn, 360,000 speakers), Ma’di (Latn, 584,000 speakers), Ejagham (Latn, 120,000 speakers), Lugbara (Latn, 2,200,000 speakers), Ngbaka (Latn, 1,020,000 speakers), Mango (Latn, 77,000 speakers), Mfumte (Latn, 79,000 speakers), Vute (Latn, 21,000 speakers), Aghem (Latn, 38,843 speakers), Dii (Latn, 71,000 speakers), Igbo (Latn, 27,823,640 speakers), Nateni (Latn, 100,000 speakers), Avokaya (Latn, 100,000 speakers), Yala (Latn, 200,000 speakers), South Central Banda (Latn, 244,000 speakers), Ekpeye (Latn, 226,000 speakers), Koonzime (Latn, 40,000 speakers), Bete-Bendi (Latn, 100,000 speakers), Gulay (Latn, 250,478 speakers), Dutch (Latn, 31,709,104 speakers), Nzakara (Latn, 50,000 speakers), Ijo, Southeast (Latn, 2,471,000 speakers), Navajo (Latn, 166,319 speakers), Mundani (Latn, 34,000 speakers), Dan (Latn, 1,099,244 speakers), Cicipu (Latn, 44,000 speakers), Makaa (Latn, 221,000 speakers).</p>
 [code: soft-dotted]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Check for codepoints not covered by METADATA subsets. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.subsets.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>The following codepoints supported by the font are not covered by
any subsets defined in the font's metadata file, and will never
be served. You can solve this by either manually adding additional
subset declarations to METADATA.pb, or by editing the glyphset
definitions.</p>
<ul>
<li>U+02C7 CARON: try adding one of: yi, canadian-aboriginal, tifinagh</li>
<li>U+02D8 BREVE: try adding one of: yi, canadian-aboriginal</li>
<li>U+02D9 DOT ABOVE: try adding one of: yi, canadian-aboriginal</li>
<li>U+02DB OGONEK: try adding one of: yi, canadian-aboriginal</li>
<li>U+02DD DOUBLE ACUTE ACCENT: not included in any glyphset definition</li>
<li>U+0302 COMBINING CIRCUMFLEX ACCENT: try adding one of: math, coptic, cherokee, tifinagh</li>
<li>U+0306 COMBINING BREVE: try adding one of: tifinagh, old-permic</li>
<li>U+0307 COMBINING DOT ABOVE: try adding one of: coptic, math, tai-le, tifinagh, syriac, canadian-aboriginal, malayalam, old-permic</li>
<li>U+030A COMBINING RING ABOVE: try adding syriac</li>
<li>U+030B COMBINING DOUBLE ACUTE ACCENT: try adding one of: cherokee, osage</li>
<li>U+030C COMBINING CARON: try adding one of: cherokee, tai-le</li>
<li>U+0312 COMBINING TURNED COMMA ABOVE: not included in any glyphset definition</li>
<li>U+0326 COMBINING COMMA BELOW: not included in any glyphset definition</li>
<li>U+0327 COMBINING CEDILLA: not included in any glyphset definition</li>
<li>U+0328 COMBINING OGONEK: not included in any glyphset definition</li>
<li>U+0335 COMBINING SHORT STROKE OVERLAY: not included in any glyphset definition</li>
<li>U+0336 COMBINING LONG STROKE OVERLAY: not included in any glyphset definition</li>
<li>U+0394 GREEK CAPITAL LETTER DELTA: try adding one of: math, greek, elbasan</li>
<li>U+03A9 GREEK CAPITAL LETTER OMEGA: try adding one of: math, greek, elbasan</li>
<li>U+03BC GREEK SMALL LETTER MU: try adding one of: math, greek</li>
<li>U+03C0 GREEK SMALL LETTER PI: try adding one of: math, yi, greek</li>
<li>U+1EBC LATIN CAPITAL LETTER E WITH TILDE: try adding vietnamese</li>
<li>U+1EBD LATIN SMALL LETTER E WITH TILDE: try adding vietnamese</li>
<li>U+2000 EN QUAD: not included in any glyphset definition</li>
<li>U+2001 EM QUAD: not included in any glyphset definition</li>
<li>U+2003 EM SPACE: try adding nushu</li>
<li>U+2004 THREE-PER-EM SPACE: not included in any glyphset definition</li>
<li>U+2005 FOUR-PER-EM SPACE: not included in any glyphset definition</li>
<li>U+2006 SIX-PER-EM SPACE: not included in any glyphset definition</li>
<li>U+2007 FIGURE SPACE: not included in any glyphset definition</li>
<li>U+2008 PUNCTUATION SPACE: not included in any glyphset definition</li>
<li>U+200A HAIR SPACE: not included in any glyphset definition</li>
<li>U+2021 DOUBLE DAGGER: try adding adlam</li>
<li>U+202F NARROW NO-BREAK SPACE: try adding one of: mongolian, yi</li>
<li>U+2030 PER MILLE SIGN: try adding adlam</li>
<li>U+205F MEDIUM MATHEMATICAL SPACE: not included in any glyphset definition</li>
<li>U+2070 SUPERSCRIPT ZERO: not included in any glyphset definition</li>
<li>U+2075 SUPERSCRIPT FIVE: not included in any glyphset definition</li>
<li>U+2076 SUPERSCRIPT SIX: not included in any glyphset definition</li>
<li>U+2077 SUPERSCRIPT SEVEN: not included in any glyphset definition</li>
<li>U+2078 SUPERSCRIPT EIGHT: not included in any glyphset definition</li>
<li>U+2079 SUPERSCRIPT NINE: not included in any glyphset definition</li>
<li>U+2080 SUBSCRIPT ZERO: not included in any glyphset definition</li>
<li>U+2081 SUBSCRIPT ONE: not included in any glyphset definition</li>
<li>U+2082 SUBSCRIPT TWO: not included in any glyphset definition</li>
<li>U+2083 SUBSCRIPT THREE: not included in any glyphset definition</li>
<li>U+2084 SUBSCRIPT FOUR: not included in any glyphset definition</li>
<li>U+2085 SUBSCRIPT FIVE: not included in any glyphset definition</li>
<li>U+2086 SUBSCRIPT SIX: not included in any glyphset definition</li>
<li>U+2087 SUBSCRIPT SEVEN: not included in any glyphset definition</li>
<li>U+2088 SUBSCRIPT EIGHT: not included in any glyphset definition</li>
<li>U+2089 SUBSCRIPT NINE: not included in any glyphset definition</li>
<li>U+2126 OHM SIGN: not included in any glyphset definition</li>
<li>U+212E ESTIMATED SYMBOL: not included in any glyphset definition</li>
<li>U+2150 VULGAR FRACTION ONE SEVENTH: not included in any glyphset definition</li>
<li>U+2151 VULGAR FRACTION ONE NINTH: not included in any glyphset definition</li>
<li>U+2152 VULGAR FRACTION ONE TENTH: not included in any glyphset definition</li>
<li>U+2153 VULGAR FRACTION ONE THIRD: not included in any glyphset definition</li>
<li>U+2154 VULGAR FRACTION TWO THIRDS: not included in any glyphset definition</li>
<li>U+2155 VULGAR FRACTION ONE FIFTH: not included in any glyphset definition</li>
<li>U+2156 VULGAR FRACTION TWO FIFTHS: not included in any glyphset definition</li>
<li>U+2157 VULGAR FRACTION THREE FIFTHS: not included in any glyphset definition</li>
<li>U+2158 VULGAR FRACTION FOUR FIFTHS: not included in any glyphset definition</li>
<li>U+2159 VULGAR FRACTION ONE SIXTH: not included in any glyphset definition</li>
<li>U+215A VULGAR FRACTION FIVE SIXTHS: not included in any glyphset definition</li>
<li>U+215B VULGAR FRACTION ONE EIGHTH: not included in any glyphset definition</li>
<li>U+215C VULGAR FRACTION THREE EIGHTHS: not included in any glyphset definition</li>
<li>U+215D VULGAR FRACTION FIVE EIGHTHS: not included in any glyphset definition</li>
<li>U+215E VULGAR FRACTION SEVEN EIGHTHS: not included in any glyphset definition</li>
<li>U+215F FRACTION NUMERATOR ONE: not included in any glyphset definition</li>
<li>U+2189 VULGAR FRACTION ZERO THIRDS: not included in any glyphset definition</li>
<li>U+2190 LEFTWARDS ARROW: try adding one of: math, symbols</li>
<li>U+2192 RIGHTWARDS ARROW: try adding one of: math, symbols</li>
<li>U+2194 LEFT RIGHT ARROW: try adding one of: math, symbols</li>
<li>U+2195 UP DOWN ARROW: try adding one of: math, symbols</li>
<li>U+2196 NORTH WEST ARROW: try adding one of: math, symbols</li>
<li>U+2197 NORTH EAST ARROW: try adding one of: math, symbols</li>
<li>U+2198 SOUTH EAST ARROW: try adding one of: math, symbols</li>
<li>U+2199 SOUTH WEST ARROW: try adding one of: math, symbols</li>
<li>U+2202 PARTIAL DIFFERENTIAL: try adding math</li>
<li>U+2206 INCREMENT: try adding math</li>
<li>U+220F N-ARY PRODUCT: try adding math</li>
<li>U+2211 N-ARY SUMMATION: try adding math</li>
<li>U+221A SQUARE ROOT: try adding math</li>
<li>U+221E INFINITY: try adding math</li>
<li>U+222B INTEGRAL: try adding math</li>
<li>U+2248 ALMOST EQUAL TO: try adding math</li>
<li>U+2260 NOT EQUAL TO: try adding math</li>
<li>U+2264 LESS-THAN OR EQUAL TO: try adding math</li>
<li>U+2265 GREATER-THAN OR EQUAL TO: try adding math</li>
<li>U+25CA LOZENGE: try adding one of: math, symbols</li>
<li>U+FB01 LATIN SMALL LIGATURE FI: not included in any glyphset definition</li>
</ul>
<p>Or you can add the above codepoints to one of the subsets supported by the font: <code>latin</code>, <code>latin-ext</code></p>
 [code: unreachable-subsetting]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Is there kerning info for non-ligated sequences? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.gpos.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>GPOS table lacks kerning info for the following non-ligated sequences:</p>
<pre><code>- f + i
</code></pre>
 [code: lacks-kern-info]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Are there caret positions declared for every ligature? <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.gdef.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>This font lacks caret position values for ligature glyphs on its GDEF table.</p>
 [code: lacks-caret-pos]



</div>
</details>

<details>
    <summary>⚠️ <b>WARN</b> Ensure fonts have ScriptLangTags declared on the 'meta' table. <a href="https://fontbakery.readthedocs.io/en/stable/fontbakery/checks/googlefonts.meta.html#"></a></summary>
    <div>







* ⚠️ **WARN** <p>This font file does not have a 'meta' table.</p>
 [code: lacks-meta-table]



</div>
</details>
</div>
</details>




### Summary

| 💥 ERROR | ☠ FATAL | 🔥 FAIL | ⚠️ WARN | ⏩ SKIP | ℹ️ INFO | ✅ PASS | 🔎 DEBUG | 
| ---|---|---|---|---|---|---|---|
| 0 | 0 | 8 | 22 | 181 | 15 | 260 | 0 | 
| 0% | 0% | 2% | 5% | 37% | 3% | 53% | 0% | 



**Note:** The following loglevels were omitted in this report:


* SKIP
* INFO
* PASS
* DEBUG
