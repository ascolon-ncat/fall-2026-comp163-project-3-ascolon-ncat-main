# Name: Alicia Colon
# Date: 16 October 2026
# Description: Guessing Game
import random

lowest = 0
highest = 100
answer = random.randint(lowest, highest)
guesses = 0
running = True
guesses_max = 2

while running:
    guess = input(f"Guess a number between {lowest} and {highest}: ")
    if guess.isdigit():
        guess = int(guess)
        guesses +=1
    print(f"Guess {guesses} of {guesses_max}")

    if guess < lowest or guess > highest:
        print("Invalid input. Ending game.")
        break

    if guess < answer:
        print("Too low.")
    elif guess > answer:
        print("Too high.")
        print(f"Average guess so far: {guesses / 2:.2f}")
    else:
        print(f"You got it! Guesses used: {guesses}")
        print(f"Average guess so far: {guesses / 2:.2f}")
        running = False
    if guesses == guesses_max:
        print(f"Out of guesses. The number was {answer}.")
        break