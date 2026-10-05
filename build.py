#!/usr/bin/env python3
"""Build a book PDF from a folder of Markdown essays.

  build.py DIR --list                      list the essays in reading order
  build.py DIR --title T --author A        build DIR/book.pdf
  build.py DIR ... --files b.md a.md       build in this exact order
"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def natural(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(p))]


def find_essays(root):
    skip = ("book", "build")
    return sorted((p for p in root.rglob("*.md")
                   if not any(x.startswith(".") or x in skip for x in p.relative_to(root).parts[:-1])
                   and p.stem != "README"), key=natural)


def clean(text, fallback):
    """Strip YAML frontmatter. Add a # title if the essay has none."""
    m = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta = m.group(1) if m else ""
    if m:
        text = text[m.end():]
    if not re.search(r"^# ", text, re.M):
        t = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", meta, re.M)
        text = f"# {t.group(1) if t else fallback}\n\n{text}"
    return text


def main():
    a = argparse.ArgumentParser()
    a.add_argument("dir")
    a.add_argument("--list", action="store_true")
    a.add_argument("--files", nargs="*")
    a.add_argument("--title", default="Untitled")
    a.add_argument("--author", default="")
    a.add_argument("--out", default="book.pdf")
    a = a.parse_args()

    root = Path(a.dir).resolve()
    files = [root / f for f in a.files] if a.files else find_essays(root)
    if not files:
        sys.exit(f"No .md files found in {root}")
    if a.list:
        for i, f in enumerate(files, 1):
            print(f"{i:2}. {f.relative_to(root)}")
        return

    build = root / "build"
    shutil.rmtree(build, ignore_errors=True)
    (build / "chapters").mkdir(parents=True)
    shutil.copy(HERE / "template.typ", build)
    lines = ['#import "@preview/cmarker:0.1.6"', '#import "template.typ": book',
             f'#show: book.with(title: "{a.title}", author: "{a.author}")']
    for i, f in enumerate(files, 1):
        name = f"chapters/{i:02}.md"
        fallback = re.sub(r"^\d+[-_. ]*", "", f.stem).replace("-", " ").replace("_", " ").title()
        (build / name).write_text(clean(f.read_text(encoding="utf-8"), fallback), encoding="utf-8")
        lines.append(f'#cmarker.render(read("{name}"))')
    (build / "main.typ").write_text("\n".join(lines) + "\n", encoding="utf-8")

    out = root / a.out
    r = subprocess.run(["typst", "compile", "--root", str(build), str(build / "main.typ"), str(out)])
    sys.exit(r.returncode)


main()
