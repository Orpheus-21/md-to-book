---
name: md-to-book
description: Turn a folder of Markdown files (essays, articles, chapters) into a typeset book PDF, for the screen or for print on KDP. Use this skill when the user has Markdown files, in any folder and not only an Obsidian vault, and wants a book, a PDF book, a print-ready PDF, a typeset collection, or "my essays as a book". The skill asks about the output and the printer, builds the book with Typst, looks at the pages, fixes layout faults, and checks print books against the KDP paperback rules.
---

# md-to-book

The user has a folder of Markdown files. The user wants one finished book. You ask a few questions, build the book, look at the pages, fix faults, and report.

The scripts are in the folder that holds this file. Write `SKILL_DIR` for that folder in the commands below.

## Rules

* Never change the words of the user. Do not edit the Markdown files. Do not shorten, correct, or reorder the text. If a file has a text fault, tell the user.
* Never write the title, the author name, or the year from a guess. Ask.
* Say the truth about what you checked. Say what you did not check.
* This skill does not make EPUB, hardcover books, covers, indexes, or bibliographies. If the user asks for one, say so and offer what the skill can make.

## Step 1: Check the tools

1. Run `typst --version`. If the command fails, tell the user to install Typst from https://typst.app. Stop.
2. For a print book, run `pdfinfo -v`. If the command fails, tell the user to install the poppler package. The print check needs it.

## Step 2: Ask the questions

Find the folder. If the user did not name it, ask for it.

Read `SKILL_DIR/questions.md`. Ask the questions in it, one at a time. Each question has a default. Do not ask a question that the user already answered.

Ask for the language of the essays. The default is `en`. Use the answer for `--lang`.

## Step 3: Build

1. Run `python3 SKILL_DIR/build.py FOLDER --list`. Show the order. Get the answer to the order question.
2. Run the build with the flags from the table in `questions.md`. Example for a KDP paperback:

```
python3 SKILL_DIR/build.py FOLDER --title "T" --author "A" --trim 6x9 --print
```

3. Check the exit code. If it is not 0, read the error text, find the cause, and fix it. Do not report a build that failed. The script deletes the old `book.pdf` before each build, so a `book.pdf` that exists is new.
4. Read every `warning:` line. An image that is remote or missing is replaced by its alt text. Tell the user.

The script writes `book.pdf` and a `build/` folder in the essay folder. Tell the user.

## Step 4: Look at the pages

A build that compiles can still look wrong. Look before you report.

1. Run the build again with `--preview PAGES`. Render these pages: the first 6, the first page of two other chapters (use the contents page to find them), the last 2, and any page with a table, an image, or code. Render 12 pages at most.
2. Read the PNG files in `FOLDER/build/preview/`.
3. Look for these faults:
   * A heading alone at the bottom of a page.
   * Text outside the margins, or a table wider than the page.
   * An image that is cut or too large.
   * A footnote on a later page than its reference.
   * A chapter that starts on a left-hand page.
   * A page number or running head on a blank page.
   * A wrong title, an empty chapter, or text that is missing.
4. Do not report a fault that you did not see. Do not call a page good that you did not read.

## Step 5: Fix faults

Fix in this order. Stop at the first fix that works.

1. Change a build flag: `--font-size`, `--trim`, `--bleed`, or `--lang`.
2. Copy `SKILL_DIR/template.typ` into the essay folder. Edit the copy. Build with `--template FOLDER/template.typ`. Never edit the template in `SKILL_DIR`.
3. If the fault is in the Markdown, tell the user. Do not edit the file.

After a fix, build again, run the look step again, and check the exit code. Make 3 fix rounds at most. If a fault is still there, tell the user what it is. A footnote that moves to the next page because the page is full is a Typst rule. Report it. Do not fight it.

## Step 6: Check a print book

The option `--print` runs the print check. Read every line of the report.

* `FAIL`: fix it. Run the build again.
* `WARN`: tell the user. A low image resolution needs a better image from the user.
* The check covers KDP paperback rules only. For another printer, say that the margin check does not apply.

The check does not replace the KDP previewer. Tell the user to use both before an upload.

## Step 7: Report

Tell the user, in short sentences:

* The path of `book.pdf` and the page count.
* The trim size, and for print the inside margin that the script chose.
* The result of the print check, line by line for each `FAIL` and `WARN`.
* The faults that you fixed and the faults that remain.
* What you did not check: the cover, the text of the essays, the color, and the printer rules other than KDP.

## Limits

* Markdown tags that look like HTML, for example `<angle>`, can disappear. Tell the user if you see this.
* A second `#` heading in an essay starts a new chapter.
* Typst bundles the font `Libertinus Serif`. The default font covers Latin text. For other scripts, the user must name a font in a copied template.
