# Bugg Bot - Discord Bot

A comprehensive multi-purpose Discord bot built with discord.py featuring weather forecasts, games, mathematical visualizations, Pokémon battles, and a living artifact system.

## Features

### Weather & Space
- US weather forecasts via National Weather Service API
- NASA Astronomy Picture of the Day with historical access

### Games & Entertainment
**Multiplayer Games:**
- Blackjack with dealer AI and persistent rounds
- Death Roll (shrinking ceiling dice game)
- Pokémon Battles with type effectiveness (17 types)
- Tic-Tac-Toe (3x3 grid)
- Connect Four (6×7 grid with gravity)

**Two-Player Games:**
- Duels (quick draw reaction game)

**Single-Player Games:**
- Hangman (5 categories with ASCII art)
- Wordle (5-letter word game with color feedback)
- Trivia from Open Trivia Database
- Akinator (20 questions guessing game)
- Type Race (typing speed challenge with WPM/accuracy)

**Quick Games:**
- Coin flip, dice rolls, slots machine
- Magic 8-ball (fortune telling)
- Rock, Paper, Scissors (two players)
- Guess the Number (1-100 with hints)
- Russian roulette (voice channel kick game)
- Mock text transformer

### Math & Visualization
- Mathematical formula plotting
- Mandelbrot fractal set generation
- Julia set fractals (custom complex constants)
- 3D spinning cube animation
- Cellular warfare simulation (Conway's Game of Life)

### Artifact System
A living, evolving entity that changes based on bot usage:
- **Chaos stat** - Increased by gambling (slots, roulette)
- **Greed stat** - Increased by market checks
- **Shadow stat** - Increased by nighttime usage (12am-6am)
- Procedurally generated visuals that evolve with mood changes
- Interactive commands: touch, disturb, status

### Monitoring & Metrics
- Bot uptime and command usage statistics
- Health checks with latency monitoring
- Error tracking and debugging tools
- Shard information
- Steam Community Market price checker
- Rate limiting demonstrations

### Timers & Productivity
- Flexible reminders (seconds, minutes, hours, days)
- Pomodoro work/break timer

### Info & Utility
- Server information (members, channels, roles, boosts)
- User profiles (join dates, roles, avatars)
- Avatar display in full resolution
- Fake ping pranks
- Message purging (admin only)
- Language translation for learning

### Voice Commands
- Chaos mode (randomly shuffle voice channel members)

## Commands

### Utility
- `!ping` - Test bot responsiveness
- `!commands` - Show all available commands
- `!purge [amount]` - Delete messages (admin only)
- `!translate <lang> <text>` - Translate text (e.g., `!translate es Hello`)
- `!serverinfo` - Display server statistics
- `!userinfo [@user]` - Show user profile information
- `!avatar [@user]` - Display user's full-size avatar
- `!fakeping @user` - Mention and instantly delete

### Monitoring
- `!metrics` - Bot uptime, top commands, error counts
- `!lasterror` - Show last error stack trace
- `!health` - Check bot latency and status
- `!shardinfo` - Display shard information
- `!ratelimit` - Test command cooldown system
- `!market <item>` - CS:GO item prices from Steam

### Weather & Space
- `!weather <city>` - US city weather forecast
- `!space [YYYY-MM-DD]` - NASA's Astronomy Picture of the Day

### Math & Visualization
- `!plot <formula>` - Plot mathematical formulas
- `!fractal` - Generate Mandelbrot set
- `!julia [c_real c_imag]` - Generate Julia set
- `!cube` - 3D spinning cube animation
- `!war` - Cellular warfare simulation (Glider vs Beacon)

### Timers
- `!remindme <time> [task]` - Set a reminder (e.g., `!remindme 10m Pizza`)
- `!pomodoro [work] [break]` - Start pomodoro timer (default 25/5 min)
- `!stop` - Cancel active timer

### Games
**Quick Games:**
- `!coinflip` - Flip a coin
- `!roll [XdY]` - Roll dice (e.g., `3d6`, `20`, default `1d6`)
- `!random [args]` - Random number or choice
- `!trivia` - Answer trivia questions
- `!8ball <question>` - Ask the magic 8-ball
- `!mock <text>` - Transform text to mocking case
- `!roulette` - Russian roulette in voice
- `!duel @user` - Quick draw duel
- `!slots` - Spin the slot machine
- `!rps @user` - Rock Paper Scissors challenge
- `!guessthenumber` - Number guessing game (1-100)
- `!g <number>` - Make a guess / `!quitguess` - End game

**Single-Player:**
- `!hangman [category]` - Word guessing (animals, food, countries, movies, random)
- `!wordle` - 5-letter word guessing game
- `!guess <word>` - Make a Wordle guess
- `!quitwordle` - End Wordle game
- `!akinator` - 20 questions guessing game
- `!typerace` - Typing speed challenge

**Multiplayer:**
- `!tictactoe @opponent` - Start Tic-Tac-Toe
- `!move <1-9>` - Place your mark
- `!connect4 @opponent` - Start Connect Four
- `!drop <1-7>` - Drop a piece

### Blackjack
- `!blackjack` - Start a new game
- `!join` - Join existing game
- `!hit` - Draw another card
- `!stand` - End your turn
- `!deal` - Start new round
- `!quit` - Leave the game

### Death Roll
- `!deathroll [ceiling]` - Start game (default 100)
- `!drjoin` - Join the game
- `!drroll` - Take your turn
- `!drquit` - Cancel/quit

### Pokémon Battle
- `!battle [difficulty]` - Battle wild Pokémon (easy/medium/hard)
- `!challenge @user` - Challenge player to PvP
- `!accept` - Accept PvP challenge
- `!attack <move #>` - Use a move (1-4)
- `!flee` - Run from battle

### Artifact System
- `!artifact_status` - View artifact state and image
- `!touch` - Physically interact with artifact
- `!disturb` - Force a change (high risk)

### Voice
- `!chaos` - Shuffle voice channel members

## Setup

### Prerequisites
- Python 3.10+
- Discord bot token
- NASA API key (optional, for space command)

### Installation

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install discord.py aiohttp matplotlib numpy pillow
   ```

3. **Configure environment variables:**
   - Set `DISCORD_TOKEN` in Codespace secrets or `.env` file
   - Set `NASA_API_KEY` for space command (get free key at https://api.nasa.gov/)

4. **Discord Developer Portal setup:**
   - Enable **Message Content Intent**
   - Enable **Server Members Intent**
   - Grant bot **Move Members** permission for chaos command
   - Grant bot **Manage Messages** permission for purge command

5. **Run the bot:**
   ```bash
   python main.py
   ```

## Project Structure

```
Discord-Bot/
├── main.py                      # Bot core - initialization & cog loading
├── cogs/                        # Command modules (hot-reloadable)
│   ├── games.py                 # Quick games (coinflip, slots, rps, etc.)
│   ├── board_games.py           # Board games (blackjack, tictactoe, connect4)
│   ├── word_games.py            # Word games (hangman, wordle, akinator)
│   ├── pokemon.py               # Pokemon battle system
│   ├── apis.py                  # External APIs (weather, space, trivia)
│   ├── math.py                  # Mathematical visualizations
│   ├── utility.py               # Server utilities and info commands
│   ├── timers.py                # Reminders and pomodoro timer
│   ├── monitoring.py            # Bot metrics and artifact system
│   └── admin.py                 # Hot reloading and cog management
├── helper/                      # Implementation modules
│   ├── games.py                 # Game logic classes
│   ├── weather_api.py           # Weather API integration
│   ├── nasa_api.py              # NASA API integration
│   ├── poke_api.py              # Pokémon API integration
│   ├── trivia_api.py            # Trivia API integration
│   ├── math_fun.py              # Mathematical visualizations
│   └── artifact_system.py       # Living artifact system
├── artifact.json                # Artifact state persistence
└── README.md                    # This file
```

## Cog Architecture

The bot uses a **modular cog system** for organization and hot-reloading:

### Benefits
- **Hot Reloading**: Update code without restarting - `!reload <cog>` or `!reloadall`
- **Modularity**: Each cog is independently testable and maintainable
- **Organization**: Commands grouped by functionality (68 total commands across 10 cogs)
- **State Management**: Bot attributes (`bot.active_battles`, etc.) for persistent state

### Admin Commands (Owner Only)
- `!load <cog>` - Load a cog module
- `!unload <cog>` - Unload a cog module
- `!reload <cog>` - Reload a specific cog
- `!reloadall` - Reload all cogs at once
- `!cogs` - List all loaded cogs

### Development Workflow
1. Edit a cog file (e.g., `cogs/games.py`)
2. Use `!reload games` in Discord
3. Test changes immediately
4. No bot restart required!

## How Systems Work

### Artifact Evolution
The artifact silently tracks bot usage and evolves:
- **Chaos:** Gambling commands (slots, roulette) → "Unstable" mood
- **Greed:** Market checks → "Voracious" mood  
- **Shadow:** Commands used 12am-6am → "Eerie" mood

When any stat exceeds 50, the artifact's mood, traits, and visual appearance change dramatically.

### Game Logic
All game logic is separated into `helper/games.py` for maintainability:
- Pure Python classes with no Discord dependencies
- Return status strings for command handlers
- State management through bot attributes
- Cogs handle Discord interaction, helpers handle implementation

### API Integrations
- **Weather:** Nominatim (geocoding) + National Weather Service
- **Space:** NASA APOD API
- **Pokémon:** PokéAPI with 17-type effectiveness system
- **Trivia:** Open Trivia Database
- **Market:** Steam Community Market API

## Contributing

This is a personal learning project, but suggestions are welcome!

## License

MIT License - Feel free to use and modify for your own Discord server.