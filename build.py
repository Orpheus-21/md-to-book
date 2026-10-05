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


# KDP minimum inside margin (gutter) by page count.
# Source: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6
GUTTER = [(150, "0.375in"), (300, "0.5in"), (500, "0.625in"), (700, "0.75in"), (828, "0.875in")]
PRESETS = {"a4": "210x297mm", "a5": "148x210mm", "a6": "105x148mm"}


def parse_trim(s):
    """'6x9', '5.5x8.5in', 'a5' or '148x210mm' -> (width, height) as Typst lengths."""
    m = re.fullmatch(r"([\d.]+)x([\d.]+)(in|mm|cm|pt)?", PRESETS.get(s.lower(), s.lower()))
    if not m:
        sys.exit(f"Bad --trim '{s}'. Use WxH with in or mm, or a4, a5, a6.")
    w, h, unit = m.groups()
    return f"{w}{unit or 'in'}", f"{h}{unit or 'in'}"


def gutter(pages):
    """The KDP minimum, but never less than 0.625in, so a small book is not cramped at the spine."""
    for top, g in GUTTER:
        if pages <= top:
            return g if float(g[:-2]) > 0.625 else "0.625in"
    sys.exit(f"{pages} pages is more than KDP prints (828 pages maximum).")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("dir")
    a.add_argument("--list", action="store_true")
    a.add_argument("--files", nargs="*")
    a.add_argument("--title", default="Untitled")
    a.add_argument("--author", default="")
    a.add_argument("--out", default="book.pdf")
    a.add_argument("--trim", default="5.5x8.5", help="trim size: 6x9, 5.5x8.5in, a5, 148x210mm (default 5.5x8.5in)")
    a.add_argument("--bleed", default="0pt", help="bleed on the top, bottom, and outer edges, e.g. 0.125in")
    a.add_argument("--font-size", default="11pt")
    a.add_argument("--print", dest="kdp", action="store_true",
                   help="set the inside margin from the KDP table for the page count (at least 0.625in)")
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
    w, h = parse_trim(a.trim)
    args = (f'title: "{esc(a.title)}", author: "{esc(a.author)}", width: {w}, height: {h}, '
            f'bleed: {a.bleed}, size: {a.font_size}')
    lines = ['#import "@preview/cmarker:0.1.6"', '#import "template.typ": book',
             '#let scope = (image: (source, alt: none, ..args) => image(source, alt: alt, ..args))']
    for i, f in enumerate(files, 1):
        name = f"chapters/{i:02}.md"
        fallback = re.sub(r"^\d+[-_. ]*", "", f.stem).replace("-", " ").replace("_", " ").title()
        text = fix_images(clean(f.read_text(encoding="utf-8"), fallback), f.parent, build, i)
        (build / name).write_text(text, encoding="utf-8")
        lines.append(f'#cmarker.render(read("{name}"), scope: scope)')
    def compile_book(extra=""):
        (build / "main.typ").write_text(
            "\n".join(lines[:2] + [f"#show: book.with({args}{extra})"] + lines[2:]) + "\n", encoding="utf-8")
        return subprocess.run(["typst", "compile", "--root", str(build), str(build / "main.typ"), str(out)])

    def page_count():
        q = subprocess.run(["typst", "query", "--root", str(build), str(build / "main.typ"), "<npages>",
                            "--field", "value", "--one"], capture_output=True, text=True)
        return int(q.stdout)

    out = root / a.out
    r = compile_book()
    if r.returncode == 0 and a.kdp:
        extra, seen = "", None
        for _ in range(4):  # the gutter can change the page count, so repeat until it is stable
            g = gutter(page_count())
            if g == seen:
                break
            seen, extra = g, f", inner: {g}"
            r = compile_book(extra)
        print(f"KDP inside margin: {seen}")
    if r.returncode == 0:
        n = page_count()
        print(f"{n} pages, trim {w} x {h}, bleed {a.bleed}")
        if a.kdp and n < 24:
            print("warning: KDP needs at least 24 pages", file=sys.stderr)
    if r.returncode == 0 and a.preview:
        prev = build / "preview"
        prev.mkdir()
        r = subprocess.run(["typst", "compile", "--root", str(build), str(build / "main.typ"),
                            str(prev / "p{0p}.png"), "--pages", a.preview, "--ppi", "70"])
        print(f"preview pages in {prev}")
    sys.exit(r.returncode)


main()
