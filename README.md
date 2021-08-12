# The Albert Sans Font Project 

[![][Fontbakery]](https://usted.github.io/Albert-Sans/fontbakery-report.html)
[![][Universal]](https://usted.github.io/Albert-Sans/fontbakery-report.html)
[![][GF Profile]](https://usted.github.io/Albert-Sans/fontbakery-report.html)
[![][Outline Correctness]](https://usted.github.io/Albert-Sans/fontbakery-report.html)
[![][Shaping]](https://usted.github.io/Albert-Sans/fontbakery-report.html)

[Fontbakery]: https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fusted%2FAlbert-Sans%2Fgh-pages%2Fbadges%2Foverall.json
[GF Profile]: https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fusted%2FAlbert-Sans%2Fgh-pages%2Fbadges%2FGoogleFonts.json
[Outline Correctness]: https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fusted%2FAlbert-Sans%2Fgh-pages%2Fbadges%2FOutlineCorrectnessChecks.json
[Shaping]: https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fusted%2FAlbert-Sans%2Fgh-pages%2Fbadges%2FShapingChecks.json
[Universal]: https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fusted%2FAlbert-Sans%2Fgh-pages%2Fbadges%2FUniversal.json

Albert Sans is a modern geometric sans serif family. 
It is inspired by the type-characteristics made by scandinavian architects and designers in the beginning of the 20th century.
Architects and designers like Knud V. Engelhardt (1882-1931), Gunnar Biilmann Petersen (1897-1968) and Thorvald Bindesbøll (1846-1908) who contributed to the foundation of scandinavian typedesign.

Designed by the Danish type designer Andreas Rasmussen, build on Latin portion of Poppins made by Jonny Pinhorn.

The Albert Sans family includes ten weights from Thin to Black and supports the Latin Extended glyph set and other western european languages.


![Sample Image](documentation/image1.png)

## Building

Fonts are built automatically by GitHub Actions - take a look in the "Actions" tab for the latest build.

If you want to build fonts manually on your own computer:

* `make build` will produce font files.
* `make test` will run [FontBakery](https://github.com/googlefonts/fontbakery)'s quality assurance tests.
* `make proof` will generate HTML proof files.

The proof files and QA tests are also available automatically via GitHub Actions - look at `https://usted.github.io/Albert-Sans`.

## Changelog

When you update your font (new version or new release), please report all notable changes here, with a date.
[Font Versioning](https://github.com/googlefonts/gf-docs/tree/main/Spec#font-versioning) is based on semver. 
Changelog example:

**12 Aug 2021. Version 1.00**
- Repository update

## License

This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is copied below, and is also available with a FAQ at
https://scripts.sil.org/OFL

## Repository Layout

This font repository structure is inspired by [Unified Font Repository v0.3](https://github.com/unified-font-repository/Unified-Font-Repository), modified for the Google Fonts workflow.