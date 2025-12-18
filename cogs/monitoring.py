"""
Monitoring & Artifact Cog

Bot monitoring and diagnostic commands:
- metrics: Shows top commands, uptime, and error counts
- lasterror: Dumps technical details of the last crash
- health: Checks latency and system status
- shardinfo: Displays horizontal scaling info
- ratelimit: Test command to demonstrate cooldowns
- market: Fetches CS:GO item prices from Steam Market

Artifact system commands:
- artifact_status: Shows the artifact's current state and image
- touch: Interact physically with the artifact
- disturb: Force a change in the artifact (high risk)

This cog also handles:
- on_command_completion: Tracks command usage and artifact updates
- on_command_error: Captures error traces and provides user-friendly messages

State tracking:
- bot.command_counts: Counter for command usage statistics
- bot.last_error_trace: String of the most recent error traceback
- bot.start_time: Timestamp when bot started (for uptime calculation)
"""

import discord
from discord.ext import commands
import time
import traceback
from collections import Counter
import datetime
import urllib.parse
import aiohttp
import random
from helper.artifact_system import artifact


class Monitoring(commands.Cog):
    """Bot monitoring, diagnostics, and artifact system"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Initialize monitoring state on the bot object
        if not hasattr(bot, 'command_counts'):
            bot.command_counts = Counter()
        if not hasattr(bot, 'last_error_trace'):
            bot.last_error_trace = "No errors yet."
        if not hasattr(bot, 'start_time'):
            bot.start_time = time.time()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Monitoring cog loaded")
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """ Track command usage statistics and update artifact """
        command_name = ctx.command.name
        self.bot.command_counts[command_name] += 1
        
        # Silently update artifact based on command usage
        # Night time check (Midnight to 6 AM)
        currentHour = datetime.datetime.now().hour
        if 0 <= currentHour < 6:
            artifact.modifyStat("shadow", 1)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """ Capture error traces and provide user-friendly messages """
        # Format the exception into a string and store it
        self.bot.last_error_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Print to console for immediate visibility
        print(f"Error in {ctx.command}: {error}")
        
        # Handle specific error types with user-friendly messages
        if isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ Invalid argument! Please use whole numbers (integers) for time values.\nExample: `!pomodoro 25 5`")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ Missing argument! Usage: `{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ Slow down! Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use that command!")
        elif isinstance(error, commands.CheckFailure):
            # This handles @commands.is_owner() failures
            await ctx.send("🔒 This command is restricted to the bot owner.")
        else:
            # Generic fallback message
            await ctx.send(f"⚠️ Something went wrong: `{error}`")
    
    # === Monitoring Commands ===
    
    @commands.command()
    async def metrics(self, ctx):
        """ Shows top commands, uptime, and error counts """
        # Calculate the total seconds the bot has been alive
        uptime_seconds = int(time.time() - self.bot.start_time)
        
        # Specific math to break seconds into days, hours, minutes
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Sort the command counts to find the most popular ones
        top_commands = self.bot.command_counts.most_common(5)
        
        # Format the list using a list comprehension for cleaner code
        stats_text = "\n".join([f"**!{cmd}**: {count} uses" for cmd, count in top_commands])
        
        if not stats_text:
            stats_text = "No commands used yet."

        embed = discord.Embed(title="📊 Bot Metrics", color=discord.Color.teal())
        embed.add_field(name="⏳ Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="🏆 Top Commands", value=stats_text, inline=False)
        # Count errors by splitting the trace string looking for the word Traceback
        embed.add_field(name="📉 Total Errors", value=f"{len(self.bot.last_error_trace.split('Traceback')) - 1} recorded", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def lasterror(self, ctx):
        """ Dumps the technical details of the last crash """
        # Wrap the trace in a python code block for syntax highlighting
        # Truncate to 1900 characters to ensure it fits within Discord's message limit
        error_msg = f"```python\n{self.bot.last_error_trace[:1900]}\n```"
        await ctx.send(f"🐞 **Last Recorded Exception:**\n{error_msg}")
    
    @commands.command()
    async def health(self, ctx):
        """ Checks latency and system status """
        # Latency measures the round-trip time to Discord servers
        latency_ms = round(self.bot.latency * 1000)
        
        # Determine health status based on lag thresholds
        status = "🟢 Healthy"
        if latency_ms > 200:
            status = "🟡 Lagging"
        if latency_ms > 500:
            status = "🔴 Critical"

        # Shard ID is useful context if you ever scale to multiple processes
        shard_id = ctx.guild.shard_id if ctx.guild else 0
        
        await ctx.send(f"🏥 **System Status:** {status}\n📶 **Latency:** {latency_ms}ms\n💎 **Shard ID:** {shard_id}")
    
    @commands.command()
    async def shardinfo(self, ctx):
        """ Displays horizontal scaling info """
        # Retrieve the shard ID for the current guild
        shard_id = ctx.guild.shard_id
        
        # Check how many total shards exist (defaults to 1 for small bots)
        total_shards = self.bot.shard_count or 1
        
        embed = discord.Embed(title="💎 Shard Information", color=discord.Color.purple())
        embed.add_field(name="Current Shard", value=f"#{shard_id}", inline=True)
        embed.add_field(name="Total Shards", value=f"{total_shards}", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)  # One use every 30 seconds per user
    async def ratelimit(self, ctx):
        """ A test command to demonstrate cooldowns """
        await ctx.send(f"✅ Command successful! Try using it again immediately to see the error.")
    
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)  # Prevent getting IP banned by Steam
    async def market(self, ctx, *, item_name: str):
        """
        Fetches price for a CS:GO item.
        Usage: !market AK-47 | Redline (Field-Tested)
        """
        # The App ID for Counter-Strike 2 is 730
        app_id = 730 
        
        # URL Encode the item name to handle spaces and special characters safely
        encoded_name = urllib.parse.quote(item_name)
        
        # Construct the endpoint URL for the Steam Community Market
        url = f"http://steamcommunity.com/market/priceoverview/?currency=1&appid={app_id}&market_hash_name={encoded_name}"

        await ctx.send(f"🔎 Searching Steam Market for **{item_name}**...")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Check if Steam blocked the request or the item does not exist
                if response.status != 200:
                    await ctx.send("❌ Steam blocked the request or item not found.")
                    return
                
                data = await response.json()
                
                # Verify the response contains the price data we need
                if not data or 'lowest_price' not in data:
                    await ctx.send("❌ Item not found! Make sure the name is EXACT (including condition).")
                    return

                # Extract price data with default fallbacks
                price = data.get('lowest_price', 'N/A')
                volume = data.get('volume', '0')
                median = data.get('median_price', 'N/A')

                embed = discord.Embed(title=f"💸 Market: {item_name}", color=discord.Color.dark_green())
                embed.add_field(name="Lowest Price", value=price, inline=True)
                embed.add_field(name="Median Price", value=median, inline=True)
                embed.add_field(name="24h Volume", value=f"{volume} sold", inline=False)
                embed.set_footer(text="Data from Steam Community Market")
                
                await ctx.send(embed=embed)
                
                # Silently update artifact (market checking = greed)
                artifact.modifyStat("greed", 1)
    
    # === Artifact Commands ===
    
    @commands.command()
    async def artifact_status(self, ctx):
        """ Shows the current state and visualizes the artifact """
        state = artifact.state
        
        # Generate the procedural image
        image_buffer = artifact.generateImage()
        file = discord.File(image_buffer, filename="artifact.png")

        embed = discord.Embed(title=f"🔮 {state['name']}", color=discord.Color.purple())
        embed.add_field(name="Mood", value=state['mood'], inline=True)
        embed.add_field(name="Age", value=f"{state['ageDays']} days", inline=True)
        embed.add_field(name="Traits", value=", ".join(state['traits']), inline=False)
        embed.set_image(url="attachment://artifact.png")
        embed.set_footer(text="It seems to be waiting for something...")

        await ctx.send(embed=embed, file=file)
    
    @commands.command()
    async def touch(self, ctx):
        """ Interact physically with the artifact """
        # Get a random response based on current mood
        response = artifact.getRandomTouchResponse()
        
        # Random chance to increase a stat (The butterfly effect)
        if random.random() < 0.3:
            artifact.modifyStat("chaos", 1)
            
        await ctx.send(f"👉 {response}")
    
    @commands.command()
    async def disturb(self, ctx):
        """ Force a change. High risk """
        # 50% chance to reset stats, 50% chance to spike Chaos
        outcome = random.choice(["calm", "anger"])
        
        if outcome == "calm":
            artifact.state["hiddenStats"] = {"chaos": 0, "greed": 0, "shadow": 0}
            artifact.saveState()
            response = artifact.getRandomDisturbOutcome("calm")
            await ctx.send(response)
        else:
            artifact.modifyStat("chaos", 20)
            response = artifact.getRandomDisturbOutcome("anger")
            await ctx.send(response)


async def setup(bot):
    await bot.add_cog(Monitoring(bot))
