#!/usr/bin/env python3
"""Run: python3 test/test_preflight.py. Needs typst and poppler."""
import shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from preflight import check

BAD = """#set page(width: 6in, height: 9in, margin: (inside: 0.2in, outside: 0.1in, top: 0.2in, bottom: 0.3in))
#for i in range(40) [Paragraph #i. #lorem(60)

]
#image("figure.png", width: 4in)
#pagebreak()
"""

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    (d / "bad.typ").write_text(BAD)
    shutil.copy(HERE / "essays/sub/figure.png", d)
    subprocess.run(["typst", "compile", str(d / "bad.typ"), str(d / "bad.pdf")], check=True)
    got = {(s, m.split(":")[0].split(" ")[0]) for s, m in check(str(d / "bad.pdf"), "6x9", "0pt")}

for want in [("FAIL", "The"), ("FAIL", "Text"), ("WARN", "Images"), ("WARN", "The"), ("OK", "Page"), ("OK", "All")]:
    assert want in got, f"missing {want} in {sorted(got)}"
print("preflight test passed")
