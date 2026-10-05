# md-to-book

md-to-book builds a typeset book PDF from a folder of Markdown essays.

## What it does

The script `build.py` reads every `.md` file in a folder. It puts the essays in reading order. It writes one Typst document and compiles it to `book.pdf`. The book has a title page, a copyright page, a table of contents, and one chapter for each essay. Each chapter starts on a right-hand page. The book has running heads and page numbers. Blank pages have neither.

The work is in progress. The planned parts are a print preflight check, a Claude Code skill file, and questions about the output and the printer.

## Requirements

* Python 3 and Typst. I tested Python 3.14 and Typst 0.15.1 on Linux. I did not test other systems.
* Internet access on the first build. Typst downloads the `cmarker` package, version 0.1.6.

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

## Configuration

The options of `build.py` are:

* `--list`: list the essays and stop.
* `--files`: the essay files, in order. The default is all `.md` files, in natural order. The file `2.md` comes before `10.md`.
* `--title`: the book title. The default is `Untitled`.
* `--author`: the author name. The default is empty.
* `--out`: the PDF file name. The default is `book.pdf`.
* `--preview`: a page range to render to PNG.

The page size and the margins are arguments of the `book` function in `template.typ`. The default page is 5.5 by 8.5 inches.

## How it works

The script skips `README.md`, hidden folders, and the `build/` folder. It removes YAML frontmatter from each essay. If an essay has no `#` heading, the script adds one. The title comes from the frontmatter or from the file name.

The script copies the cleaned essays and the local images to `build/` in the essay folder. It writes `build/main.typ` and `build/template.typ`. The `cmarker` package turns each essay into Typst content. The command `typst compile` makes the PDF.

An image that is remote or missing is replaced by its alt text. The script prints a warning.

## License

This project uses the GNU General Public License, version 3 or any later version. See the file `LICENSE`.
