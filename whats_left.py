#!/usr/bin/env python3

# It's recommended to run this with `python3 -I not_impl_gen.py`, to make sure
# that nothing in your global Python environment interferes with what's being
# extracted here.
#
# This script generates Lib/snippets/whats_left_data.py with these variables defined:
# expected_methods - a dictionary mapping builtin objects to their methods
# cpymods - a dictionary mapping module names to their contents
# libdir - the location of RustPython's Lib/ directory.
#
# TODO: include this:
# which finds all modules it has available and
# creates a Python dictionary mapping module names to their contents, which is
# in turn used to generate a second Python script that also finds which modules
# it has available and compares that against the first dictionary we generated.
# We then run this second generated script with RustPython.

import argparse
import re
import os
import sys
import json
import warnings
import inspect
import subprocess
import platform
from pydoc import ModuleScanner

GENERATED_FILE = "extra_tests/snippets/not_impl.py"

implementation = platform.python_implementation()
if implementation != "CPython":
    sys.exit("whats_left.py must be run under CPython, got {implementation} instead")


def parse_args():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--mismatched-values",
        action="store_true",
        help="print functions whose signatures don't match CPython's",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print output as JSON (instead of line by line)",
    )

    args = parser.parse_args()
    return args


args = parse_args()


sys.path = [
    path
    for path in sys.path
    if ("site-packages" not in path and "dist-packages" not in path)
]


def attr_is_not_inherited(type_, attr):
    """
    returns True if type_'s attr is not inherited from any of its base classes
    """
    bases = type_.__mro__[1:]
    return getattr(type_, attr) not in (getattr(base, attr, None) for base in bases)


def extra_info(obj):
    # RustPython doesn't support __text_signature__ for getting signatures of builtins
    # https://github.com/RustPython/RustPython/issues/2410
    if callable(obj) and not inspect._signature_is_builtin(obj):
        try:
            sig = str(inspect.signature(obj))
            # remove function memory addresses
            return re.sub(" at 0x[0-9A-Fa-f]+", " at 0xdeadbeef", sig)
        except Exception as e:
            exception = repr(e)
            # CPython uses ' RustPython uses "
            if exception.replace('"', "'").startswith("ValueError('no signature found"):
                return "ValueError('no signature found')"
            return exception
    return None


def gen_methods():
    types = [
        bool,
        bytearray,
        bytes,
        complex,
        dict,
        enumerate,
        filter,
        float,
        frozenset,
        int,
        list,
        map,
        memoryview,
        range,
        set,
        slice,
        str,
        super,
        tuple,
        object,
        zip,
        classmethod,
        staticmethod,
        property,
        Exception,
        BaseException,
    ]
    objects = [t.__name__ for t in types]
    objects.append("type(None)")

    iters = [
        "type(bytearray().__iter__())",
        "type(bytes().__iter__())",
        "type(dict().__iter__())",
        "type(dict().values().__iter__())",
        "type(dict().items().__iter__())",
        "type(dict().values())",
        "type(dict().items())",
        "type(set().__iter__())",
        "type(list().__iter__())",
        "type(range(0).__iter__())",
        "type(str().__iter__())",
        "type(tuple().__iter__())",
    ]

    methods = {}
    for typ_code in objects + iters:
        typ = eval(typ_code)
        attrs = []
        for attr in dir(typ):
            if attr_is_not_inherited(typ, attr):
                attrs.append((attr, extra_info(getattr(typ, attr))))
        methods[typ.__name__] = (typ_code, extra_info(typ), attrs)

    output = "expected_methods = {\n"
    for name, (typ_code, extra, attrs) in methods.items():
        output += f" '{name}': ({typ_code}, {extra!r}, [\n"
        for attr, attr_extra in attrs:
            output += f"    ({attr!r}, {attr_extra!r}),\n"
        output += " ]),\n"
        if typ_code != objects[-1]:
            output += "\n"
    output += "}\n\n"
    return output


def scan_modules():
    """taken from the source code of help('modules')

    https://github.com/python/cpython/blob/63298930fb531ba2bb4f23bc3b915dbf1e17e9e1/Lib/pydoc.py#L2178"""
    modules = {}

    def callback(path, modname, desc, modules=modules):
        if modname and modname[-9:] == ".__init__":
            modname = modname[:-9] + " (package)"
        if modname.find(".") < 0:
            modules[modname] = 1

    def onerror(modname):
        callback(None, modname, None)

    with warnings.catch_warnings():
        # ignore warnings from importing deprecated modules
        warnings.simplefilter("ignore")
        ModuleScanner().run(callback, onerror=onerror)
    return list(modules.keys())


def dir_of_mod_or_error(module_name):
    with warnings.catch_warnings():
        # ignore warnings caused by importing deprecated modules
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        try:
            module = __import__(module_name)
        except Exception as e:
            return e
    item_names = sorted(set(dir(module)))
    result = {}
    for item_name in item_names:
        item = getattr(module, item_name)
        result[item_name] = extra_info(item)
    return result


def gen_modules():
    # check name because modules listed have side effects on import,
    # e.g. printing something or opening a webpage
    modules = {}
    for mod_name in scan_modules():
        if mod_name in ("this", "antigravity"):
            continue
        dir_result = dir_of_mod_or_error(mod_name)
        if isinstance(dir_result, Exception):
            print(
                f"!!! {mod_name} skipped because {type(dir_result).__name__}: {str(dir_result)}",
                file=sys.stderr,
            )
            continue
        modules[mod_name] = dir_result
    return modules


output = """\
# WARNING: THIS IS AN AUTOMATICALLY GENERATED FILE
# EDIT extra_tests/not_impl_gen.sh, NOT THIS FILE.
# RESULTS OF THIS TEST DEPEND ON THE CPYTHON
# VERSION AND PYTHON ENVIRONMENT USED
# TO RUN not_impl_mods_gen.py

"""

output += gen_methods()
output += f"""
cpymods = {gen_modules()!r}
libdir = {os.path.abspath("Lib/").encode('utf8')!r}

"""

# Copy the source code of functions we will reuse in the generated script
for fn in [attr_is_not_inherited, extra_info, dir_of_mod_or_error]:
    output += "".join(inspect.getsourcelines(fn)[0]) + "\n\n"

# Prevent missing variable linter errors from compare()
expected_methods = {}
cpymods = {}
libdir = ""
# This function holds the source code that will be run under RustPython
def compare():
    import re
    import os
    import sys
    import warnings
    import json
    import inspect
    import platform

    def method_incompatability_reason(typ, method_name, real_method_value):
        has_method = hasattr(typ, method_name)
        if not has_method:
            return ""

        is_inherited = not attr_is_not_inherited(typ, method_name)
        if is_inherited:
            return "inherited"

        value = extra_info(getattr(typ, method_name))
        if value != real_method_value:
            return f"{value} != {real_method_value}"

        return None

    not_implementeds = {}
    for name, (typ, real_value, methods) in expected_methods.items():
        missing_methods = {}
        for method, real_method_value in methods:
            reason = method_incompatability_reason(typ, method, real_method_value)
            if reason is not None:
                missing_methods[method] = reason
        if missing_methods:
            not_implementeds[name] = missing_methods

    if platform.python_implementation() == "CPython":
        if not_implementeds:
            sys.exit("ERROR: CPython should have all the methods")

    mod_names = [
        name.decode()
        for name, ext in map(os.path.splitext, os.listdir(libdir))
        if ext == b".py" or os.path.isdir(os.path.join(libdir, name))
    ]
    mod_names += list(sys.builtin_module_names)
    # Remove easter egg modules
    mod_names = sorted(set(mod_names) - {"this", "antigravity"})

    rustpymods = {mod: dir_of_mod_or_error(mod) for mod in mod_names}

    result = {
        "implemented": {},
        "not_implemented": {},
        "failed_to_import": {},
        "missing_items": {},
        "mismatched_items": {},
    }
    for modname, cpymod in cpymods.items():
        rustpymod = rustpymods.get(modname)
        if rustpymod is None:
            result["not_implemented"][modname] = None
        elif isinstance(rustpymod, Exception):
            result["failed_to_import"][modname] = rustpymod.__class__.__name__ + str(
                rustpymod
            )
        else:
            implemented_items = sorted(set(cpymod) & set(rustpymod))
            mod_missing_items = set(cpymod) - set(rustpymod)
            mod_missing_items = sorted(
                f"{modname}.{item}" for item in mod_missing_items
            )
            mod_mismatched_items = [
                (f"{modname}.{item}", rustpymod[item], cpymod[item])
                for item in implemented_items
                if rustpymod[item] != cpymod[item]
                and not isinstance(cpymod[item], Exception)
            ]

            if mod_missing_items or mod_mismatched_items:
                if mod_missing_items:
                    result["missing_items"][modname] = mod_missing_items
                if mod_mismatched_items:
                    result["mismatched_items"][modname] = mod_mismatched_items
            else:
                result["implemented"][modname] = None

    # TODO: fix variable names
    result = {
        "builtins": not_implementeds,
        "modules": result,
    }
    print(json.dumps(result))


def remove_one_indent(s):
    indent = "    "
    return s[len(indent) :] if s.startswith(indent) else s


compare_src = inspect.getsourcelines(compare)[0][1:]
output += "".join(remove_one_indent(line) for line in compare_src)

with open(GENERATED_FILE, "w") as f:
    f.write(output + "\n")


subprocess.run(["cargo", "build", "--release"], check=True)
result = subprocess.run(
    ["cargo", "run", "--release", "-q", "--", GENERATED_FILE],
    env={**os.environ.copy(), "RUSTPYTHONPATH": "Lib"},
    text=True,
    capture_output=True,
)
# The last line should be json output, the rest of the lines can contain noise
# because importing certain modules can print stuff to stdout/stderr
result = json.loads(result.stdout.splitlines()[-1])

if args.json:
    print(json.dumps(result))
    sys.exit()

modules = result["modules"]
builtins = result["builtins"]

# missing from builtins
for module, missing_methods in builtins.items():
    for method, reason in missing_methods.items():
        print(f"{module}.{method}" + (f" {reason}" if reason else ""))

# missing from modules
for modname in modules["not_implemented"]:
    print(modname, "(entire module)")
for modname, exception in modules["failed_to_import"].items():
    print(f"{modname} (exists but not importable: {exception})")
for modname, missing in modules["missing_items"].items():
    for item in missing:
        print(item)
if args.mismatched_values:
    for modname, mismatched in modules["mismatched_items"].items():
        for (item, rustpy_value, cpython_value) in mismatched:
            print(f"{item} {rustpy_value} != {cpython_value}")
