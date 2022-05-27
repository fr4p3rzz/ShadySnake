
from compushady import Buffer, HEAP_DEFAULT, HEAP_READBACK, HEAP_UPLOAD, Compute, config
import glfw
import compushady.formats
from compushady.shaders import hlsl
import struct
import platform
import random
import functions, sn_tuning

compushady.config.set_debug(True)

print('Using device', compushady.get_current_device().name)

target = compushady.Texture2D(sn_tuning.window_width, sn_tuning.window_height, compushady.formats.B8G8R8A8_UNORM) # our game world

# we need space for 4 quads (uint4 * 3)
snake = [random.randint(sn_tuning.snake_offset, 
        target.width - sn_tuning.snake_offset), 
        random.randint(sn_tuning.snake_offset, 
        target.height - sn_tuning.snake_offset), 
        sn_tuning.snake_size_x, 
        sn_tuning.snake_size_y, 1, 1, 1, 1]
snake_speed = sn_tuning.snake_starting_speed # Snake speed
food = [random.randint(sn_tuning.food_offset, 
        target.width - sn_tuning.food_offset), 
        random.randint(sn_tuning.food_offset, 
        target.height - sn_tuning.food_offset), 
        sn_tuning.food_size_x, 
        sn_tuning.food_size_y, 0, 1, 0, 1] 
food_counter = 0


# Support to d3d11
quads_staging_buffer = compushady.Buffer(8 * 4 * 3, compushady.HEAP_UPLOAD)
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
[numthreads(8, 8, 3)]
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

# a super simple clear screen procedure
clear_screen = compushady.Compute(hlsl.compile("""
RWTexture2D<float4> target : register(u0);

[numthreads(8, 8, 1)]
void main(int3 tid : SV_DispatchThreadID)
{
    target[tid.xy] = float4(0, 0, 0, 0);
}
"""), uav=[target])

glfw.init()
# we do not want implicit OpenGL!
glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)

window = glfw.create_window(target.width, target.height, 'Snake', None, None)

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


direction = -1
axis = 1
while not glfw.window_should_close(window):
    glfw.poll_events()
    effect_variation = random.randrange(0, 2)
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

    snake[axis] += direction * snake_speed
    clear_screen.dispatch(target.width // 8, target.height // 8, 1)

    # Eat the food
    if functions.is_ate(snake, food):
        food_counter += 1
        snake_speed += sn_tuning.snake_increment_speed
        food[0] = random.randint(20, target.width - 20)
        food[1] = random.randint(20, target.height - 20)
        functions.food_new_color(food)
   
    # Pacman-effect on window limits
    if snake[0] < 0:
        snake[0] = target.width 
    if snake[0] > target.width:
        snake[0] = 0
    if snake[1] < 0:
        snake[1] = target.height 
    if snake[1] > target.height:
        snake[1] = 0

    quads_staging_buffer.upload(struct.pack('16i', *snake, *food))
    quads_staging_buffer.copy_to(quads_buffer)
    compute.dispatch(target.width // 8, target.height // 8, 1)
    swapchain.present(target)

swapchain = None  # this ensures the swapchain is destroyed before the window
glfw.terminate()

