#!/usr/bin/env python3
"""Run the same checks the autograder runs, on your own machine.

    python3 check.py

This is the whole autograder except the commit count, which only means
something once your work is pushed. If everything here says PASS, the
autograder will agree.

The patterns below are the autograder's own, so the two cannot drift apart.

Run it as often as you like. It never changes your code. It does write
concept_check_report.json, which git ignores.
"""
import hashlib
import os
import re
import subprocess
import sys

FILE = "guessing_game.py"
CHECKER = os.path.join("tests", "cs163_fall2026_concept_checker.py")

# The concept checker as provided, as a SHA-256 with line endings ignored.
# The autograder checks it before the concept check runs, and if it has
# changed, the concept check scores 0.
PROVIDED = {
    "tests/cs163_fall2026_concept_checker.py":
        "fb52b5b62ed0c335190b207155749131844268b4a1abce0d8476ad4ef3045825",
}

EOL = r"(?:\r?\n|\Z)"


def line(marker):
    return r"[\s\S]*" + marker + EOL


def has(marker):
    return r"(?=" + line(marker) + r")"


def never(text):
    return r"(?![\s\S]*" + text + r")"


HIGH = r"Too high\."
LOW = r"Too low\."
INVALID = r"Invalid input\. Ending game\."
WIN_ANY = r"You got it!"
LOSS_ANY = r"Out of guesses\."


def win(k):
    return r"You got it! Guesses used: " + str(k)


def avg(value):
    return r"Average guess so far: " + value.replace(".", r"\.")


def prompt(k, m):
    return r"Guess " + str(k) + r" of " + str(m) + r":"


NO_WIN = never(WIN_ANY)
NO_LOSS = never(LOSS_ANY)
NO_INVALID = never(INVALID)
NO_HINT = never(r"Too (?:high|low)\.")
TWO_AVERAGES = r"[\s\S]*Average guess so far:[\s\S]*Average guess so far:"

IO_TESTS = [
    ("First-guess win", 4, ["42", "5", "42"],
     r"\A" + NO_LOSS + NO_INVALID + NO_HINT
     + has(avg("42.00")) + line(win(1)),
     "Secret 42, maximum 5, first guess 42 must print "
     "You got it! Guesses used: 1 and Average guess so far: 42.00. It must "
     "not print Too high. or Too low., the loss line, or the invalid line."),
    ("Hints compare numbers", 5, ["42", "5", "70", "9", "42"],
     r"\A" + NO_LOSS + NO_INVALID
     + line(HIGH) + line(LOW) + line(win(3)),
     "Secret 42, maximum 5, guesses 70, 9, 42 must print Too high., then "
     "Too low., then You got it! Guesses used: 3."),
    ("Running average", 5, ["50", "4", "10", "25", "60", "50"],
     r"\A" + NO_LOSS + NO_INVALID + has(win(4))
     + line(avg("10.00")) + line(avg("17.50"))
     + line(avg("31.67")) + line(avg("36.25")),
     "Secret 50, maximum 4, guesses 10, 25, 60, 50 must print the averages "
     "10.00, 17.50, 31.67 and 36.25 in that order, and a correct fourth "
     "guess out of four is a win: You got it! Guesses used: 4."),
    ("Loss reveals the secret", 6, ["07", "3", "1", "2", "3", "7"],
     r"\A" + NO_WIN + NO_INVALID + never(prompt(4, 3))
     + line(LOW) + line(LOW) + line(LOW)
     + line(r"Out of guesses\. The number was 7\."),
     "Secret 07, maximum 3, guesses 1, 2, 3 must print Too low. three times "
     "and then Out of guesses. The number was 7. The test sends a fourth "
     "guess of 7; your program must not ask for it."),
    ("Bad setup stops the game", 3, ["42", "-5", "42"],
     r"\A" + NO_WIN + NO_LOSS + never(r"Guess 1 of") + line(INVALID),
     "A maximum of -5 must print Invalid input. Ending game. "
     "and no rounds at all."),
    ("Bad guess stops the game", 4, ["42", "5", "70", "abc", "42"],
     r"\A" + NO_WIN + NO_LOSS + never(prompt(3, 5))
     + r"(?!" + TWO_AVERAGES + r")"
     + has(avg("70.00")) + line(INVALID),
     "Secret 42, maximum 5, guesses 70 then abc must print one average "
     "(70.00), then Invalid input. Ending game. and no further rounds. The "
     "test sends a 42 after the abc; your program must not ask for it."),
    ("Spaces around input are accepted", 3, ["  42 ", " 3", "42  "],
     r"\A" + NO_LOSS + NO_INVALID
     + r"(?=[\s\S]*" + prompt(1, 3) + r")"
     + has(avg("42.00")) + line(win(1)),
     "Secret '  42 ', maximum ' 3', guess '42  ' (spaces included) are all "
     "valid and must play as 42, 3 and 42: Guess 1 of 3:, then a win."),
]


def run_program(stdin_lines):
    try:
        done = subprocess.run([sys.executable, FILE],
                              input="\n".join(stdin_lines) + "\n",
                              capture_output=True, text=True, timeout=15)
        return done.stdout, None
    except subprocess.TimeoutExpired:
        return "", "your program did not finish within 15 seconds"
    except OSError as err:
        return "", str(err)


def changed_provided_files():
    changed = []
    for name, expected in PROVIDED.items():
        try:
            with open(name, "rb") as handle:
                data = handle.read().replace(b"\r", b"")
        except OSError:
            changed.append(name)
            continue
        if hashlib.sha256(data).hexdigest() != expected:
            changed.append(name)
    return changed


def main():
    if not os.path.exists(FILE):
        print("There is no " + FILE + " in this folder. Are you in your repo?")
        return 1

    earned = 0
    possible = 0
    failures = []

    print("=" * 64)
    print("  Project 3 self-check")
    print("=" * 64)

    possible += 3
    # Must match the autograder, which greps the whole file:
    #     grep -qE "^# Name:[[:space:]]*[^[:space:]]" guessing_game.py
    # utf-8-sig drops a byte order mark, which the autograder also allows.
    with open(FILE, "r", encoding="utf-8-sig", errors="replace") as handle:
        source = handle.read()
    if re.search(r"^# Name:[^\S\r\n]*\S", source, re.MULTILINE):
        earned += 3
        print("  PASS   File header (3)")
    else:
        print("  FAIL   File header (3)")
        failures.append("Fill in your name on the first line, after '# Name:'")

    possible += 5
    changed = changed_provided_files()
    if not changed:
        result = subprocess.run([sys.executable, "-I", CHECKER, "--project",
                                 "3", "--strict", FILE],
                                capture_output=True, text=True)
    if changed:
        print("  FAIL   Concept check (5)")
        for name in changed:
            failures.append(
                name + " is not the file you were given, so the concept "
                "check scores 0 until it is put back. To restore it, run: "
                "git checkout $(git rev-list --max-parents=0 HEAD) -- "
                + name)
    elif result.returncode == 0:
        earned += 5
        print("  PASS   Concept check (5)")
    else:
        print("  FAIL   Concept check (5)")
        for text in result.stdout.splitlines():
            stripped = text.strip()
            if stripped.startswith("your program does not contain"):
                failures.append(stripped[0].upper() + stripped[1:])
            elif stripped.startswith(FILE + ":"):
                failures.append("Remove this, it is not allowed here: "
                                + stripped)

    for name, points, stdin_lines, pattern, hint in IO_TESTS:
        possible += points
        output, err = run_program(stdin_lines)
        if err:
            print("  FAIL   %s (%d)" % (name, points))
            failures.append(name + ": " + err)
            continue
        if re.match(pattern, output):
            earned += points
            print("  PASS   %s (%d)" % (name, points))
        else:
            print("  FAIL   %s (%d)" % (name, points))
            failures.append(name + ": " + hint)

    print("-" * 64)
    print("  %d of %d points from the checks that run locally"
          % (earned, possible))
    print("  Plus 2 points for committing at least 3 times as you work.")
    print("=" * 64)

    if failures:
        print("\nWhat to fix:\n")
        for item in failures:
            print("  - " + item)
        print()
        return 1

    print("\nEverything passes. Commit, push, and submit your repo URL "
          "in Canvas.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
