"""
Math & Visualization Cog

Commands for mathematical visualizations and computational art:
- plot: Plot a mathematical formula (e.g., !plot x**2 + 2*x)
- fractal: Generate the Mandelbrot Set fractal
- julia: Generate a Julia Set fractal with custom or random parameters
- cube: Generate a 3D spinning cube animation
- war: Simulate cellular warfare between two Game of Life patterns

All rendering operations run in separate threads to prevent blocking
the bot's async event loop.
"""

import discord
from discord.ext import commands
import random
from functools import partial
from helper.math_fun import plot_formula, generate_mandelbrot, generate_spinning_cube, generate_julia, generate_cellular_war


class Math(commands.Cog):
    """Mathematical plotting and fractal generation"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Math cog loaded")
    
    @commands.command()
    async def plot(self, ctx, *, formula: str):
        """ Plot a mathematical formula """
        # Use the plot function from math_fun.py
        buf, error = plot_formula(formula)
        
        if error:
            await ctx.send(f"❌ **Math Error:** Could not plot that.\nUse Python syntax: `x**2` not `x^2`.\nError: `{error}`")
        else:
            await ctx.send(file=discord.File(buf, filename="plot.png"))

    @commands.command()
    async def fractal(self, ctx):
        """ Generate the Mandelbrot fractal set """
        await ctx.send("🎨 **Rendering the Mandelbrot Set...** (This is heavy math, give me a second!)")
        
        # Run this heavy calculation in a separate thread so the bot doesn't freeze
        buf = await self.bot.loop.run_in_executor(None, generate_mandelbrot)
        
        await ctx.send(file=discord.File(buf, filename="mandelbrot.png"))

    @commands.command()
    async def julia(self, ctx, c_real: float = None, c_imag: float = None):
        """ Generate the Julia set fractal """
        # Determine the constant 'c'
        # If the user didn't provide numbers, we generate random ones
        if c_real is None or c_imag is None:
            # Pick values between -1 and 1 because that's where the interesting shapes live
            c_real = random.uniform(-1.0, 1.0)
            c_imag = random.uniform(-1.0, 1.0)
            await ctx.send(f"🎲 **Random Julia Set**\nUsing c = {c_real:.3f} + {c_imag:.3f}i\n\n*💡 Tip: Try values between -2 and 2 for best results!*")
        else:
            # Validate the input values
            if abs(c_real) > 2 or abs(c_imag) > 2:
                await ctx.send("❌ **Values too large!** Try keeping both values between -2 and 2.\n\n**Optimal ranges for interesting fractals:**\n• Real: -1.5 to 1.5\n• Imaginary: -1.5 to 1.5\n\n**Popular examples:**\n`!julia -0.7 0.27` (dragon)\n`!julia 0.285 0.01` (spiral)\n`!julia -0.4 0.6` (dendrite)")
                return
            
            await ctx.send(f"🎨 **Custom Julia Set**\nUsing c = {c_real} + {c_imag}i")

        await ctx.send("Computing... (This relies on NumPy vectorization!)")

        # Execute the function using the executor to keep Discord async happy
        fn = partial(generate_julia, c_real, c_imag)
        buf = await self.bot.loop.run_in_executor(None, fn)
        
        await ctx.send(file=discord.File(buf, filename="julia.png"))

    @commands.command()
    async def cube(self, ctx):
        """ Generate a 3D spinning cube animation """
        await ctx.send("🧊 **Rendering a 3D Spinning Cube...** (This takes a few seconds!)")
        
        # Run in separate thread to avoid blocking
        buf = await self.bot.loop.run_in_executor(None, generate_spinning_cube)
        
        await ctx.send(file=discord.File(buf, filename="cube.gif"))

    @commands.command()
    async def war(self, ctx):
        """ Simulate cellular warfare between two Game of Life patterns """
        await ctx.send("⚔️ **Simulating Cellular Warfare...** (Glider vs Beacon)")
        
        # Run in separate thread to avoid blocking (this takes several seconds)
        gif_buf, winner, p1_score, p2_score = await self.bot.loop.run_in_executor(None, generate_cellular_war)
        
        await ctx.send(f"🏆 **Winner: {winner}** (Red: {p1_score} | Cyan: {p2_score})", 
                       file=discord.File(gif_buf, filename="war.gif"))


async def setup(bot):
    await bot.add_cog(Math(bot))
