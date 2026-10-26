"""Check every relative link, #anchor and pinned GitHub blob link in the given Markdown files.

Usage: python3 work/docs-pass/linkcheck.py README.md docs/reviewer-guide.md ...
Prints one line per broken link and exits 1 if any are broken.
"""
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO = "alexisdacquay/sail-event"
ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())


def slug(text):
    # GitHub: strip markup, lowercase, drop punctuation except - and _, spaces to -
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").replace("*", "").strip().lower()
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "-_" or ch == " " or cat[0] in "LN":
            out.append("-" if ch == " " else ch)
    return "".join(out)


def anchors(md_text):
    seen, result = {}, set()
    in_code = False
    for line in md_text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            s = slug(m.group(2))
            n = seen.get(s, 0)
            result.add(s if n == 0 else f"{s}-{n}")
            seen[s] = n + 1
    for m in re.finditer(r'<a\s+(?:id|name)="([^"]+)"', md_text):
        result.add(m.group(1))
    return result


def lines_at(sha, path):
    r = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True, text=True)
    return None if r.returncode else r.stdout.count("\n") + 1


def check_line_anchor(frag, nlines):
    m = re.match(r"L(\d+)(?:-L(\d+))?$", frag)
    if not m:
        return True
    return max(int(m.group(1)), int(m.group(2) or 0)) <= nlines


def links(md_text):
    text = re.sub(r"```.*?```", "", md_text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    refs = dict(re.findall(r"^\[([^\]]+)\]:\s*(\S+)", text, flags=re.M))
    for m in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", text):
        yield m.group(1)
    for m in re.finditer(r"!?\[[^\]]*\]\[([^\]]+)\]", text):
        yield refs.get(m.group(1), f"MISSING-REF:{m.group(1)}")
    for m in re.finditer(r'(?:src|href)="([^"]+)"', text):
        yield m.group(1)
    yield from refs.values()


def main(files):
    bad = []
    for f in files:
        src = ROOT / f
        md = src.read_text()
        for url in set(links(md)):
            if url.startswith("MISSING-REF:"):
                bad.append(f"{f}: undefined reference [{url[12:]}]")
                continue
            if url.startswith(("mailto:", "http://localhost", "https://img.shields.io")):
                continue
            m = re.match(rf"https://github\.com/{REPO}/(?:blob|tree)/([0-9a-f]{{7,40}}|main)/([^#?]+)(?:#(.*))?$", url)
            if m:
                sha, path, frag = m.group(1), m.group(2), m.group(3) or ""
                n = lines_at(sha, path)
                if n is None:
                    r = subprocess.run(["git", "cat-file", "-t", f"{sha}:{path}"], capture_output=True, text=True)
                    if r.stdout.strip() != "tree":
                        bad.append(f"{f}: {url} -> no {path} at {sha}")
                elif frag and not check_line_anchor(frag, n):
                    bad.append(f"{f}: {url} -> {path} at {sha} has {n} lines")
                continue
            if re.match(r"^[a-z]+://", url):
                continue
            path, _, frag = url.partition("#")
            target = (src.parent / path).resolve() if path else src
            if not target.exists():
                bad.append(f"{f}: {url} -> missing file")
                continue
            if frag and target.suffix == ".md":
                if frag not in anchors(target.read_text()):
                    bad.append(f"{f}: {url} -> no anchor #{frag}")
            elif frag and target.is_file():
                if not check_line_anchor(frag, target.read_text().count("\n") + 1):
                    bad.append(f"{f}: {url} -> line anchor past end of file")
    print("\n".join(sorted(bad)) or "all links ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
