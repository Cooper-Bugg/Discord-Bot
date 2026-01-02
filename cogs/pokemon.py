"""
Pokemon Battle Cog

Commands for Pokemon battles (PvE and PvP):
- battle: Start a PvE battle against the computer (easy/normal/hard)
- attack: Use a move in battle
- challenge: Challenge another user to PvP
- accept: Accept a PvP challenge
- flee: Forfeit the current battle

State tracking:
- bot.active_battles: Tracks active Pokemon battles by user_id
- bot.pending_challenges: Tracks pending PvP challenges by user_id
"""

import random
import discord
from discord.ext import commands
from helper.poke_api import get_pokemon_data, scale_stats
from helper.games import PokemonBattle


def create_hp_bar(current_hp, max_hp, length=10):
    """
    Creates a visual HP bar.
    Example: [████░░░░░░] 40/100
    """
    if max_hp <= 0:
        return "[░░░░░░░░░░] 0/0"
    
    # Calculate the percentage of HP remaining
    percentage = current_hp / max_hp
    
    # Calculate how many filled blocks we need
    filled_blocks = int(percentage * length)
    
    # Calculate empty blocks
    empty_blocks = length - filled_blocks
    
    # Build the bar with filled (█) and empty (░) blocks
    bar = "█" * filled_blocks + "░" * empty_blocks
    
    return f"[{bar}] {current_hp}/{max_hp}"


class Pokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Initialize state dictionaries on the bot object
        if not hasattr(bot, 'active_battles'):
            bot.active_battles = {}
        if not hasattr(bot, 'pending_challenges'):
            bot.pending_challenges = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Pokemon cog loaded")
    
    @commands.command()
    async def battle(self, ctx, difficulty: str = "normal"):
        """ 
        Starts a PvE Battle against the computer. 
        Usage: !battle [easy/normal/hard] 
        """
        
        # Determine level scaling based on difficulty input
        user_lvl = 50
        if difficulty == "easy":
            cpu_lvl = 40 # CPU is underleveled
        elif difficulty == "hard":
            cpu_lvl = 60 # CPU is overleveled
        else:
            cpu_lvl = 50 # Even match

        await ctx.send(f"🔍 Searching for a wild Pokémon ({difficulty})...")

        # Setup the User's Team with error handling and retry logic
        starters = ["charmander", "squirtle", "bulbasaur", "pikachu"]
        user_base = None
        retries = 0
        while not user_base and retries < 3:
            try:
                user_base = await get_pokemon_data(random.choice(starters))
                retries += 1
            except:
                retries += 1
        
        if not user_base:
            await ctx.send("❌ Error fetching your Pokémon. Try again later!")
            return
        
        user_poke = scale_stats(user_base, user_lvl)

        # Setup the CPU's Team with error handling and retry logic
        cpu_base = None
        retries = 0
        while not cpu_base and retries < 5:
            try:
                # Try random Pokemon from Gen 1 (1-151)
                cpu_base = await get_pokemon_data(str(random.randint(1, 151)))
                retries += 1
            except:
                retries += 1
        
        if not cpu_base:
            await ctx.send("❌ Error fetching wild Pokémon. Try again later!")
            return
        
        cpu_poke = scale_stats(cpu_base, cpu_lvl)

        # Final validation check
        if not user_poke or not cpu_poke:
            await ctx.send("❌ Error setting up battle data.")
            return

        # Create the Battle Instance in PvE mode
        game = PokemonBattle([user_poke], [cpu_poke], mode="pve")
        
        # Save the game instance so we can retrieve it when the user types !attack
        self.bot.active_battles[ctx.author.id] = game

        # Create the Discord Embed to show the "Versus" screen
        embed = discord.Embed(title="⚔️ Battle Started!", color=discord.Color.red())
        
        # Format types display
        user_types = "/".join(user_poke.get('types', ['???'])).title()
        cpu_types = "/".join(cpu_poke.get('types', ['???'])).title()
        
        # Add stats for the User with HP bar and type
        user_hp_bar = create_hp_bar(user_poke['hp'], user_poke['max_hp'])
        embed.add_field(name="You", value=f"**{user_poke['name']}** ({user_types})\n{user_hp_bar}", inline=True)
        
        # Add a visual separator
        embed.add_field(name="VS", value="⚡", inline=True)
        
        # Add stats for the Enemy with HP bar and type
        cpu_hp_bar = create_hp_bar(cpu_poke['hp'], cpu_poke['max_hp'])
        embed.add_field(name="Enemy", value=f"**{cpu_poke['name']}** ({cpu_types}) Lvl {cpu_lvl}\n{cpu_hp_bar}", inline=True)
        
        # Show available moves
        moves_list = "\n".join([f"{i+1}. {move['name']} ({move['type'].title()}, {move['power']} power)" 
                                 for i, move in enumerate(user_poke.get('moves', [])[:4])])
        embed.add_field(name="Your Moves", value=moves_list, inline=False)
        
        # Set the main image to the enemy's sprite so it looks like an encounter
        embed.set_image(url=cpu_poke['image']) 
        embed.set_footer(text="Type !attack <move number> to use a move! Example: !attack 1")

        await ctx.send(embed=embed)

    @commands.command()
    async def attack(self, ctx, move_num: int = 1):
        """ The main combat command used to progress the turn """
        
        # Check if the user is actually in a battle
        if ctx.author.id not in self.bot.active_battles:
            await ctx.send("You aren't in a battle!")
            return

        # Retrieve the game instance
        game = self.bot.active_battles[ctx.author.id]
        
        # Validate move number
        if move_num < 1 or move_num > 4:
            await ctx.send("⚠️ Please choose a move number between 1-4!")
            return
        
        # Convert to 0-based index
        move_index = move_num - 1
        
        # Get current attacker to check if move exists
        current_pokemon = game.get_active(game.turn)
        available_moves = current_pokemon.get('moves', [])
        
        if move_index >= len(available_moves):
            await ctx.send(f"⚠️ That move doesn't exist! You only have {len(available_moves)} moves.")
            return

        # PvP Check: Verify it is actually this user's turn
        if game.mode == "pvp":
            # Note: Ideally we store player IDs in the class, but checking the turn variable helps
            # If it is Team A's turn but the user is NOT the challenger (Player 1), block it
            if game.turn == "team_a" and ctx.author.id != game.p1_id:
                await ctx.send("It's not your turn!")
                return
            # If it is Team B's turn but the user IS the challenger, block it
            if game.turn == "team_b" and ctx.author.id == game.p1_id:
                await ctx.send("It's not your turn!")
                return
        
        # Execute the attack for whoever's turn it is with chosen move
        is_over, winner = game.attack_turn(game.turn, move_index) 
        
        # Start building the message string from the game log
        log_text = "\n".join(game.log)
        
        # PvE Logic: If playing against CPU, force the CPU to attack back immediately
        # We only do this if the game isn't over yet
        if not is_over and game.mode == "pve" and game.turn == "team_b":
            is_over, winner = game.cpu_turn()
            # Append the CPU's actions to the log text
            log_text += "\n" + "\n".join(game.log)

        # Prepare the Embed for the updated status
        p1 = game.get_active("team_a")
        p2 = game.get_active("team_b")

        embed = discord.Embed(title="⚔️ Battle Log", description=log_text, color=discord.Color.blue())
        
        # Update HP displays with visual bars
        p1_hp_bar = create_hp_bar(p1['hp'], p1['max_hp'])
        p2_hp_bar = create_hp_bar(p2['hp'], p2['max_hp'])
        embed.add_field(name="Your HP", value=f"{p1['name']}\n{p1_hp_bar}", inline=True)
        embed.add_field(name="Enemy HP", value=f"{p2['name']}\n{p2_hp_bar}", inline=True)
        
        # If game is not over, show available moves for next turn
        if not is_over and game.turn == "team_a":
            moves_list = "\n".join([f"{i+1}. {move['name']} ({move['type'].title()})" 
                                     for i, move in enumerate(p1.get('moves', [])[:4])])
            embed.add_field(name="Your Moves", value=moves_list, inline=False)
        
        # Handle Game Over scenarios
        if is_over:
            if winner == "team_a":
                embed.set_footer(text="🏆 VICTORY! You won!")
            else:
                embed.set_footer(text="💀 DEFEAT! You whited out...")
            
            # Clean up the battle instance to free memory
            del self.bot.active_battles[ctx.author.id]
            
            # If PvP, we should also delete the instance for the other player
            if game.mode == "pvp":
                other_id = game.p2_id if ctx.author.id == game.p1_id else game.p1_id
                if other_id in self.bot.active_battles:
                    del self.bot.active_battles[other_id]
        else:
            # If game continues, show whose turn it is with player nickname
            turn_name = game.get_turn_name()
            embed.set_footer(text=f"Turn: {turn_name}")

        await ctx.send(embed=embed)

    @commands.command()
    async def challenge(self, ctx, opponent: discord.Member):
        """ Challenge another user to a PvP battle """
        # Prevent challenging bots
        if opponent.bot: 
            return
        
        # Store the challenge request
        self.bot.pending_challenges[opponent.id] = ctx.author.id
        await ctx.send(f"⚔️ {opponent.mention}, **{ctx.author.name}** challenges you! Type `!accept` to fight.")

    @commands.command()
    async def accept(self, ctx):
        """ Accept a pending PvP Challenge """
        # Check if anyone has challenged this user
        if ctx.author.id not in self.bot.pending_challenges:
            await ctx.send("No active challenges found.")
            return

        # Retrieve the Challenger's ID
        challenger_id = self.bot.pending_challenges[ctx.author.id]
        
        await ctx.send("🔍 Preparing Pokémon for PvP battle...")
        
        # Fetch Data for both players with error handling
        p1_base = None
        retries = 0
        while not p1_base and retries < 5:
            try:
                p1_base = await get_pokemon_data(str(random.randint(1, 151)))
            except:
                pass
            retries += 1
        
        if not p1_base:
            await ctx.send("❌ Error fetching Player 1's Pokémon.")
            return
            
        p1_poke = scale_stats(p1_base, 50)

        p2_base = None
        retries = 0
        while not p2_base and retries < 5:
            try:
                p2_base = await get_pokemon_data(str(random.randint(1, 151)))
            except:
                pass
            retries += 1
        
        if not p2_base:
            await ctx.send("❌ Error fetching Player 2's Pokémon.")
            return
            
        p2_poke = scale_stats(p2_base, 50)

        # Initialize the PvP Game
        game = PokemonBattle([p1_poke], [p2_poke], mode="pvp")
        
        # Store the Player IDs in the game object for turn checking
        game.p1_id = challenger_id
        game.p2_id = ctx.author.id
        
        # Store player user references for display names
        game.p1_user = ctx.guild.get_member(challenger_id)
        game.p2_user = ctx.author
        
        # Link the SAME game object to both users so they share the state
        self.bot.active_battles[challenger_id] = game
        self.bot.active_battles[ctx.author.id] = game
        
        # Remove the pending challenge
        del self.bot.pending_challenges[ctx.author.id]

        # Announce the match start
        await ctx.send(f"🔔 **PvP Started!**\n**{p1_poke['name']}** (Player 1) VS **{p2_poke['name']}** (Player 2)\nPlayer 1, type `!attack`!")

    @commands.command()
    async def flee(self, ctx):
        """ Quit/forfeit your current Pokemon battle """
        if ctx.author.id not in self.bot.active_battles:
            await ctx.send("You aren't in a battle!")
            return
        
        game = self.bot.active_battles[ctx.author.id]
        
        # In PvP, notify both players
        if game.mode == "pvp":
            other_id = game.p2_id if ctx.author.id == game.p1_id else game.p1_id
            other_user = game.p2_user if ctx.author.id == game.p1_id else game.p1_user
            
            await ctx.send(f"🏃 **{ctx.author.display_name}** fled from the battle!")
            
            # Notify the other player if they exist
            if other_user:
                try:
                    await other_user.send(f"⚠️ **{ctx.author.display_name}** has fled from your battle!")
                except:
                    pass  # DMs might be closed
            
            # Clean up both players
            if ctx.author.id in self.bot.active_battles:
                del self.bot.active_battles[ctx.author.id]
            if other_id in self.bot.active_battles:
                del self.bot.active_battles[other_id]
        else:
            # PvE - just delete the battle
            await ctx.send(f"🏃 **{ctx.author.display_name}** fled from the wild Pokémon!")
            del self.bot.active_battles[ctx.author.id]


async def setup(bot):
    await bot.add_cog(Pokemon(bot))
