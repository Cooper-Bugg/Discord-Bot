# Discord-Bot

A multi-purpose Discord bot built with discord.py featuring weather forecasts, blackjack, and more.

## Features

### Weather
- Get current US weather forecasts by city name
- Displays city, state, and detailed forecast

### Blackjack
- Multiplayer blackjack game
- Persistent rounds with dealer AI
- Commands: join, hit, stand, deal, quit

## Commands

**Utility:**
- `!ping` - Test bot responsiveness
- `!hello` - Get a greeting

**Weather:**
- `!weather <city name>` - Get US city weather forecast

**Blackjack:**
- `!blackjack` - Start a new blackjack game
- `!join` - Join an existing game
- `!hit` - Draw another card
- `!stand` - End your turn
- `!deal` - Start a new round
- `!quit` - Leave the game

**Future Commands (Not Implemented):**
- `!coinflip` - Flip a coin
- `!random` - Random number/choice generator
- `!deathroll` - Players take turns rolling with shrinking ceiling until someone rolls 1
- `!chaos` - Move users randomly in voice channels

## Setup

1. Create a virtual environment: `python3 -m venv venv`
2. Activate it: `source venv/bin/activate`
3. Install dependencies: `pip install discord.py aiohttp`
4. Set up Discord bot token in Codespace secrets as `DISCORD_TOKEN`
5. Enable Message Content and Server Members intents in Discord Developer Portal
6. Run: `python main.py`