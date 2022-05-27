# Here are custom functions used
import random

def is_ate(snake, food):
    if snake[0] + snake[2] < food[0]:
        return False
    if snake[0] > food[0] + food[2]:
        return False
    if snake[1] + snake[3] < food[1]:
        return False
    if snake[1] > food[1] + food[3]:
        return False
    return True

def food_new_color(food):
    r = random.randint(0, 1)
    g = random.randint(0, 1)
    b = random.randint(0, 1)
    
    if r == g == b == 0:
        r = 1

    food[4] = r
    food[5] = g
    food[6] = b