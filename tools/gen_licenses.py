"""Generate THIRD_PARTY_LICENSES.txt from installed package metadata.

Usage: python tools/gen_licenses.py [requirements-file] [output-file]
Run it after installing that requirements file, on the platform you are building for.
"""
import re
import sys
import sysconfig
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

LICENSE_FILE = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE)[^/]*$", re.I)
HEADER = "THIRD-PARTY LICENSES\n" + "=" * 60 + "\n"
RULE = "-" * 60
QT_NOTICE = Path(__file__).parent / "licenses" / "qt.txt"


def read(path):
    return Path(path).read_text(encoding="utf-8", errors="replace").strip()


def warn(msg):
    print(f"WARNING: {msg}", file=sys.stderr)


def read_requirements(path):
    """Package names in a requirements file, following `-r` includes and
    skipping entries whose environment marker doesn't apply on this platform."""
    path = Path(path)
    names = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if line.startswith(("-r ", "--requirement ")):
            names += read_requirements(path.parent / line.split(None, 1)[1].strip())
        elif not line.startswith("-"):
            req = Requirement(line)
            if not req.marker or req.marker.evaluate():
                names.append(req.name)
    return names


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
    """Python (PSF) license text and the Qt notice."""
    blocks = []

    candidates = [Path(sys.base_prefix) / "LICENSE.txt",
                  Path(sysconfig.get_path("stdlib")) / "LICENSE.txt"]
    py = next((p for p in candidates if p.exists()), None)
    if py:
        blocks.append(f"\n{RULE}\nPython {sys.version.split()[0]}\n"
                      f"License: PSF-2.0\nURL: https://www.python.org\n\n{read(py)}")
    else:
        warn("Python LICENSE.txt not found")

    if QT_NOTICE.exists():
        blocks.append(f"\n{RULE}\nQt\nLicense: LGPL-3.0\nURL: https://www.qt.io\n\n{read(QT_NOTICE)}")
    else:
        warn("tools/licenses/qt.txt missing")
    return blocks


def main(req_path="requirements.txt", out_path="THIRD_PARTY_LICENSES.txt"):
    parts = [HEADER, *runtime_blocks(),
             *(package_block(d) for d in walk(read_requirements(req_path)))]
    Path(out_path).write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
