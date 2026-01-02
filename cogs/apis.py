"""
APIs Cog

Commands that integrate with external APIs:
- weather: Get weather forecast for a US city (National Weather Service API)
- space: Get NASA's Astronomy Picture of the Day (APOD API)
- trivia: Play a trivia question game (Open Trivia Database API)

All commands use async API calls with proper error handling.
"""

import discord
from discord.ext import commands
import asyncio
from helper.weather_api import get_weather_data
from helper.nasa_api import get_apod
from helper.trivia_api import get_trivia_question


class APIs(commands.Cog):
    """External API integrations for weather, space, and trivia"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("APIs cog loaded")
    
    @commands.command(name='weather')
    async def weather_command(self, ctx, *, city_name: str):
        """ Get the current weather forecast for a specified US city """
        # The '*' ensures the entire city is captured (e.g. "San Francisco")   
        # Get data from helper function
        forecast_message = await get_weather_data(city_name)

        # Send result back
        await ctx.send(forecast_message)

    @commands.command(name='space')
    async def space(self, ctx, date: str = None):
        """ 
        Get NASA's Astronomy Picture of the Day
        Optional: Provide a date in YYYY-MM-DD format (e.g., !space 2023-12-25)
        """
        image_url, text = await get_apod(date)
        
        if image_url:
            await ctx.send(text)
            await ctx.send(image_url) # Discord automatically shows the image!
        else:
            await ctx.send("Houston, we have a problem. Couldn't get the image.")

    @commands.command()
    async def trivia(self, ctx):
        """ Play a trivia question game """
        # Fetch a trivia question from the API
        trivia_data = await get_trivia_question()
        
        if not trivia_data:
            await ctx.send("Trivia API is down! Try again later.")
            return
        
        # Create the answer options display
        answer_str = ""
        for i, ans in enumerate(trivia_data['all_answers']):
            answer_str += f"**{i+1}.** {ans}\n"
        
        # Send the Embed with the question
        embed = discord.Embed(title="🧠 Trivia Time!", description=trivia_data['question'], color=discord.Color.gold())
        embed.add_field(name="Category", value=trivia_data['category'], inline=True)
        embed.add_field(name="Difficulty", value=trivia_data['difficulty'], inline=True)
        embed.add_field(name="Options", value=answer_str, inline=False)
        embed.set_footer(text="Type the number (1-4) of the correct answer! You have 15 seconds.")
        await ctx.send(embed=embed)
        
        # Helper function to check if the user replied correctly
        def check(m):
            # We only accept messages from the user who started the game in the same channel
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            # Wait for a message that matches the check
            msg = await self.bot.wait_for('message', check=check, timeout=15.0)
            
            # Check if their input (e.g., "1") matches the correct index
            # We subtract 1 because computer lists start at 0, but humans start at 1
            try:
                user_choice_index = int(msg.content) - 1
                
                # Check if the index is valid (0-3)
                if user_choice_index < 0 or user_choice_index >= len(trivia_data['all_answers']):
                    await ctx.send(f"❌ That wasn't a valid option! The answer was **{trivia_data['correct_answer']}**.")
                    return
                
                user_answer = trivia_data['all_answers'][user_choice_index]
                
                if user_answer == trivia_data['correct_answer']:
                    await ctx.send(f"✅ Correct, {ctx.author.display_name}! The answer was **{trivia_data['correct_answer']}**. 🎉")
                else:
                    await ctx.send(f"❌ Wrong! The correct answer was **{trivia_data['correct_answer']}**. Better luck next time!")
                    
            except ValueError:
                await ctx.send(f"❌ That wasn't a valid number! The answer was **{trivia_data['correct_answer']}**.")

        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! The correct answer was **{trivia_data['correct_answer']}**. 🐢")


async def setup(bot):
    await bot.add_cog(APIs(bot))
