import os
import asyncio
import discord
from discord.ext import commands

"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                           BUGG BOT - MAIN MODULE                          ║
║                       Discord Bot with Cog Architecture                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

Core bot initialization and cog loading system.
All commands are organized into modular cogs for maintainability.

Cog Structure:
  • games.py       - Quick games (coinflip, slots, rps, etc.)
  • board_games.py - Multi-turn games (blackjack, tictactoe, connect4)
  • word_games.py  - Word games (hangman, wordle, akinator, typerace)
  • pokemon.py     - Pokemon battle system
  • apis.py        - External APIs (weather, space, trivia)
  • math.py        - Mathematical visualizations
  • utility.py     - Server utilities and info commands
  • timers.py      - Reminders and pomodoro
  • monitoring.py  - Bot metrics and artifact system
  • admin.py       - Hot reloading and cog management

Helper Modules (in helper/ folder):
  • games.py, poke_api.py, nasa_api.py, weather_api.py,
    trivia_api.py, math_fun.py, artifact_system.py

Features:
    Hot reloading - Update cogs without restarting bot
    Modular design - Each cog is independently testable
    State management - Bot attributes for persistent state
    Event distribution - Handlers in appropriate cogs

Bot uses command prefix: !
"""

# Read token from the enviroment
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise RuntimeError("DISCORD_TOKEN enviroment varible is not set")

# Set up intents so the bot can see message content
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable members intent to see guild members/nicknames

# Create bot object
bot = commands.Bot(command_prefix = "!", intents = intents)

# === Load Cogs ===
async def load_extensions():
    """Load all cog modules from the cogs folder"""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded cog: {filename[:-3]}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")

# === Bot Event Handlers ===
# Event handlers moved to respective cogs:
# - on_ready: stays here for core bot initialization
# - on_command_completion, on_command_error: moved to cogs/monitoring.py
# - on_message: moved to cogs/word_games.py

# === All Commands Moved to Cogs ===
# - games.py: coinflip, roll, 8ball, random, slots, roulette, duel, mock, rps, choose, guessthenumber, g, quitguess
# - admin.py: load, unload, reload, reloadall, cogs
# - board_games.py: blackjack, join, hit, stand, deal, quit, deathroll, drjoin, drroll, drquit, tictactoe, move, connect4, drop
# - word_games.py: hangman, quithangman, wordle, guess, quitwordle, akinator, quitakinator, typerace, quittyperace
# - pokemon.py: battle, attack, challenge, accept, flee
# - apis.py: weather, space, trivia
# - math.py: plot, fractal, julia, cube, war
# - utility.py: ping, commands, purge, translate, serverinfo, userinfo, avatar, fakeping, chaos, mock
# - timers.py: remindme, pomodoro, stop
# - monitoring.py: metrics, lasterror, health, shardinfo, ratelimit, market, artifact_status, touch, disturb

# === Main Entry Point ===
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
