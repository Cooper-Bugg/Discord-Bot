import os
import discord
from discord.ext import commands

# Read token from the enviroment
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise RuntimeError("DISCORD_TOKEN enviroment varible is not set")

# Set up intents so the bot can see message content
intents = discord.Intents.default()
intents.message_content = True

# Create bot object
bot = commands.Bot(command_prefix = "!", intents = intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")

# === Test Commands ===
@bot.command()
async def ping(ctx):
    # Simple test command that responds with "Pong!"
    await ctx.send("Pong!")

# === [] Commands ===
@bot.command()
async def hello(ctx):
    # Greets the user
    await ctx.send(f"Hello, {ctx.author.mention}!")

if __name__ == "__main__":
    bot.run(TOKEN)
