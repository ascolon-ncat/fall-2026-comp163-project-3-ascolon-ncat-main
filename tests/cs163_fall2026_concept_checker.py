#!/usr/bin/env python3
"""
CS 163 Fall 2026 - Concept Checker

Scans student Python files for concepts from chapters not yet covered, and
for the constructs a project must contain. Violations and commit count are
saved to concept_check_report.json.

With --strict it exits nonzero on any violation or missing construct. That is
how the autograder runs it, as a scored test. Without --strict it always exits
0.

A violation reported by this script results in a zero for the project after
instructor review.

Usage:
    python3 cs163_fall2026_concept_checker.py --project N [file1.py ...]

    If no files are specified, all .py files in the current directory are
    scanned, excluding provided files and test infrastructure.
"""

import ast
import builtins
import sys
import json
import argparse
import os
import fnmatch
import subprocess
from pathlib import Path
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Forbidden concept map by project number
# Each entry: AST node class name -> plain-language description
#
#   P1 - Ch. 1-2:   Intro, Variables & Expressions
#   P2 - Ch. 3-4:   Types, Branching
#   P3 - Ch. 5-6:   Loops, Strings
#   P4 - Ch. 7-8:   Functions, Files
#   P5 - Ch. 9-11:  Classes, Inheritance, Exceptions
# ---------------------------------------------------------------------------

FORBIDDEN_BY_PROJECT: dict[int, dict[str, str]] = {
    1: {
        "FunctionDef":      "function definition",
        "AsyncFunctionDef": "async function definition",
        "Lambda":           "lambda function",
        "ClassDef":         "class definition",
        "For":              "for loop",
        "While":            "while loop",
        "If":               "if/elif/else statement",
        "IfExp":            "conditional expression (a if b else c)",
        "Match":            "match/case statement",
        "Import":           "import statement",
        "ImportFrom":       "from...import statement",
        "Try":              "try/except block",
        "TryStar":          "try/except* block",
        "With":             "with statement",
        "ListComp":         "list comprehension",
        "DictComp":         "dict comprehension",
        "SetComp":          "set comprehension",
        "GeneratorExp":     "generator expression",
    },
    2: {
        "FunctionDef":      "function definition",
        "AsyncFunctionDef": "async function definition",
        "Lambda":           "lambda function",
        "ClassDef":         "class definition",
        "For":              "for loop",
        "While":            "while loop",
        "Match":            "match/case statement",
        "Import":           "import statement",
        "ImportFrom":       "from...import statement",
        "Try":              "try/except block",
        "TryStar":          "try/except* block",
        "With":             "with statement",
        "ListComp":         "list comprehension",
        "DictComp":         "dict comprehension",
        "SetComp":          "set comprehension",
        "GeneratorExp":     "generator expression",
    },
    # Match and the comprehensions are in no chapter of this book.
    3: {
        "FunctionDef":      "function definition",
        "AsyncFunctionDef": "async function definition",
        "Lambda":           "lambda function",
        "ClassDef":         "class definition",
        "Match":            "match/case statement",
        "Import":           "import statement",
        "ImportFrom":       "from...import statement",
        "Try":              "try/except block",
        "TryStar":          "try/except* block",
        "With":             "with statement",
        "ListComp":         "list comprehension",
        "DictComp":         "dict comprehension",
        "SetComp":          "set comprehension",
        "GeneratorExp":     "generator expression",
        # `raise SystemExit` ends the game as exit() would.
        "Raise":            "raise statement",
    },
    # def and with are now allowed. lambda is not: Chapter 7 never teaches it
    # (2.3 only lists it as a reserved word). raise is Chapter 11 with try.
    # yield and async/await are taught in no chapter of this book.
    4: {
        "ClassDef":         "class definition",
        "Lambda":           "lambda function",
        "Import":           "import statement",
        "Match":            "match/case statement",
        "ImportFrom":       "from...import statement",
        "Try":              "try/except block",
        "TryStar":          "try/except* block",
        "Raise":            "raise statement",
        "ListComp":         "list comprehension",
        "DictComp":         "dict comprehension",
        "SetComp":          "set comprehension",
        "GeneratorExp":     "generator expression",
        "AsyncFunctionDef": "async function definition",
        "Await":            "await expression",
        "Yield":            "yield expression",
        "YieldFrom":        "yield from expression",
    },
    # Classes, raise and try are now allowed, and lists and dicts are Chapter
    # 3. Everything else Project 4 bans stays banned.
    5: {
        "Lambda":           "lambda function",
        "Import":           "import statement",
        "Match":            "match/case statement",
        "ImportFrom":       "from...import statement",
        "ListComp":         "list comprehension",
        "DictComp":         "dict comprehension",
        "SetComp":          "set comprehension",
        "GeneratorExp":     "generator expression",
        "AsyncFunctionDef": "async function definition",
        "Await":            "await expression",
        "Yield":            "yield expression",
        "YieldFrom":        "yield from expression",
    },
}

# String methods are Chapter 6. A Chapter 3-4 project must compare with ==
# rather than normalizing input first, so these are forbidden for Project 2
# only. Listed explicitly rather than flagging every attribute call, because a
# blanket rule would also catch things students legitimately reach for later.
FORBIDDEN_METHODS_BY_PROJECT: dict[int, set[str]] = {
    2: {
        "lower", "upper", "strip", "lstrip", "rstrip", "title", "capitalize",
        "split", "rsplit", "join", "replace", "find", "rfind", "index",
        "startswith", "endswith", "count", "format", "isdigit", "isalpha",
        "isnumeric", "isspace", "islower", "isupper", "zfill", "casefold",
    },
}

# Built-in functions that are off limits. `With` already blocks
# `with open(...)`, but a bare `open(name)` call is an ordinary Call node, so
# Projects 2 and 3 list open here.
#
# exit() and quit() end the program without the control flow a project is
# about. exec(), eval(), compile() and __import__() reach an import or exit()
# without the statement. breakpoint() runs a committed .pdbrc, and help()
# imports any module named in its argument. From Project 4 on, getattr(),
# setattr(), delattr(), vars(), globals() and locals() join them: each turns a string into a name, which is
# how __builtins__ and the dunder attributes below would otherwise be reached.
_ESCAPES: dict[str, str] = {
    "exit": "calling exit()",
    "quit": "calling quit()",
    "exec": "calling exec()",
    "eval": "calling eval()",
    "__import__": "calling __import__()",
    "compile": "calling compile()",
    "breakpoint": "calling breakpoint()",
    "help": "calling help()",
}
_STRING_LOOKUPS: dict[str, str] = {
    "getattr": "calling getattr()",
    "setattr": "calling setattr()",
    "delattr": "calling delattr()",
    "vars": "calling vars()",
    "globals": "calling globals()",
    "locals": "calling locals()",
}

FORBIDDEN_CALLS_BY_PROJECT: dict[int, dict[str, str]] = {
    2: {"open": "opening a file"},
    3: {"open": "opening a file", **_ESCAPES},
    # Project 4 allows open() (Chapter 8) inside a with statement.
    4: {**_ESCAPES, **_STRING_LOOKUPS},
    5: {**_ESCAPES, **_STRING_LOOKUPS},
}

# These names are flagged wherever they are used, not only when called
# directly, so `loader = __import__` or `e = eval` does not slip past. exit
# and quit are left to the call check: a student may reasonably name a
# variable `exit`, and calling exit through another name gains nothing.
FLAG_ANY_USE: set[str] = {"exec", "eval", "__import__", "compile",
                           "breakpoint", "help", *_STRING_LOOKUPS}

# Label printed beside a forbidden call. Anything not listed is Ch. 8.
CALL_CHAPTER_REF: dict[str, str] = {
    "open": "Ch. 8",
    **{name: "not allowed in projects" for name in _ESCAPES},
    **{name: "not allowed in projects" for name in _STRING_LOOKUPS},
}

# Names and attributes that start and end with two underscores reach the
# interpreter's internals (__builtins__, __class__, __subclasses__,
# __globals__ and the like), so every project flags them. The ones below are
# the ones the book teaches: constructors and __str__ (Ch. 9 and 10), the
# operator methods of 9.8, and __name__ compared to "__main__".
ALLOWED_DUNDER_NAMES: set[str] = {"__name__"}
ALLOWED_DUNDER_ATTRIBUTES: set[str] = {
    "__init__", "__str__", "__repr__", "__name__",
    "__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__",
    "__add__", "__sub__", "__mul__", "__truediv__", "__floordiv__",
    "__mod__", "__pow__", "__abs__", "__int__", "__float__",
    "__and__", "__or__",
}


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


# Constructs a project must CONTAIN. The forbidden map above stops students
# reaching ahead; this stops them falling short. Three of Project 2's stated
# requirements (an elif, a compound boolean, a numeric comparison) are
# invisible in program output, so an input/output test cannot check them. They
# are plain in the AST.
#
# Each entry maps a key to (human description, predicate over the parsed tree).
def _has_elif(tree: ast.AST) -> bool:
    """`elif` parses as an If whose orelse is exactly one If."""
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and len(node.orelse) == 1 \
                and isinstance(node.orelse[0], ast.If):
            return True
    return False


def _has_boolop(tree: ast.AST) -> bool:
    """A compound condition joined by `and` or `or`."""
    return any(isinstance(n, ast.BoolOp) for n in ast.walk(tree))


def _has_ordering_compare(tree: ast.AST) -> bool:
    """A <, <=, > or >= comparison, which is how a numeric tracker is tested.

    Equality is excluded deliberately: every student compares the choice
    strings with ==, so == proves nothing about the numeric requirement.
    """
    ordering = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and any(
                isinstance(op, ordering) for op in node.ops):
            return True
    return False


def _has_loop(tree: ast.AST) -> bool:
    """A while or for loop."""
    return any(isinstance(n, (ast.While, ast.For)) for n in ast.walk(tree))


# The string methods taught in zyBooks 6.3 and 6.4. Only these count toward
# Project 3's "two distinct string methods". The check is by name, so a list's
# .count() would also count; an AST cannot tell the receiver's type.
CH6_STRING_METHODS: set[str] = {
    "replace", "find", "rfind", "count", "isalnum", "isdigit", "islower",
    "isupper", "isspace", "startswith", "endswith", "capitalize", "lower",
    "upper", "strip", "title", "split", "join",
}


def _has_two_string_methods(tree: ast.AST) -> bool:
    """Calls to at least two DIFFERENT Chapter 6 string methods."""
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in CH6_STRING_METHODS:
            used.add(node.func.attr)
    return len(used) >= 2


# Project 4: the engine imports four functions by name, and 7.16 makes a
# docstring part of each one.
P4_FUNCTIONS = ["load_questions", "save_score", "load_scores",
                "display_leaderboard"]


def _top_level_def(tree: ast.AST, name: str):
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _defines(name: str):
    return lambda tree: _top_level_def(tree, name) is not None


def _documents(name: str):
    def predicate(tree: ast.AST) -> bool:
        node = _top_level_def(tree, name)
        return node is not None and bool((ast.get_docstring(node) or "").strip())
    return predicate


# Project 5: at least five classes, one class that inherits from another class
# in the same file, two classes that reach Exception, and a raise statement.
# Inheritance is read from the class statement only, so both ways of calling
# the base constructor, super().__init__(...) and Character.__init__(self,
# ...), satisfy it; neither is looked for.
BUILTIN_EXCEPTIONS: set[str] = {
    name for name, value in vars(builtins).items()
    if isinstance(value, type) and issubclass(value, Exception)
}


def _class_bases(tree: ast.AST) -> dict[str, list[str]]:
    """Each class defined in the file, mapped to the names of its bases."""
    bases: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    names.append(base.attr)
            bases[node.name] = names
    return bases


def _has_five_classes(tree: ast.AST) -> bool:
    """At least five class statements."""
    return sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)) >= 5


def _has_in_file_subclass(tree: ast.AST) -> bool:
    """A class whose base is another class defined in this file."""
    bases = _class_bases(tree)
    return any(b in bases and b != name
               for name, parents in bases.items() for b in parents)


def _has_two_exception_classes(tree: ast.AST) -> bool:
    """Two classes that inherit from Exception or any built-in exception
    under it (ValueError and the like), directly or through another class in
    this file (a shared GameError base counts)."""
    bases = _class_bases(tree)

    def reaches(name: str, seen: set[str]) -> bool:
        if name in seen:
            return False
        seen.add(name)
        for parent in bases.get(name, []):
            if parent not in bases and parent in BUILTIN_EXCEPTIONS:
                return True
            if reaches(parent, seen):
                return True
        return False

    return sum(reaches(name, set()) for name in bases) >= 2


def _has_raise(tree: ast.AST) -> bool:
    """A raise statement."""
    return any(isinstance(n, ast.Raise) for n in ast.walk(tree))


REQUIRED_BY_PROJECT: dict[int, list[tuple[str, str, object]]] = {
    2: [
        ("elif", "at least one elif", _has_elif),
        ("boolop", "a compound condition using and or or", _has_boolop),
        ("ordering", "a numeric comparison using <, <=, > or >=",
         _has_ordering_compare),
    ],
    3: [
        ("loop", "a while loop or a for loop", _has_loop),
        ("methods", "at least two different string methods from "
         "Chapter 6 (sections 6.3 and 6.4)", _has_two_string_methods),
    ],
    4: [(f"def_{name}", f"a function named {name} at the top level of the "
         "file", _defines(name)) for name in P4_FUNCTIONS]
       + [(f"doc_{name}", f"a docstring in {name}", _documents(name))
          for name in P4_FUNCTIONS],
    5: [
        ("classes", "at least five classes", _has_five_classes),
        ("subclass", "a class that inherits from another class in your file",
         _has_in_file_subclass),
        ("exceptions", "two classes that inherit from Exception",
         _has_two_exception_classes),
        ("raise", "a raise statement", _has_raise),
    ],
}


# Rules about WHERE things sit, reported as violations with a line number.
# Project 4's grader imports the file, so anything at the top level other than
# a def runs on import (a stray input() hangs every test). And 8.6 teaches
# `with`: nothing in the output shows whether a file was closed, so the rule
# "every open() is the target of a with" can only be checked here. Any use of
# the name open other than that call is flagged too, so `f = open` cannot
# carry it outside a with.
def _p4_structure(tree: ast.AST) -> list[tuple[int, str, str]]:
    found = []
    for index, node in enumerate(tree.body):
        if isinstance(node, ast.FunctionDef):
            continue
        if index == 0 and isinstance(node, ast.Expr) \
                and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            continue
        found.append((node.lineno, "code outside a function (only def "
                      "statements belong at the top level)", "project rule"))
    allowed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            for item in node.items:
                expr = item.context_expr
                if isinstance(expr, ast.Call) \
                        and isinstance(expr.func, ast.Name):
                    allowed.add(id(expr.func))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "open" \
                and id(node) not in allowed:
            found.append((node.lineno, "open() that is not the target of a "
                          "with statement", "Ch. 8.6"))
    return found


STRUCTURE_BY_PROJECT: dict[int, object] = {
    4: _p4_structure,
}

CHAPTER_REF: dict[str, str] = {
    "FunctionDef":      "Ch. 7",
    "AsyncFunctionDef": "Ch. 7",
    "Lambda":           "Ch. 7",
    "ClassDef":         "Ch. 9",
    "For":              "Ch. 5",
    "While":            "Ch. 5",
    "If":               "Ch. 4",
    "IfExp":            "Ch. 4",
    # match/case and comprehensions are taught in no chapter of this book.
    # import is taught in 2.8-2.10; banning it is policy, not chapter order.
    "Match":            "not taught in this course",
    "Import":           "not allowed in projects",
    "ImportFrom":       "not allowed in projects",
    "Try":              "Ch. 11",
    "TryStar":          "Ch. 11",
    "Raise":            "Ch. 11",
    "With":             "Ch. 8",
    "ListComp":         "not taught in this course",
    "DictComp":         "not taught in this course",
    "SetComp":          "not taught in this course",
    "GeneratorExp":     "not taught in this course",
    "Await":            "not taught in this course",
    "Yield":            "not taught in this course",
    "YieldFrom":        "not taught in this course",
}

# Label overrides for one project. Projects 1-3 print "Ch. 7" for lambda and
# async def. From Project 4, which covers Chapter 7, that label would be
# false: no chapter teaches either.
CHAPTER_REF_BY_PROJECT: dict[int, dict[str, str]] = {
    4: {"Lambda": "not taught in this course",
        "AsyncFunctionDef": "not taught in this course"},
    5: {"Lambda": "not taught in this course",
        "AsyncFunctionDef": "not taught in this course"},
}

# Files provided to students - never scan these.
# check.py is the local test runner shipped in every starter. It uses imports,
# functions, loops and conditionals by design, so scanning it would report
# violations against every student.
EXCLUDED_FILES: set[str] = {
    "cs163_fall2026_concept_checker.py",
    "concept_checker.py",
    "check.py",
    # The Project 4 game engine, provided and imported by nothing it checks.
    "quiz_engine.py",
    # The Project 5 engine imports from characters.py by design.
    "battle.py",
    # Test infrastructure
    "conftest.py",
    "test_*.py",
    "*_test.py",
}

# One initial commit is created by "Use this template", so the floor of 4 total
# means 3 student commits. Kept in step with the autograder's commit-count test:
#     git rev-list --no-merges --count HEAD >= 4
MIN_COMMITS = 4


def should_exclude(filepath: str) -> bool:
    name = os.path.basename(filepath)
    for pattern in EXCLUDED_FILES:
        if "*" in pattern:
            if fnmatch.fnmatch(name, pattern):
                return True
        elif name == pattern:
            return True
    return False


def read_source(filepath: str) -> str:
    # utf-8-sig, so a file saved with a byte order mark still parses.
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def check_file(filepath: str, project: int) -> list[dict]:
    forbidden = FORBIDDEN_BY_PROJECT.get(project, {})
    methods = FORBIDDEN_METHODS_BY_PROJECT.get(project, set())
    calls = FORBIDDEN_CALLS_BY_PROJECT.get(project, {})
    structure = STRUCTURE_BY_PROJECT.get(project)
    labels = {**CHAPTER_REF, **CHAPTER_REF_BY_PROJECT.get(project, {})}
    try:
        source = read_source(filepath)
    except OSError as e:
        return [{"file": os.path.basename(filepath), "line": 0,
                 "node_type": "READ_ERROR",
                 "description": f"Could not read file: {e}", "chapter": "N/A"}]
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    name = os.path.basename(filepath)
    # The Name node of every direct call, so a call is reported once, by the
    # call check, and not again as a bare use of the name.
    called = {id(node.func) for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    violations = []
    for node in ast.walk(tree):
        node_type = type(node).__name__
        if node_type in forbidden:
            violations.append({
                "file": name,
                "line": getattr(node, "lineno", 0),
                "node_type": node_type,
                "description": forbidden[node_type],
                "chapter": labels.get(node_type, "?"),
            })
        # Independent `if`s, not an elif chain, so a later rule can never be
        # swallowed by an earlier one.
        if calls and isinstance(node, ast.Call) and isinstance(
                node.func, ast.Name) and node.func.id in calls:
            violations.append({
                "file": name,
                "line": getattr(node, "lineno", 0),
                "node_type": "ForbiddenCall",
                "description": calls[node.func.id],
                "chapter": CALL_CHAPTER_REF.get(node.func.id, "Ch. 8"),
            })
        if isinstance(node, ast.Name) and id(node) not in called \
                and node.id in calls and node.id in FLAG_ANY_USE:
            violations.append({
                "file": name,
                "line": getattr(node, "lineno", 0),
                "node_type": "ForbiddenName",
                "description": f"using {node.id} without calling it directly",
                "chapter": CALL_CHAPTER_REF.get(node.id, "Ch. 8"),
            })
        if isinstance(node, ast.Name) and _is_dunder(node.id) \
                and node.id not in ALLOWED_DUNDER_NAMES \
                and node.id not in calls:
            violations.append({
                "file": name,
                "line": getattr(node, "lineno", 0),
                "node_type": "DunderName",
                "description": f"the name {node.id}",
                "chapter": "not allowed in projects",
            })
        if isinstance(node, ast.Attribute) and _is_dunder(node.attr) \
                and node.attr not in ALLOWED_DUNDER_ATTRIBUTES:
            violations.append({
                "file": name,
                "line": getattr(node, "lineno", 0),
                "node_type": "DunderAttribute",
                "description": f"the attribute .{node.attr}",
                "chapter": "not allowed in projects",
            })
        if methods and isinstance(node, ast.Call) \
                and isinstance(node.func, ast.Attribute) \
                and node.func.attr in methods:
            violations.append({
                "file": name,
                "line": getattr(node, "lineno", 0),
                "node_type": "StringMethod",
                "description": f"string method .{node.func.attr}()",
                "chapter": "Ch. 6",
            })
    if structure:
        for line, description, chapter in structure(tree):
            violations.append({
                "file": name,
                "line": line,
                "node_type": "Structure",
                "description": description,
                "chapter": chapter,
            })
        violations.sort(key=lambda v: v["line"])
    return violations


def check_required(filepath: str, project: int) -> list[dict]:
    """Report the required constructs this file is MISSING."""
    required = REQUIRED_BY_PROJECT.get(project, [])
    if not required:
        return []
    try:
        tree = ast.parse(read_source(filepath), filename=filepath)
    except (OSError, SyntaxError):
        # A file that will not parse cannot be shown to contain anything.
        return [{"file": os.path.basename(filepath), "key": key,
                 "description": desc} for key, desc, _ in required]

    missing = []
    for key, desc, predicate in required:
        if not predicate(tree):
            missing.append({"file": os.path.basename(filepath),
                            "key": key, "description": desc})
    return missing


def is_shallow() -> bool:
    """True if this is a shallow clone, where the commit count is meaningless.

    CI checkouts often default to fetch-depth 1. In that case `git rev-list
    --count HEAD` returns 1 regardless of how many commits the student made,
    which would flag every student in the class as low-commit.
    """
    try:
        r = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() == "true"
    except Exception:
        return False


def get_commit_count() -> int:
    """Student-authored commits, excluding merge commits.

    Matches the autograder's check, which counts with
    `git rev-list --no-merges --count HEAD`.
    """
    try:
        result = subprocess.run(
            ["git", "rev-list", "--no-merges", "--count", "HEAD"],
            capture_output=True, text=True, timeout=10)
        return int(result.stdout.strip())
    except Exception:
        return -1


def collect_files(explicit: list[str]) -> list[str]:
    if explicit:
        return [f for f in explicit if not should_exclude(f) and os.path.isfile(f)]
    found = []
    for p in Path(".").rglob("*.py"):
        if should_exclude(str(p)):
            continue
        # Compare path PARTS, not a string prefix. On Windows, rglob yields
        # backslash-separated paths, so startswith("tests/") never matched.
        parts = set(p.parts)
        if ".github" in parts or "tests" in parts or "__pycache__" in parts:
            continue
        found.append(str(p))
    return sorted(found)


def main() -> None:
    parser = argparse.ArgumentParser(description="CS 163 Fall 2026 Concept Checker")
    parser.add_argument("--project", type=int, required=True, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when anything is flagged, so an "
                             "autograder can score this as a test")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    files = collect_files(args.files)
    all_violations: list[dict] = []
    for filepath in files:
        all_violations.extend(check_file(filepath, args.project))

    # A required construct counts as present if ANY scanned file has it.
    required = REQUIRED_BY_PROJECT.get(args.project, [])
    satisfied: set[str] = set()
    for filepath in files:
        missing_here = {m["key"] for m in check_required(filepath, args.project)}
        satisfied |= {key for key, _, _ in required} - missing_here
    missing = [{"key": key, "description": desc}
               for key, desc, _ in required if key not in satisfied]
    if required and not files:
        missing = [{"key": key, "description": desc} for key, desc, _ in required]

    commit_count = get_commit_count()
    shallow = is_shallow()
    # Never flag on a shallow clone: the count is capped at 1 by the checkout
    # depth, not by the student, so flagging would hit the whole class.
    low_commits = (not shallow) and (commit_count >= 0) and (commit_count < MIN_COMMITS)

    report = {
        "project":         args.project,
        "checked_at":      datetime.now(timezone.utc).isoformat(),
        "files_checked":   [os.path.basename(f) for f in files],
        "commit_count":    commit_count,
        "shallow_clone":   shallow,
        "low_commit_flag": low_commits,
        "violation_count": len(all_violations),
        "violations":      all_violations,
        "missing_required": missing,
        "flag_for_review": len(all_violations) > 0 or low_commits or bool(missing),
    }

    with open("concept_check_report.json", "w") as f:
        json.dump(report, f, indent=2)

    if report["flag_for_review"]:
        print("=" * 60)
        print(f"CONCEPT CHECK - Project {args.project}")
        print(f"Files:   {', '.join(report['files_checked']) or 'none found'}")
        print(f"Commits: {commit_count if commit_count >= 0 else 'unknown'}")
        print("=" * 60)
        if all_violations:
            print(f"VIOLATIONS ({len(all_violations)} found):")
            for v in all_violations:
                print(f"  {v['file']}:{v['line']}  {v['description']}  [{v['chapter']}]")
        if missing:
            print(f"MISSING REQUIRED ({len(missing)}):")
            for m in missing:
                print(f"  your program does not contain {m['description']}")
        if low_commits:
            print(f"LOW COMMIT COUNT: {commit_count} (expected >= {MIN_COMMITS})")
        print("=" * 60)
        print("Flagged for instructor review. See concept_check_report.json.")
    else:
        print(f"[concept check] Project {args.project} - "
              f"{len(files)} file(s), {commit_count} commits - no flags.")

    # --strict makes this scoreable by an autograder. A low commit count is
    # deliberately NOT fatal here: the autograder scores commits separately,
    # and a shallow CI checkout would otherwise fail every student.
    if args.strict and (all_violations or missing):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
