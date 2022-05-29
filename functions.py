# Here are custom functions used
import random
import struct
import sn_tuning

def pack_content(content_array):
    buffer = bytes(0)
    for item in content_array:
        items_to_patck = '{}i'.format(len(item))
        packed_item = struct.pack(items_to_patck, *item)
        buffer += packed_item
    return buffer

def check_borders(snake, target):
    if snake[0] < 0:
        snake[0] = target.width 
    if snake[0] > target.width:
        snake[0] = 0
    if snake[1] < 0:
        snake[1] = target.height 
    if snake[1] > target.height:
        snake[1] = 0

def collide(snake, item):
    if snake[0] + snake[2] < item[0]:
        return False
    if snake[0] > item[0] + item[2]:
        return False
    if snake[1] + snake[3] < item[1]:
        return False
    if snake[1] > item[1] + item[3]:
        return False
    return True

def update_food(food, target):
    food[0] = random.randint(sn_tuning.snake_offset, target.width - sn_tuning.snake_offset)
    food[1] = random.randint(sn_tuning.snake_offset, target.height - sn_tuning.snake_offset)
    food_new_color(food)

def food_new_color(food):
    r = random.randint(0, 1)
    g = random.randint(0, 1)
    b = random.randint(0, 1)
    
    if r == g == b == 0:
        r = 1

    food[4] = r
    food[5] = g
    food[6] = b

def generate_food(target):
    food = [random.randint(sn_tuning.food_offset, 
        target.width - sn_tuning.food_offset), 
        random.randint(sn_tuning.food_offset, 
        target.height - sn_tuning.food_offset), 
        sn_tuning.food_size_x, 
        sn_tuning.food_size_y, 0, 1, 0, 1]
    return food

def generate_head(target):
    snake_head = [random.randint(sn_tuning.snake_offset, target.width - sn_tuning.snake_offset), 
        random.randint(sn_tuning.snake_offset, target.height - sn_tuning.snake_offset), 
        sn_tuning.snake_size, 
        sn_tuning.snake_size, 
        1, 1, 1, 1]
    return snake_head

def generate_tail(content_to_render, snake_tails):
    new_tail = [content_to_render[len(content_to_render)-1][0], 
        content_to_render[len(content_to_render)-1][1]  - sn_tuning.snake_size * snake_tails,
        sn_tuning.snake_size, 
        sn_tuning.snake_size, 0, 1, 1, 1]
    return new_tail

def game_reset(content_to_render, target):
    if len(content_to_render) > 2:
        new_snake = generate_head(target)
        new_food = generate_food(target)

        content_to_render = [new_food, new_snake]
    return content_to_render

