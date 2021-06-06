#!/usr/bin/env python3

# This script scans all .py files in cpython/Lib, finds all import statements
# in them and counts out what is imported most often in each top directory
# or file in Lib/ (meaning if some library is imported many times in various
# files in e.g. Lib/http/ , it will only be counted once).
#
# Clone the CPython repo then put this file in the top level cpython/
# directory and run it:
#
# cd /tmp
# git clone https://github.com/python/cpython/
# cd cpython
# # <download find_improts.py to this directory>
# python3 find_imports.py

from pathlib import Path
import ast
import itertools
from operator import itemgetter
import json
from collections import Counter

CPYTHON_LIB = Path("../../cpython/Lib")


imported = {}
for p in CPYTHON_LIB.rglob("*.py"):
    if "test" in p.parts or "tests" in p.parts or p.name.startswith("test_"):
        continue
    lib = p.relative_to(CPYTHON_LIB).parts[0].removesuffix(".py")
    with open(p) as f:
        parsed = ast.parse(f.read())
        imports = []
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            if isinstance(node, ast.ImportFrom):
                if node.level == 0:  # Don't include relative imports
                    imports.append(node.module)
        # Count "collections.abc" as "collections"
        imports = [i.split(".")[0] for i in imports]
        # If the library is a directory with multiple files, imported might
        # already contain something.
        new_imports = set(imported.get(lib, [])) | set(imports)
        # Don't count self imports
        imported[lib] = sorted(new_imports - {lib, "__main__"})

# print(json.dumps(imported, indent=4))

# most_imported = dict(Counter(itertools.chain.from_iterable(imported.values())))
# for lib, count in sorted(most_imported.items(), key=itemgetter(1, 0)):
#     print(lib, count)

most_imported = Counter(itertools.chain.from_iterable(imported.values()))
top_most_imported = {k for k, v in most_imported.most_common(30)}
top_most_imported = {}


def flatten(list_of_lists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(list_of_lists)


cpython_keys = sorted({s.removesuffix(".py") for s in imported} | set(flatten(imported.values())))
# Edit not_impl_gen.py to output a json dict of names then
# run this command in the RustPython repo:
# ./whats_left.sh | tail -n 1 > left.json
with open("left.json") as f:
    statuses = json.load(f)
key_status = {}
for status in [
    "implemented",
    "not_implemented",
    "failed_to_import",
    "missing_items",
    "mismatched_items",
]:
    for module in statuses[status]:
        key_status.setdefault(module, status)

cpython_keys = {k: i for i, k in enumerate(cpython_keys)}
# See https://bl.ocks.org/agnjunio/fd86583e176ecd94d37f3d2de3a56814
nodes = []
key_idx = {}
for i, k in enumerate(cpython_keys):
    nodes.append({"name": k, "group": 1, "class": key_status.get(k, "unknown_to_rustpython")})
    key_idx[k] = i
for i, k in enumerate([k for k in key_status if k not in cpython_keys], start=len(nodes)):
    nodes.append({"name": k, "group": 1, "class": "unknown_to_cpython"})
    key_idx[k] = i

links = []
for src, dependencies in imported.items():
    src = src.removesuffix(".py")
    # if src not in statuses["not_implemented"]:
    #     continue
    for dep in dependencies:
        if dep not in (statuses["not_implemented"]) and dep in key_status:
            continue
        links.append(
            {
                "source": key_idx[dep],
                "target": key_idx[src],
                "value": 1,  # TODO: could set this differently
                "type": "depends",
            }
        )

print(json.dumps({"nodes": nodes, "links": links}))
# print(json.dumps({"nodes": nodes, "links": links}, indent=4))
