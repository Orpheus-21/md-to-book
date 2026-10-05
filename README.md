# md-to-book

md-to-book builds a typeset book PDF from a folder of Markdown essays.

## What it does

The script `build.py` reads every `.md` file in a folder. It puts the essays in reading order. It writes one Typst document and compiles it to `book.pdf`. The book has a title page, a copyright page, a table of contents, and one chapter for each essay. Each chapter starts on a right-hand page. The book has running heads and page numbers. Blank pages have neither.

The script can also set the page size and the bleed, and it can check a print book against the KDP paperback rules. The work is in progress. The planned part is a Claude Code skill file.

## Requirements

* Python 3 and Typst. I tested Python 3.14 and Typst 0.15.1 on Linux. I did not test other systems.
* Internet access on the first build. Typst downloads the `cmarker` package, version 0.1.6.
* For the print check: the poppler tools `pdfinfo`, `pdffonts`, `pdftotext`, and `pdfimages`.

## Install

1. Install Typst. See https://typst.app for the method for your system.
2. Clone the repository:

```
git clone https://github.com/Orpheus-21/md-to-book.git
```

## Usage

List the essays in reading order:

```
python3 build.py ~/essays --list
```

Build the book. The script writes `book.pdf` in the essay folder:

```
python3 build.py ~/essays --title "My Essays" --author "A. Writer"
```

Build in an exact order:

```
python3 build.py ~/essays --title "My Essays" --author "A. Writer" --files b.md a.md
```

Render pages to PNG files, to check the layout:

```
python3 build.py ~/essays --title "My Essays" --author "A. Writer" --preview 1-6
```

The PNG files go to `build/preview/` in the essay folder.

Build a 6 by 9 inch paperback for KDP, with the print check:

```
python3 build.py ~/essays --title "My Essays" --author "A. Writer" --trim 6x9 --print
```

The script prints the page count, the inside margin, and the report of the check. Each line of the report starts with `OK`, `WARN`, or `FAIL`. Fix every `FAIL` before you upload the book.

Check a PDF that you built earlier:

```
python3 preflight.py ~/essays/book.pdf --trim 6x9
```

The command exits with code 1 when a check fails.

## Configuration

The options of `build.py` are:

* `--list`: list the essays and stop.
* `--files`: the essay files, in order. The default is all `.md` files, in natural order. The file `2.md` comes before `10.md`.
* `--title`: the book title. The default is `Untitled`.
* `--author`: the author name. The default is empty.
* `--out`: the PDF file name. The default is `book.pdf`.
* `--preview`: a page range to render to PNG.
* `--trim`: the trim size. Use `6x9`, `5.5x8.5in`, `148x210mm`, `a4`, `a5`, or `a6`. The default is `5.5x8.5`.
* `--bleed`: extra paper on the top, bottom, and outer edges, for example `0.125in`. The default is `0pt`.
* `--font-size`: the size of the body text. The default is `11pt`.
* `--print`: set the inside margin from the KDP table for the page count, then run the print check. The inside margin is never less than 0.625 inches.

The margins are arguments of the `book` function in `template.typ`. The default inside margin is 0.875 inches. The default outside margin is 0.625 inches.

## How it works

The script skips `README.md`, hidden folders, and the `build/` folder. It removes YAML frontmatter from each essay. If an essay has no `#` heading, the script adds one. The title comes from the frontmatter or from the file name.

The script copies the cleaned essays and the local images to `build/` in the essay folder. It writes `build/main.typ` and `build/template.typ`. The `cmarker` package turns each essay into Typst content. The command `typst compile` makes the PDF.

An image that is remote or missing is replaced by its alt text. The script prints a warning.

The option `--print` builds the PDF again with the inside margin for the page count. The margin can change the page count, so the script repeats the build up to 4 times until the margin is stable. The script reads the page count with `typst query`.

The file `preflight.py` reads the PDF with the poppler tools. It checks the page count (24 to 828 pages), the page size, the embedded fonts, the blank pages, the margins, and the image resolution (300 ppi). The rules come from the KDP help pages for [trim, bleed, and margins](https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6) and for [images](https://kdp.amazon.com/en_US/help/topic/G202169030).

The file `questions.md` lists the questions to ask a user before a build. The file `test/test_preflight.py` tests the print check.

## License

This project uses the GNU General Public License, version 3 or any later version. See the file `LICENSE`.
