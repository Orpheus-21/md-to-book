#!/usr/bin/env python3
"""Build a book PDF from a folder of Markdown essays.

  build.py DIR --list                      list the essays in reading order
  build.py DIR --title T --author A        build DIR/book.pdf
  build.py DIR ... --files b.md a.md       build in this exact order
"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path
from urllib.parse import unquote

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


IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)([^)]*)\)")


def fix_images(text, src_dir, build, n):
    """Copy local images into the build folder. Replace the rest with the alt text."""
    def sub(m):
        alt, path, rest = m.groups()
        f = src_dir / unquote(path)
        if re.match(r"\w+://", path) or not f.is_file():
            print(f"warning: image not used (remote or missing): {path}", file=sys.stderr)
            return alt
        dest = Path("assets") / f"{n:02}-{f.name}"
        (build / dest).parent.mkdir(exist_ok=True)
        shutil.copy(f, build / dest)
        return f"![{alt}]({dest}{rest})"
    return IMG.sub(sub, text)


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main():
    a = argparse.ArgumentParser()
    a.add_argument("dir")
    a.add_argument("--list", action="store_true")
    a.add_argument("--files", nargs="*")
    a.add_argument("--title", default="Untitled")
    a.add_argument("--author", default="")
    a.add_argument("--out", default="book.pdf")
    a.add_argument("--preview", metavar="PAGES", help="also render these pages to build/preview/, e.g. 1-6")
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
             f'#show: book.with(title: "{esc(a.title)}", author: "{esc(a.author)}")',
             '#let scope = (image: (source, alt: none, ..args) => image(source, alt: alt, ..args))']
    for i, f in enumerate(files, 1):
        name = f"chapters/{i:02}.md"
        fallback = re.sub(r"^\d+[-_. ]*", "", f.stem).replace("-", " ").replace("_", " ").title()
        text = fix_images(clean(f.read_text(encoding="utf-8"), fallback), f.parent, build, i)
        (build / name).write_text(text, encoding="utf-8")
        lines.append(f'#cmarker.render(read("{name}"), scope: scope)')
    (build / "main.typ").write_text("\n".join(lines) + "\n", encoding="utf-8")

    out = root / a.out
    r = subprocess.run(["typst", "compile", "--root", str(build), str(build / "main.typ"), str(out)])
    if r.returncode == 0 and a.preview:
        prev = build / "preview"
        prev.mkdir()
        r = subprocess.run(["typst", "compile", "--root", str(build), str(build / "main.typ"),
                            str(prev / "p{0p}.png"), "--pages", a.preview, "--ppi", "70"])
        print(f"preview pages in {prev}")
    sys.exit(r.returncode)


main()
