# COMP 163 - Project 3: Number Guessing Game

**Chapters 5 and 6: Loops and Strings**

Write a Python program for a two-player number guessing game. Player 1 types a
secret number and a maximum number of guesses. Player 2 guesses until they get
it or run out.

> **If anything here disagrees with the instructions on Canvas, Canvas is
> correct.** This file exists so the exact required output sits next to your
> code. Canvas has the full assignment description, the grading breakdown, the
> due date, and any updates posted after the project was released.

Your file is `guessing_game.py`.

## Why two players

The secret comes from Player 1 so that every game has a known answer. The
autograder plays both players. It types the secret, so it knows what every hint
should say.

## Input

Your program reads these, one per line, in this order:

1. the secret number
2. the maximum number of guesses
3. then one guess per round

Word your two setup prompts however you like.

A value is **valid** when, ignoring any spaces before or after it, it is one or
more of the digits 0 to 9. So `42` is valid, and so is 42 with spaces before
or after it. Your program must accept those spaces on every input. Signs,
decimal points, words and empty lines are invalid.

When the maximum is valid, it is always 1 or more.

## Required output

These lines must appear exactly as written, with `<k>`, `<max>`, `<avg>` and
`<secret>` replaced by numbers. Anything else your program prints is up to you.

The prompt for each round, where `<k>` is the guess number starting at 1. It
ends with a colon and one space:

```
Guess <k> of <max>: 
```

A wrong guess prints one of these. Compare the guess and the secret as numbers.

```
Too high.
```

```
Too low.
```

A correct guess prints this, where `<k>` is the number of guesses used:

```
You got it! Guesses used: <k>
```

After **every** valid guess, including the correct one, print the average of all
valid guesses so far, with exactly two digits after the decimal point, such as
`15.00` or `7.50`:

```
Average guess so far: <avg>
```

When Player 2 has used every guess without getting it, print this after the
last average line:

```
Out of guesses. The number was <secret>.
```

The secret prints as a number, so a secret typed as `07` prints `7`.

## Rules

- Player 2 gets at most `<max>` guesses. A correct guess ends the game, even
  with guesses left.
- If **any** input is invalid, whether the secret, the maximum or a guess,
  print this line and end the game:

  ```
  Invalid input. Ending game.
  ```

  No round may start after it.
- A run that ends in a win must not print the loss line or the invalid line.
- A run that ends in a loss must not print the win line.

## What your program must contain

These are checked by reading your code, not your output:

1. **A `while` loop or a `for` loop.**
2. **At least two different string methods** from sections 6.3 and 6.4. These
   are the ones that count: `replace`, `find`, `rfind`, `count`, `isalnum`,
   `isdigit`, `islower`, `isupper`, `isspace`, `startswith`, `endswith`,
   `capitalize`, `lower`, `upper`, `strip`, `title`, `split`, `join`.

## What you may use

**This project covers Chapters 5 and 6.**

You may use anything from Chapters 1 through 6, including `while`, `for`,
`range()`, `break`, `continue`, loop `else`, `enumerate()`, string slicing,
f-string formatting, and the string methods above.

These are not allowed:

| Not allowed here | Why |
|---|---|
| Functions you define yourself (`def`, `lambda`) | Chapter 7 |
| Opening or reading files (`open()`, `with`) | Chapter 8 |
| Classes | Chapter 9 |
| `try` / `except` and `raise` | Chapter 11 |
| `import` of anything, `__import__()`, `exec()`, `eval()` | Not allowed in projects |
| `exit()` and `quit()` | Not allowed in projects |
| `compile()`, `breakpoint()` and `help()` | Not allowed in projects |
| Names that start and end with two underscores, such as `__builtins__` or `__class__`, other than `__name__` | Not allowed in projects |
| Comprehensions, generator expressions and `match` | Not taught in this course |

The autograder checks this on every push, and the check is worth 5 points, so
using any of these costs you those 5 straight away. That is not the whole cost.
A confirmed use of anything in this table is a zero on the project once I
review it.

## AI

No AI on this project, with one exception. You may use it as a rubber duck:
explain your problem to it, and take a hint from it once you have struggled
long enough to have earned one. It does not write your code.

## Check your work before you push

```
python3 check.py
```

This runs every check the autograder runs, except the commit count, and tells
you which requirement any failure came from. If `check.py` is clean, the
autograder will be too.

## Grading

This repository is worth 40 points. The Project 3 Tech Interview is a separate
60-point grade, for 100 in total.

| Component | Points |
|---|---|
| File header filled in | 3 |
| At least 3 commits | 2 |
| Concept check (required and forbidden features) | 5 |
| A first-guess win | 4 |
| Hints compare numbers | 5 |
| Running average | 5 |
| A loss reveals the secret | 6 |
| A bad setup value stops the game | 3 |
| A bad guess stops the game | 4 |
| Spaces around input are accepted | 3 |
| **Total** | **40** |

### About the header

The first lines of `guessing_game.py` must be filled in:

```
# Name: Your Name
# Date: 2026-10-05
# Description: A short description of your program
```

The file ships with those labels blank. Blank scores nothing.

### About the commits

You get 2 points for making at least three commits. A commit is a save point.
When you break something at 11pm, the last commit that worked is how you get
back without starting over.

Commit when you finish a piece, not all at once at the end:

```
git add guessing_game.py
git commit -m "Setup inputs are read and validated"
git push
```


## Submitting

Due **Friday, October 16, 2026 at 11:59 PM**. Two steps, and you need both:

1. **Push to this repository.** Every push runs the checks automatically, and
   the most recent push before the deadline is what gets graded.
2. **Paste this repository's URL into the Canvas assignment.**

The URL by itself grades nothing. It tells me which repository is yours. It
looks something like:

```
https://github.com/COMP-163/fall-2026-comp163-project-3-yourusername
```

Copy it out of your browser's address bar rather than typing it.
