# Name: Alicia Colon
# Date: 16 October 2026
# Description: Guessing Game
import random

lowest = 0
highest = 100
guesses = 0
total = 0
running = True

secret = input("Enter the secret number: ").strip()
guesses_max = input("Enter maximum guesses: ").strip()

if not secret.isdigit() or not guesses_max.isdigit():
    print("Invalid input. Ending game.")
    running = False

else:
    answer = int(secret)
    guesses_max = int(guesses_max)

    if answer < lowest or answer > highest or guesses_max <= 0:
        print("Invalid input. Ending game.")
        running = False


while running:
    print(f"Guess {guesses + 1} of {guesses_max}: ")
    guess = input(f"Guess a number between {lowest} and {highest}: ")
    guess = guess.strip()

    if guess.isdigit():
        guess = int(guess)
    else:
        print("Invalid input. Ending game.")
        break

    if guess < lowest or guess > highest:
        print("Invalid input. Ending game.")
        break

    guesses += 1
    total += guess

    print(f"Average guess so far: {total / guesses:.2f}")

    if guess < answer:
        print("Too low.")
        
    elif guess > answer:
        print("Too high.")
        
    elif guess == answer:
        print(f"You got it! Guesses used: {guesses}")
        running = False

    if guesses == guesses_max and running:
        print(f"Out of guesses. The number was {secret}.")
        running = False