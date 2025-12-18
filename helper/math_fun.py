"""
Bugg Bot - Mathematical Visualization Module

Provides computational and visualization functions for mathematical content.
All functions return BytesIO buffers containing PNG/GIF images.

Features:
- plot_formula: Plot any mathematical formula using matplotlib
- generate_mandelbrot: Render the Mandelbrot fractal set (800x600, inferno colormap)
- generate_julia: Render Julia set fractals with custom complex constant c
- generate_spinning_cube: Create 3D animated cube with symbols on faces (60 frames)
- generate_cellular_war: Simulate Conway's Game of Life with two competing teams

All heavy computations designed to run in executor threads to avoid blocking Discord.
Uses NumPy for efficient array operations and PIL for image manipulation.
"""

# Import necessary libraries for mathematical computations and visualizations
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from matplotlib.colors import ListedColormap
from PIL import Image

# Function to plot a mathematical formula
def plot_formula(formula):
    """
    Plots a mathematical formula and returns a BytesIO buffer with the image.
    
    Args:
        formula: String containing a Python/NumPy expression (e.g., "x**2 + 3*x")
    
    Returns:
        BytesIO: Buffer containing the PNG image, or None if error
        str: Error message if failed, None if success
    """
    try:
        # Create the X-axis data (from -10 to 10 with 100 steps)
        x = np.linspace(-10, 10, 100)

        # Evaluate the user's formula
        # We allow 'x' and numpy functions in the evaluation context
        y = eval(formula, {"x": x, "np": np, "sin": np.sin, "cos": np.cos, "tan": np.tan, "sqrt": np.sqrt})

        # Setup the plot
        plt.figure(figsize=(8, 6))
        plt.plot(x, y, label=f"y = {formula}", color='cyan')
        
        # Add decorations
        plt.title(f"Graph of {formula}")
        plt.axhline(0, color='black', linewidth=1) # X-axis line
        plt.axvline(0, color='black', linewidth=1) # Y-axis line
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        # Save to memory buffer
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Clean up
        plt.close()

        return buf, None

    except Exception as e:
        return None, str(e)

# Function to generate the Mandelbrot fractal set
def generate_mandelbrot():
    """
    Generates the Mandelbrot fractal set.
    
    Returns:
        BytesIO: Buffer containing the PNG image of the Mandelbrot set
    """
    # Setup the complex plane
    width, height = 800, 600
    # Create a grid of complex numbers
    x = np.linspace(-2.0, 1.0, width)
    y = np.linspace(-1.0, 1.0, height)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y # This creates the complex number c = x + iy
    
    # The Mandelbrot algorithm (z = z^2 + c)
    Z = np.zeros_like(C)
    escape_time = np.zeros(C.shape, dtype=int)
    max_iter = 50 # Higher = more detail but slower
    
    for i in range(max_iter):
        # The core formula
        mask = np.abs(Z) < 2
        Z[mask] = Z[mask]**2 + C[mask]
        escape_time[mask] += 1

    # Colorize it using a heatmap
    plt.figure(figsize=(10, 8))
    plt.imshow(escape_time, cmap='inferno', extent=[-2, 1, -1, 1])
    plt.axis('off') # Hide axes
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    plt.close()
    return buf

# Function to generate a spinning ASCII cube animation
def generate_spinning_cube():
    """
    Generates ASCII art spinning cube using z-buffer algorithm.
    Ported from C implementation with rotation matrices.
    
    Returns:
        BytesIO: Buffer containing the GIF animation of rotating ASCII cube
    """
    import math
    from PIL import Image, ImageDraw, ImageFont
    
    # ASCII display dimensions
    width, height = 160, 44
    background_char = ' '
    cube_width = 20
    distance_from_cam = 100
    K1 = 40
    increment_speed = 0.6
    
    # Rotation angles
    A, B, C = 0.0, 0.0, 0.0
    
    def calculate_x(i, j, k, a, b, c):
        return (j * math.sin(a) * math.sin(b) * math.cos(c) - 
                k * math.cos(a) * math.sin(b) * math.cos(c) +
                j * math.cos(a) * math.sin(c) + 
                k * math.sin(a) * math.sin(c) + 
                i * math.cos(b) * math.cos(c))
    
    def calculate_y(i, j, k, a, b, c):
        return (j * math.cos(a) * math.cos(c) + 
                k * math.sin(a) * math.cos(c) -
                j * math.sin(a) * math.sin(b) * math.sin(c) + 
                k * math.cos(a) * math.sin(b) * math.sin(c) -
                i * math.cos(b) * math.sin(c))
    
    def calculate_z(i, j, k, a, b, c):
        return (k * math.cos(a) * math.cos(b) - 
                j * math.sin(a) * math.cos(b) + 
                i * math.sin(b))
    
    def calculate_for_surface(cube_x, cube_y, cube_z, ch, buffer, z_buffer, 
                              horizontal_offset, a, b, c):
        x = calculate_x(cube_x, cube_y, cube_z, a, b, c)
        y = calculate_y(cube_x, cube_y, cube_z, a, b, c)
        z = calculate_z(cube_x, cube_y, cube_z, a, b, c) + distance_from_cam
        
        if z == 0:
            return
        
        ooz = 1 / z
        
        xp = int(width / 2 + horizontal_offset + K1 * ooz * x * 2)
        yp = int(height / 2 + K1 * ooz * y)
        
        idx = xp + yp * width
        if 0 <= idx < width * height:
            if ooz > z_buffer[idx]:
                z_buffer[idx] = ooz
                buffer[idx] = ch
    
    frames = []
    
    # Generate 100 frames
    for frame_num in range(100):
        # Initialize buffers
        buffer = [background_char] * (width * height)
        z_buffer = [0.0] * (width * height)
        
        # Draw single cube
        horizontal_offset = 0
        cube_w = cube_width
        
        cube_x = -cube_w
        while cube_x < cube_w:
            cube_y = -cube_w
            while cube_y < cube_w:
                # Six faces with different characters
                calculate_for_surface(cube_x, cube_y, -cube_w, '@', buffer, z_buffer, horizontal_offset, A, B, C)
                calculate_for_surface(cube_w, cube_y, cube_x, '$', buffer, z_buffer, horizontal_offset, A, B, C)
                calculate_for_surface(-cube_w, cube_y, -cube_x, '~', buffer, z_buffer, horizontal_offset, A, B, C)
                calculate_for_surface(-cube_x, cube_y, cube_w, '#', buffer, z_buffer, horizontal_offset, A, B, C)
                calculate_for_surface(cube_x, -cube_w, -cube_y, ';', buffer, z_buffer, horizontal_offset, A, B, C)
                calculate_for_surface(cube_x, cube_w, cube_y, '+', buffer, z_buffer, horizontal_offset, A, B, C)
                cube_y += increment_speed
            cube_x += increment_speed
        
        # Convert buffer to image
        img = Image.new('RGB', (width * 6, height * 12), 'black')
        draw = ImageDraw.Draw(img)
        
        for k in range(width * height):
            char = buffer[k]
            if char != background_char:
                x_pos = (k % width) * 6
                y_pos = (k // width) * 12
                draw.text((x_pos, y_pos), char, fill='white')
        
        frames.append(img)
        
        # Update rotation angles
        A += 0.05
        B += 0.05
        C += 0.01
    
    # Save as GIF
    buf = BytesIO()
    frames[0].save(buf, format='GIF', save_all=True, append_images=frames[1:], 
                   duration=50, loop=0, optimize=True)
    buf.seek(0)
    
    return buf

def generate_julia(c_real, c_imag):
    """
    Generates the Julia set fractal for a given complex constant c.
    
    Args:
        c_real: Real part of the complex constant
        c_imag: Imaginary part of the complex constant
    
    Returns:
        BytesIO: Buffer containing the PNG image of the Julia set
    """
    # Setup the resolution and complex plane
    w, h = 800, 600
    # Zoom level: We look at the area from -1.5 to 1.5
    y, x = np.ogrid[-1.5:1.5:h*1j, -1.5:1.5:w*1j]
    
    # Create the grid of complex numbers (Z)
    z = x + y*1j
    
    # The constant complex number C
    c = c_real + c_imag*1j

    # The iteration loop
    # We track how many iterations it takes for a point to "escape" to infinity
    max_iter = 100
    div_time = max_iter + np.zeros(z.shape, dtype=int)

    for i in range(max_iter):
        # The core fractal formula: z = z^2 + c
        z = z**2 + c
        
        # Find points that have "escaped" (magnitude > 2)
        diverge = z * np.conj(z) > 2**2
        div_now = diverge & (div_time == max_iter)
        div_time[div_now] = i
        
        # Stop calculating points that have already escaped to save speed
        z[diverge] = 2

    # Visualization
    plt.figure(figsize=(10, 8))
    plt.imshow(div_time, cmap='twilight', extent=[-1.5, 1.5, -1.5, 1.5])
    plt.axis('off')

    # Save to memory buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    plt.close()
    return buf

def generate_cellular_war():
    """
    Simulates a cellular warfare using Conway's Game of Life rules with two teams.
    Returns a GIF showing 50 generations of battle between a Glider (Red) and Beacon (Cyan).
    
    Returns:
        tuple: (BytesIO buffer with GIF, winner_message, p1_score, p2_score)
    """
    # 1. SETUP THE ARENA (50x50 Grid for more interesting interactions)
    # 0 = Dead, 1 = Player 1 (Red), 2 = Player 2 (Cyan)
    grid = np.zeros((50, 50), dtype=int)

    # 2. SPAWN PLAYER 1 (The "Glider" - Mobile diagonal pattern)
    # Multiple gliders for better visualization
    glider = [[0, 1, 0], [0, 0, 1], [1, 1, 1]]
    for r in range(3):
        for c in range(3):
            if glider[r][c] == 1:
                grid[r+5][c+5] = 1  # Top left glider
                grid[r+8][c+15] = 1  # Another glider

    # 3. SPAWN PLAYER 2 (Blinker + Block - Classic patterns)
    # Blinker (oscillator)
    grid[40:43, 40] = 2  # Vertical blinker
    
    # Block (stable)
    grid[35:37, 42:44] = 2
    
    # Another blinker
    grid[38, 35:38] = 2  # Horizontal blinker

    # 4. RUN THE WAR (80 Generations for more interesting evolution)
    # We save frames to make a GIF
    frames = []
    
    # Define colors: Black (Dead), Red (P1), Cyan (P2)
    cmap = ListedColormap(['#000000', '#FF0000', '#00FFFF'])

    size = 50
    for gen in range(80):
        # Create image for this frame (only save every 2nd frame to reduce file size)
        if gen % 2 == 0:
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.imshow(grid, cmap=cmap, vmin=0, vmax=2, interpolation='nearest')
            ax.set_title(f"Generation {gen}", color='white', fontsize=10)
            ax.axis('off')
            fig.patch.set_facecolor('black')
            
            # Save frame to buffer
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', facecolor='black')
            buf.seek(0)
            frames.append(Image.open(buf))
            plt.close()

        # --- THE GAME OF LIFE LOGIC (With Teams) ---
        new_grid = np.zeros_like(grid)
        
        for x in range(size):
            for y in range(size):
                # Count neighbors in 3x3 region
                p1_neighbors = 0
                p2_neighbors = 0
                
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue  # Skip the cell itself
                        
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < size and 0 <= ny < size:
                            if grid[nx][ny] == 1:
                                p1_neighbors += 1
                            elif grid[nx][ny] == 2:
                                p2_neighbors += 1
                
                total_neighbors = p1_neighbors + p2_neighbors

                # Apply Conway's Rules
                if grid[x][y] > 0:  # If cell is alive
                    if total_neighbors == 2 or total_neighbors == 3:
                        new_grid[x][y] = grid[x][y]  # Survives
                    # else: dies (underpopulation or overpopulation)
                else:  # If cell is dead
                    if total_neighbors == 3:
                        # REPRODUCTION: Team with more neighbors claims the cell
                        if p1_neighbors > p2_neighbors:
                            new_grid[x][y] = 1
                        elif p2_neighbors > p1_neighbors:
                            new_grid[x][y] = 2
                        else:
                            # Tie: randomly choose (using position as seed)
                            new_grid[x][y] = 1 if (x + y) % 2 == 0 else 2

        grid = new_grid

    # 5. DETERMINE WINNER
    p1_score = np.sum(grid == 1)
    p2_score = np.sum(grid == 2)
    
    # Save GIF with optimizations
    gif_buf = BytesIO()
    frames[0].save(
        gif_buf, 
        format="GIF", 
        save_all=True, 
        append_images=frames[1:], 
        duration=150,  # 150ms per frame
        loop=0,
        optimize=True
    )
    gif_buf.seek(0)

    if p1_score > p2_score:
        winner = "🔴 RED TEAM"
    elif p2_score > p1_score:
        winner = "🔵 CYAN TEAM"
    else:
        winner = "⚔️ TIE"
    
    return gif_buf, winner, p1_score, p2_score
