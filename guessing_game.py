# Name: Alicia Colon
# Date: 16 October 2026
# Description: Guessing Game
import random

lowest = 0
highest = 100
guesses = 0
total = 0
running = True
guesses_max = int(input("Enter maximum guesses: ").strip())
answer = int(input("Enter the secret number: ").strip())
secret = answer

if lowest >= highest or guesses_max <= 0:
    print("Invalid setup. Ending game.")
    running = False

if running:
    answer = random.randint(lowest, highest)

while running:
    print(f"Guess {guesses + 1} of {guesses_max}: ")
    guess = input(f"Guess a number between {lowest} and {highest}: ")
    guess = guess.strip()

    if guess.isdigit():
        guess = int(guess)
        guesses +=1
        total += guess
    else:
        print("Invalid input. Ending game.")
        break

    if guess < lowest or guess > highest:
        print("Invalid input. Ending game.")
        running = False

    if guess < answer:
        print("Too low.")
        print(f"Average guess so far: {total / guess:.2f}")
        
    elif guess > answer:
        print("Too high.")
        print(f"Average guess so far: {total / guess:.2f}")
        
    elif guess == answer:
        print(f"You got it! Guesses used: {guesses}")
        print(f"Average guess so far: {total / guess:.2f}")
        running = False

    if guesses == guesses_max and running:
        print(f"Out of guesses. The number was {secret}.")
        running = False