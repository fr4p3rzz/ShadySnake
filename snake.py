from compushady import Buffer, HEAP_DEFAULT, HEAP_READBACK, HEAP_UPLOAD, Compute, config
import glfw
import compushady.formats
from compushady.shaders import hlsl
import struct
import platform
import random
import functions, sn_tuning

# Init
compushady.config.set_debug(True)
print('Using device', compushady.get_current_device().name)

# Our game world
target = compushady.Texture2D(sn_tuning.window_width, sn_tuning.window_height, compushady.formats.B8G8R8A8_UNORM)

# Creating necessary items
food = functions.generate_food(target)
snake = functions.generate_head(target)
content_to_render = [food, snake]

# Necessary variables
snake_tails = 0
food_counter = 0
direction = -1
axis = 1
timer = sn_tuning.timer

# Support to d3d11
quads_staging_buffer = compushady.Buffer(16 * 4 * 4, compushady.HEAP_UPLOAD)
quads_buffer = compushady.Buffer(
    quads_staging_buffer.size, format=compushady.formats.R32G32B32A32_SINT)

# Rendering algorithm
shader = hlsl.compile("""
struct data
{
    uint4 rendered_obj;
    uint4 color;
};
StructuredBuffer<data> quads : register(t0);
RWTexture2D<float4> target : register(u0);
[numthreads(8, 8, 8)]
void main(int3 tid : SV_DispatchThreadID)
{
    data quad = quads[tid.z];
    if (tid.x > quad.rendered_obj[0] + quad.rendered_obj[2])
        return;
    if (tid.x < quad.rendered_obj[0])
        return;
    if (tid.y < quad.rendered_obj[1])
        return;
    if (tid.y > quad.rendered_obj[1] + quad.rendered_obj[3])
        return;
    target[tid.xy] = float4(quad.color);
}
""")

compute = compushady.Compute(shader, srv=[quads_buffer], uav=[target])

# A super simple clear screen procedure
clear_screen = compushady.Compute(hlsl.compile("""
RWTexture2D<float4> target : register(u0);

[numthreads(8, 8, 1)]
void main(int3 tid : SV_DispatchThreadID)
{
    target[tid.xy] = float4(0, 0, 0, 0);
}
"""), uav=[target])

# Initialising our window system
glfw.init()

# we do not want implicit OpenGL!
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

# Creating window
window = glfw.create_window(target.width, target.height, 'Snake', None, None)

# Selecting GPUs API based on current system
if platform.system() == 'Windows':
    swapchain = compushady.Swapchain(glfw.get_win32_window(
        window), compushady.formats.B8G8R8A8_UNORM, 2)
elif platform.system() == 'Darwin':
    from compushady.backends.metal import create_metal_layer
    ca_metal_layer = create_metal_layer(glfw.get_cocoa_window(window), compushady.formats.B8G8R8A8_UNORM)
    swapchain = compushady.Swapchain(
        ca_metal_layer, compushady.formats.B8G8R8A8_UNORM, 2)
else:
    swapchain = compushady.Swapchain((glfw.get_x11_display(), glfw.get_x11_window(
        window)), compushady.formats.B8G8R8A8_UNORM, 2)


# Game Loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    if glfw.get_key(window, glfw.KEY_A) | glfw.get_key(window, glfw.KEY_LEFT):
        axis = 0
        direction = -1
    if glfw.get_key(window, glfw.KEY_D) | glfw.get_key(window, glfw.KEY_RIGHT):
        axis = 0
        direction = 1
    if glfw.get_key(window, glfw.KEY_S) | glfw.get_key(window, glfw.KEY_DOWN):
        axis = 1
        direction = 1
    if glfw.get_key(window, glfw.KEY_W  | glfw.get_key(window, glfw.KEY_UP)):
        axis = 1
        direction = -1
    if glfw.get_key(window, glfw.KEY_ESCAPE):
        swapchain = None  
        glfw.terminate()

    # Moving each body part of the snake 
    timer -= sn_tuning.timer_offset * sn_tuning.snake_speed
    if timer <= 0:
        if len(content_to_render) > 2:
            for i in range(len(content_to_render)-1, 1, -1):
                content_to_render[i][0] = content_to_render[i-1][0]
                content_to_render[i][1] = content_to_render[i-1][1]

        snake[axis] += direction * sn_tuning.snake_speed
        timer = 1000

    clear_screen.dispatch(target.width // 8, target.height // 8, 1)

    # Eat the food
    if functions.collide(snake, food):
        functions.update_food(food, target)
        food_counter += 1

        # We want to create tails only until our buffer limit is reached
        if snake_tails < sn_tuning.snake_max_length:
            snake_tail = functions.generate_tail(content_to_render, snake_tails)
            content_to_render.append(snake_tail)
            snake_tails += 1

        # We increase the speed only until the maximum possible is reached
        if sn_tuning.timer_offset < sn_tuning.snake_speed:
            sn_tuning.timer_offset += 1

    # Pacman-effect on window limits
    functions.check_borders(snake, target)

    # Render the scene
    quads_staging_buffer.upload(functions.pack_content(content_to_render))
    quads_staging_buffer.copy_to(quads_buffer)
    compute.dispatch(target.width // 8, target.height // 8, 1)
    swapchain.present(target)

# Close the application
swapchain = None  # this ensures the swapchain is destroyed before the window
glfw.terminate()
