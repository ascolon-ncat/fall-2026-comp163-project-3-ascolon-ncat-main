# Name: Alicia Colon
# Date: 16 October 2026
# Description: Guessing Game
import random

lowest = 0
highest = 100
answer = random.randint(lowest, highest)
guesses = 0
running = True

while running:
    guess = input(f"Guess a number between {lowest} and {highest}: ")

    if guess.isdigit():
        guess = int(guess)
        guesses +=1

        if guess < lowest or guess > highest:
            print("Out of range.")
            print(f"Please enter a number between {lowest} and {highest}.")
        elif guess < answer:
            print("Too low.")
        elif guess > answer:
            print("Too high.")
        else:
            print(f"You got it! Guesses used: {guesses}")
            running = False
    if guesses == 2:
        print(f"Out of guesses. The number was {answer}.")

    else:
        print("Please enter a valid number.")
        print(f"Guess a number between {lowest} and {highest}: ")
