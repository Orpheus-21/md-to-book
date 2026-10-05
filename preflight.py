#!/usr/bin/env python3
"""Check a book PDF against the KDP paperback rules and print a report.

  preflight.py book.pdf --trim 6x9 [--bleed 0.125in]

Rules: https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6 (trim, bleed, margins)
       https://kdp.amazon.com/en_US/help/topic/G202169030 (images, 300 ppi)
Exit code 1 when a check fails.
"""
import argparse, re, subprocess, sys
from build import gutter_min, parse_trim

PT = {"in": 72.0, "mm": 72 / 25.4, "cm": 72 / 2.54, "pt": 1.0}


def to_pt(length):
    n, unit = re.fullmatch(r"([\d.]+)(in|mm|cm|pt)", length).groups()
    return float(n) * PT[unit]


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def ranges(pages):
    """[2, 3, 7] -> '2-3, 7'."""
    out, i = [], 0
    while i < len(pages):
        j = i
        while j + 1 < len(pages) and pages[j + 1] == pages[j] + 1:
            j += 1
        out.append(str(pages[i]) if i == j else f"{pages[i]}-{pages[j]}")
        i = j + 1
    return ", ".join(out)


def check(pdf, trim, bleed):
    """Return a list of (status, message). Status is OK, WARN, or FAIL."""
    res = []
    w, h = (to_pt(x) for x in parse_trim(trim))
    b = to_pt(bleed)

    info = run("pdfinfo", pdf)
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    pw, ph = (float(x) for x in re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info).groups())

    if pages < 24:
        res.append(("FAIL", f"The book has {pages} pages. KDP needs at least 24."))
    elif gutter_min(pages) is None:
        res.append(("FAIL", f"The book has {pages} pages. KDP prints 828 pages at most."))
    else:
        res.append(("OK", f"Page count: {pages}."))

    ew, eh = w + b, h + 2 * b
    if abs(pw - ew) > 0.5 or abs(ph - eh) > 0.5:
        res.append(("FAIL", f"The page is {pw:.1f} x {ph:.1f} pt. With this trim and bleed it must be {ew:.1f} x {eh:.1f} pt."))
    else:
        res.append(("OK", f"Page size: {pw:.1f} x {ph:.1f} pt."))

    bad = []
    for line in run("pdffonts", pdf).splitlines()[2:]:
        t = line.split()
        if len(t) >= 8 and t[-5] != "yes":
            bad.append(t[0])
    res.append(("FAIL", f"Fonts not embedded: {', '.join(bad)}.") if bad else ("OK", "All fonts are embedded."))

    texts = run("pdftotext", "-layout", pdf, "-").split("\f")[:pages]
    blank = [i for i, t in enumerate(texts, 1) if not t.strip()]
    consecutive = [p for p in blank if p + 1 in blank]
    if pages in blank:
        res.append(("WARN", f"The last page is blank (blank pages: {ranges(blank)})."))
    elif consecutive:
        res.append(("WARN", f"Two blank pages follow each other: {ranges(consecutive + [consecutive[-1] + 1])}."))
    else:
        res.append(("OK", f"Blank pages: {ranges(blank) or 'none'}. A blank page before a chapter is normal."))

    # Margins: the distance from each word to the trim edge. The bleed lies on the outer, top, and bottom edges.
    side_min = 0.375 if b else 0.25
    inside_min = gutter_min(pages)
    problems = []
    n = 0
    for pg in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>',
                          run("pdftotext", "-bbox", pdf, "-"), re.S):
        n += 1
        W, H, body = float(pg.group(1)), float(pg.group(2)), pg.group(3)
        words = [tuple(map(float, m)) for m in re.findall(
            r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"', body)]
        if not words:
            continue
        x0, y0 = min(x[0] for x in words), min(x[1] for x in words)
        x1, y1 = max(x[2] for x in words), max(x[3] for x in words)
        recto = n % 2 == 1
        left = x0 - (0 if recto else b)
        right = (W - b if recto else W) - x1
        inside, outside = (left, right) if recto else (right, left)
        for name, d, need in (("inside", inside, inside_min), ("outside", outside, side_min),
                              ("top", y0 - b, side_min), ("bottom", H - b - y1, side_min)):
            if need is not None and d < need * 72 - 0.5:
                problems.append((n, name, d / 72, need))
    if problems:
        pgs = ranges(sorted({p[0] for p in problems}))
        n0, name, d, need = problems[0]
        names = ", ".join(sorted({p[1] for p in problems}))
        res.append(("FAIL", f"Text is too near these edges: {names}. Example: {name} edge on page {n0} is {d:.2f} in, KDP needs {need} in. Pages: {pgs}."))
    else:
        res.append(("OK", f"Margins: all text is inside the KDP margins (inside {inside_min} in, others {side_min} in)."))

    low = []
    for line in run("pdfimages", "-list", pdf).splitlines()[2:]:
        t = line.split()
        if len(t) > 13 and min(float(t[12]), float(t[13])) < 300:
            low.append((int(t[0]), min(float(t[12]), float(t[13]))))
    if low:
        res.append(("WARN", f"Images below 300 ppi: page {low[0][0]} has {low[0][1]:.0f} ppi. Pages: {ranges(sorted({p for p, _ in low}))}."))
    else:
        res.append(("OK", "Images: none below 300 ppi."))
    return res


def report(res):
    for status, msg in res:
        print(f"{status:4}  {msg}")
    fails = sum(s == "FAIL" for s, _ in res)
    warns = sum(s == "WARN" for s, _ in res)
    print(f"Result: {fails} fail, {warns} warn." + (" The book is ready for KDP." if not fails else " Fix the fails first."))
    return fails


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("pdf")
    a.add_argument("--trim", default="5.5x8.5")
    a.add_argument("--bleed", default="0pt")
    a = a.parse_args()
    sys.exit(1 if report(check(a.pdf, a.trim, a.bleed)) else 0)
