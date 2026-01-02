"""
Quick Games Cog

Commands for quick and casual entertainment:
- coinflip: Flip a coin (heads or tails)
- roll: Roll dice (supports NdN format)
- 8ball: Ask the magic 8-ball a question
- random: Generate a random number or pick from choices
- slots: Spin the slot machine
- roulette: Play roulette (red/black/green)
- duel: Challenge another user to a quick showdown
- rps: Play Rock-Paper-Scissors
- choose: Choose your RPS move via DM
- guessthenumber: Start a number guessing game
- g: Make a guess in the active game
- quitguess: Quit the number guessing game

State tracking:
- bot.active_rps: Tracks active Rock-Paper-Scissors games
- bot.active_guessnumber: Tracks active number guessing games
"""

import discord
from discord.ext import commands
import random
import asyncio

# Import game logic from the games module (helper file)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helper.games import flip_coin, roll_dice, random_number, random_choice, spin_slots, spin_roulette, play_duel, RPSGame, GuessTheNumberGame


class Games(commands.Cog):
    """Quick games and entertainment commands"""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize state dictionaries on the bot object
        if not hasattr(bot, 'active_rps'):
            bot.active_rps = {}
        if not hasattr(bot, 'active_guessnumber'):
            bot.active_guessnumber = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Games cog loaded")
    
    # === Quick Games ===
    
    @commands.command(name='coinflip')
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = flip_coin()
        emoji = "⚪" if result == "Heads" else "🔵"
        await ctx.send(f"{emoji} **{result}!**")
    
    @commands.command(name='roll')
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in XdY format (e.g., 3d6, 1d20)"""
        try:
            # Parse the dice string
            if 'd' not in dice.lower():
                sides = int(dice)
                amount = 1
            else:
                parts = dice.lower().split('d')
                amount = int(parts[0]) if parts[0] else 1
                sides = int(parts[1])
            
            # Roll the dice
            rolls, total = roll_dice(sides, amount)
            
            if rolls is None:
                await ctx.send("Invalid dice roll! Use format like `!roll 3d6` (max 100 dice)")
                return
            
            # Format output
            if amount == 1:
                await ctx.send(f"🎲 **{ctx.author.display_name}** rolled **{total}** (1d{sides})")
            else:
                rolls_str = ", ".join(str(r) for r in rolls)
                await ctx.send(f"🎲 **{ctx.author.display_name}** rolled {amount}d{sides}: [{rolls_str}] = **{total}**")
        except:
            await ctx.send("Invalid format! Use `!roll 3d6` or `!roll 20`")
    
    @commands.command(name='8ball')
    async def eightball(self, ctx, *, question: str = None):
        """Ask the magic 8-ball a question"""
        if not question:
            await ctx.send("You need to ask a question! Example: `!8ball Will I win?`")
            return
        
        responses = [
            # Positive
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            # Non-committal
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            # Negative
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        
        answer = random.choice(responses)
        await ctx.send(f"🎱 **Question:** {question}\n🎱 **Answer:** {answer}")
    
    @commands.command(name='random')
    async def random_cmd(self, ctx, *args):
        """Random number or choice from arguments"""
        if not args:
            result = random_number(1, 100)
            await ctx.send(f"🎲 Random number: **{result}**")
        elif len(args) == 1:
            try:
                max_num = int(args[0])
                result = random_number(1, max_num)
                await ctx.send(f"🎲 Random number (1-{max_num}): **{result}**")
            except:
                await ctx.send(f"🎲 Random choice: **{args[0]}**")
        elif len(args) == 2:
            try:
                min_num = int(args[0])
                max_num = int(args[1])
                result = random_number(min_num, max_num)
                await ctx.send(f"🎲 Random number ({min_num}-{max_num}): **{result}**")
            except:
                result = random_choice(list(args))
                await ctx.send(f"🎲 Random choice: **{result}**")
        else:
            result = random_choice(list(args))
            await ctx.send(f"🎲 Random choice: **{result}**")
    
    @commands.command()
    async def slots(self, ctx):
        """Spin the slot machine - 3 rows, middle counts!"""
        result = spin_slots()
        # Format the slot machine display
        output = f"🎰 **SLOT MACHINE** 🎰\n"
        output += f"   {''.join(result['top'])}\n"
        output += f"**[** {''.join(result['middle'])} **]**\n"
        output += f"   {''.join(result['bottom'])}\n\n"
        
        # Determine outcome
        if result['triple_jackpot']:
            output += "🌟💰 **TRIPLE JACKPOT!!!** 💰🌟"
        elif result['middle_jackpot']:
            output += "💰 **JACKPOT!** 💰"
        elif result['partial_win']:
            output += "✨ **Partial Win!** ✨"
        else:
            output += "😔 No win this time..."
        
        await ctx.send(output)
        
        # Artifact hook: +1 chaos for gambling
        if hasattr(self.bot, 'artifact'):
            self.bot.artifact.modifyStat('chaos', 1)
    
    @commands.command()
    async def roulette(self, ctx):
        """Russian roulette in voice channel"""
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to play roulette!")
            return
        
        result = spin_roulette()
        
        if "💀 BANG!" in result:
            try:
                await ctx.author.move_to(None)
                await ctx.send(f"{result} {ctx.author.mention} has been kicked from voice!")
                
                # Artifact hook: +3 chaos for losing roulette
                if hasattr(self.bot, 'artifact'):
                    self.bot.artifact.modifyStat('chaos', 3)
            except:
                await ctx.send(f"{result} (Couldn't kick - check permissions)")
        else:
            await ctx.send(result)
            # Artifact hook: +1 chaos for surviving
            if hasattr(self.bot, 'artifact'):
                self.bot.artifact.modifyStat('chaos', 1)
    
    @commands.command()
    async def duel(self, ctx, opponent: discord.Member):
        """Quick draw duel - first to type 'bang' wins"""
        if opponent.bot:
            await ctx.send("You can't duel a bot!")
            return
        
        if opponent.id == ctx.author.id:
            await ctx.send("You can't duel yourself!")
            return
        
        result = await play_duel(ctx, ctx.author, opponent, self.bot)
        # play_duel handles sending messages internally
    
    # === Rock Paper Scissors ===
    
    @commands.command(name='rps')
    async def rps(self, ctx, opponent: discord.Member):
        """Challenge someone to Rock, Paper, Scissors"""
        if opponent.bot:
            await ctx.send("You can't challenge a bot!")
            return
        
        if opponent.id == ctx.author.id:
            await ctx.send("You can't challenge yourself!")
            return
        
        if ctx.channel.id in self.bot.active_rps:
            await ctx.send("An RPS game is already active in this channel!")
            return
        
        game = RPSGame(ctx.author.id, opponent.id)
        self.bot.active_rps[ctx.channel.id] = game
        
        await ctx.send(f"🪨📄✂️ **{ctx.author.display_name}** challenged **{opponent.display_name}** to Rock, Paper, Scissors!\n"
                       f"Both players, DM me your choice: `!choose rock`, `!choose paper`, or `!choose scissors`")
    
    @commands.command(name='choose')
    async def choose(self, ctx, choice: str = None):
        """Make your RPS choice (use in DMs)"""
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Use this command in DMs to keep your choice secret!")
            return
        
        if not choice:
            await ctx.send("Choose: `!choose rock`, `!choose paper`, or `!choose scissors`")
            return
        
        # Find which game this user is in
        user_game = None
        game_channel = None
        for channel_id, game in self.bot.active_rps.items():
            if ctx.author.id in [game.challenger_id, game.opponent_id]:
                user_game = game
                game_channel = self.bot.get_channel(channel_id)
                break
        
        if not user_game:
            await ctx.send("You're not in an active RPS game!")
            return
        
        if not user_game.make_choice(ctx.author.id, choice):
            await ctx.send("Invalid choice! Choose: `rock`, `paper`, or `scissors`")
            return
        
        await ctx.send(f"✅ Choice recorded: **{choice}**")
        
        # Check if both players have chosen
        if user_game.status == "ready":
            winner_id = user_game.determine_winner()
            
            challenger = await self.bot.fetch_user(user_game.challenger_id)
            opponent = await self.bot.fetch_user(user_game.opponent_id)
            
            c1 = user_game.choices[user_game.challenger_id]
            c2 = user_game.choices[user_game.opponent_id]
            
            result_msg = f"🪨📄✂️ **Rock, Paper, Scissors Results!**\n"
            result_msg += f"**{challenger.display_name}** chose **{c1}**\n"
            result_msg += f"**{opponent.display_name}** chose **{c2}**\n\n"
            
            if winner_id == "tie":
                result_msg += "🤝 **It's a tie!**"
            else:
                winner = await self.bot.fetch_user(winner_id)
                result_msg += f"🏆 **{winner.display_name} wins!**"
            
            if game_channel:
                await game_channel.send(result_msg)
            del self.bot.active_rps[game_channel.id]
    
    # === Guess the Number ===
    
    @commands.command(name='guessthenumber')
    async def guessthenumber(self, ctx):
        """Start a number guessing game (1-100)"""
        if ctx.author.id in self.bot.active_guessnumber:
            await ctx.send("You already have an active game! Use `!g <number>` to guess or `!quitguess` to end it.")
            return
        
        game = GuessTheNumberGame()
        self.bot.active_guessnumber[ctx.author.id] = game
        
        await ctx.send(f"🎯 **Guess the Number!**\n"
                       f"I'm thinking of a number between **1** and **100**.\n"
                       f"Use `!g <number>` to make a guess!\n"
                       f"Example: `!g 50`")
    
    @commands.command(name='g')
    async def g(self, ctx, guess: int = None):
        """Make a guess in your number guessing game"""
        if ctx.author.id not in self.bot.active_guessnumber:
            await ctx.send("You don't have an active game! Start one with `!guessthenumber`")
            return
        
        if guess is None:
            await ctx.send("You need to provide a number! Example: `!g 50`")
            return
        
        if guess < 1 or guess > 100:
            await ctx.send("❌ Guess must be between 1 and 100!")
            return
        
        game = self.bot.active_guessnumber[ctx.author.id]
        result = game.make_guess(guess)
        
        if result == "correct":
            await ctx.send(f"🎉 **Correct!** The number was **{game.number}**!\n"
                          f"It took you **{game.attempts}** attempt(s).")
            del self.bot.active_guessnumber[ctx.author.id]
        elif result == "higher":
            await ctx.send(f"📈 **Higher!** ({game.attempts} attempt(s))")
        else:  # lower
            await ctx.send(f"📉 **Lower!** ({game.attempts} attempt(s))")
    
    @commands.command(name='quitguess')
    async def quitguess(self, ctx):
        """Quit your number guessing game"""
        if ctx.author.id not in self.bot.active_guessnumber:
            await ctx.send("You don't have an active game!")
            return
        
        game = self.bot.active_guessnumber[ctx.author.id]
        await ctx.send(f"Game ended. The number was **{game.number}**. You made {game.attempts} attempt(s).")
        del self.bot.active_guessnumber[ctx.author.id]


async def setup(bot):
    await bot.add_cog(Games(bot))
