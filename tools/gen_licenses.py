"""Generate THIRD_PARTY_LICENSES.txt from installed package metadata."""
import glob
import os
import re
import sys
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

LICENSE_FILE = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE)[^/]*$", re.I)
HEADER = "THIRD-PARTY LICENSES\n" + "=" * 60 + "\n"
RULE = "-" * 60


def read(path):
    return Path(path).read_text(encoding="utf-8", errors="replace").strip()


def warn(msg):
    print(f"WARNING: {msg}", file=sys.stderr)


def read_requirements(path):
    lines = (line.split("#")[0].strip() for line in open(path, encoding="utf-8"))
    return [Requirement(line).name for line in lines if line]


def walk(names):
    seen, stack = {}, list(names)
    while stack:
        name = stack.pop()
        key = canonicalize_name(name)
        if key in seen:
            continue
        try:
            dist = distribution(name)
        except PackageNotFoundError:
            warn(f"{name} not installed, skipping")
            continue
        seen[key] = dist
        for r in dist.requires or []:
            req = Requirement(r)
            if not req.marker or req.marker.evaluate({"extra": ""}):
                stack.append(req.name)
    return sorted(seen.values(), key=lambda d: d.metadata["Name"].lower())


def license_name(dist):
    md = dist.metadata
    if md.get("License-Expression"):
        return md["License-Expression"]
    lic = md.get("License")
    if lic and "\n" not in lic and len(lic) < 100:
        return lic
    classifiers = [c.split("::")[-1].strip()
                   for c in md.get_all("Classifier") or []
                   if c.startswith("License ::")]
    return ", ".join(classifiers) or "UNKNOWN"


def package_block(dist):
    md = dist.metadata
    lic = license_name(dist)
    if lic == "UNKNOWN":
        warn(f"no license found for {md['Name']}")
    block = [f"\n{RULE}\n{md['Name']} {dist.version}\nLicense: {lic}"]
    url = md.get("Home-page") or (md.get_all("Project-URL") or [""])[0]
    if url:
        block.append(f"URL: {url}")
    for f in dist.files or []:
        if LICENSE_FILE.search(f.as_posix()):
            block.append(f"\n[{f.name}]\n{read(dist.locate_file(f))}")
    return "\n".join(block)


def runtime_blocks():
    """Python (PSF) and Tcl/Tk license texts from the interpreter's install."""
    base = sys.base_prefix
    blocks = []

    py = os.path.join(base, "LICENSE.txt")
    if os.path.exists(py):
        blocks.append(f"\n{RULE}\nPython {sys.version.split()[0]}\n"
                      f"License: PSF-2.0\nURL: https://www.python.org\n\n{read(py)}")
    else:
        warn("Python LICENSE.txt not found")

    tcl = glob.glob(os.path.join(base, "tcl", "**", "license.terms"), recursive=True)
    if tcl:
        blocks.append(f"\n{RULE}\nTcl/Tk\nLicense: Tcl/Tk (BSD-style)\n"
                      f"URL: https://www.tcl-lang.org\n\n{read(sorted(tcl)[0])}")
    else:
        warn("Tcl/Tk license.terms not found")
    return blocks


def main(req_path="requirements.txt", out_path="THIRD_PARTY_LICENSES.txt"):
    parts = [HEADER, *runtime_blocks(),
             *(package_block(d) for d in walk(read_requirements(req_path)))]
    Path(out_path).write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])