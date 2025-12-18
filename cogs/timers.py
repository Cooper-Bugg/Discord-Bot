"""
Timers Cog

Commands for time management and reminders:
- remindme: Set a reminder with a specific time delay
- pomodoro: Start a Pomodoro work/break timer session
- stop: Cancel your active Pomodoro timer

State tracking:
- bot.active_pomodoros: Tracks active Pomodoro sessions by user_id

Time format: Use 's' (seconds), 'm' (minutes), 'h' (hours), 'd' (days)
Examples: 10s, 5m, 2h, 1d
"""

import discord
from discord.ext import commands
import asyncio


def convert_time_to_seconds(time_str):
    """
    Converts a string like '10m', '1h', '30s' into seconds.
    Returns: (seconds, unit_name) or (None, None) if invalid.
    """
    # Get the unit (last character) and value (everything else)
    unit = time_str[-1].lower()
    value = time_str[:-1]

    # Validate that the value is actually a number
    if not value.isdigit():
        return None, None

    seconds = int(value)

    if unit == 's':
        return seconds, "seconds"
    elif unit == 'm':
        return seconds * 60, "minutes"
    elif unit == 'h':
        return seconds * 3600, "hours"
    elif unit == 'd':
        return seconds * 86400, "days"
    else:
        return None, None


class Timers(commands.Cog):
    """Time management tools: reminders and Pomodoro timers"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Initialize state dictionary on the bot object
        if not hasattr(bot, 'active_pomodoros'):
            bot.active_pomodoros = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Timers cog loaded")
    
    @commands.command(aliases=['remind', 'timer'])
    async def remindme(self, ctx, time_str: str, *, task: str = "Something important!"):
        """ Set a reminder with a specific time delay """
        # Convert the time string to seconds
        seconds, unit_name = convert_time_to_seconds(time_str)

        if seconds is None:
            await ctx.send("⚠️ Invalid format! Use `s` (seconds), `m` (minutes), or `h` (hours).\nExample: `!remindme 10m Check the pizza`")
            return

        # Confirm the timer
        await ctx.reply(f"⌚ I set a timer for **{time_str}** ({seconds} seconds). I'll remind you about: **{task}**")

        # Wait (non-blocking)
        await asyncio.sleep(seconds)

        # Send the reminder
        await ctx.send(f"🔔 {ctx.author.mention}, time's up! Don't forget: **{task}**")
    
    @commands.command(aliases=['pomo', 'work'])
    async def pomodoro(self, ctx, work_min: int = 25, break_min: int = 5):
        """ Start a Pomodoro work/break timer session """
        # Validate input
        if work_min < 1 or break_min < 1:
            await ctx.send("⚠️ Work and break times must be at least 1 minute!")
            return
        
        if work_min > 480 or break_min > 480:
            await ctx.send("⚠️ Times must be less than 480 minutes (8 hours)!")
            return
        
        # Check if they already have a timer running
        if ctx.author.id in self.bot.active_pomodoros:
            await ctx.send("You already have a timer running! Type `!stop` to end it first.")
            return

        await ctx.send(f"⌚ **Pomodoro Started!**\nFocus for **{work_min} minutes**. I'll ping you for a break.")

        # Define the pomodoro session loop
        async def run_pomo_session():
            try:
                # Work interval
                await asyncio.sleep(work_min * 60) 
                await ctx.send(f"🔔 {ctx.author.mention}, **Work time is up!** Take a **{break_min} minute** break.")
                
                # Break interval
                await asyncio.sleep(break_min * 60)
                await ctx.send(f"🔔 {ctx.author.mention}, **Break is over!** Type `!pomo` again to start another round.")
                
                # Clean up when done
                if ctx.author.id in self.bot.active_pomodoros:
                    del self.bot.active_pomodoros[ctx.author.id]

            except asyncio.CancelledError:
                # Triggered when user types !stop
                await ctx.send(f"🛑 **Timer stopped.** Good work, {ctx.author.name}!")

        # Create and save the background task
        task = self.bot.loop.create_task(run_pomo_session())
        self.bot.active_pomodoros[ctx.author.id] = task
    
    @commands.command()
    async def stop(self, ctx):
        """ Cancel your active Pomodoro timer """
        # Check if they have an active timer
        if ctx.author.id not in self.bot.active_pomodoros:
            await ctx.send("You don't have any active timers!")
            return

        # Get the task and cancel it
        task = self.bot.active_pomodoros[ctx.author.id]
        task.cancel()
        
        # Remove from dictionary
        del self.bot.active_pomodoros[ctx.author.id]


async def setup(bot):
    await bot.add_cog(Timers(bot))
