import os
import discord
from discord.ext import commands

from weather_api import get_weather_data
from blackjack_game import BlackjackGame

"""
Bugg Bot - Main Discord Bot Module

A multi-purpose Discord bot featuring:
- Weather forecasts for US cities
- Multiplayer blackjack game with persistent rounds
- Utility and test commands

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
active_games = {} # A dictionary to track games: {channel_id: BlackjackGame_Object}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")

# === Test Commands ===
@bot.command()
async def ping(ctx):
    # Simple test command that responds with "Pong!"
    await ctx.send("Pong!")

# === Utility Commands ===
@bot.command()
async def hello(ctx):
    # Greets the user
    await ctx.send(f"Hello, {ctx.author.mention}!")

@bot.command(name = 'weather')
async def weather_command(ctx, *, city_name: str):
    # Get the current weather forecast for a specified US city
    # The '*' ensures the entire city is captured (e.g. "San Francisco")   
    # Get data from helper function
    forecast_message = await get_weather_data(city_name)

    # Send result back
    await ctx.send(forecast_message)

# === Blackjack Helper Functions ===
async def end_game(ctx, game):
    # Runs the Dealer's turn and announces the winners
    await ctx.send("--- All players done! Dealer's Turn ---")
    
    # Dealer Plays Logic
    dealer_score = game.dealer_play()
    dealer_hand_str = game.display_hand(game.dealer_hand)
    
    await ctx.send(f"**Dealer** reveals: {dealer_hand_str} (**{dealer_score}**)")

    # Check Winners
    final_message = ""
    for user_id, data in game.players.items():
        player_score = data[2]
        player_status = data[1]
        
        # Get server nickname - try multiple methods
        member = ctx.guild.get_member(user_id)
        if member:
            name = member.display_name
        else:
            # Fallback to fetching user
            try:
                user = await bot.fetch_user(user_id)
                name = user.name
            except:
                name = "Unknown Player"

        if player_status == "busted":
            final_message += f"**{name}** busted! (Score: {player_score})\n"
        elif dealer_score > 21:
            final_message += f"**{name}** wins! Dealer busted.\n"
        elif player_score > dealer_score:
             final_message += f"**{name}** wins! ({player_score} vs {dealer_score})\n"
        elif player_score == dealer_score:
             final_message += f"**{name}** pushed (Tie).\n"
        else:
             final_message += f"**{name}** lost. ({player_score} vs {dealer_score})\n"

    await ctx.send(final_message)
    await ctx.send("Round Over! Type `!deal` to play again or `!quit` to leave.")

# === Blackjack Commands ===
@bot.command(name = 'blackjack')
async def blackjack(ctx):
    if ctx.channel.id in active_games:
        await ctx.send("A game is already in progress here! Finish it first.")
        return

    # Create and store the game
    game = BlackjackGame(ctx.channel.id, dealer_id = bot.user.id)
    active_games[ctx.channel.id] = game
    
    # Add the player who started it
    hand = game.add_player(ctx.author.id)
    
    # Send display
    player_hand_str = game.display_hand(hand)
    dealer_hand_str = game.display_hand(game.dealer_hand, hide_second_card=True)
    
    await ctx.send(f"**Game Started!**\n"
                   f"**{ctx.author.display_name}**: {player_hand_str} ({game.get_hand_value(hand)})\n"
                   f"**Dealer**: {dealer_hand_str}\n"
                   f"Type `!hit`, `!stand`, or `!join`.")

@bot.command()
async def join(ctx):
    if ctx.channel.id not in active_games:
        await ctx.send("No game running. Type `!blackjack` to start one.")
        return

    game = active_games[ctx.channel.id]

    if ctx.author.id in game.players:
        await ctx.send("You are already in the game!")
        return

    hand = game.add_player(ctx.author.id)
    player_hand_str = game.display_hand(hand)

    await ctx.send(f"**{ctx.author.display_name}** joined!\n"
                   f"Your Hand: {player_hand_str} ({game.get_hand_value(hand)})")

@bot.command()
async def hit(ctx):
    if ctx.channel.id not in active_games:
        return
    game = active_games[ctx.channel.id]
    if ctx.author.id not in game.players:
        return

    # Check if they can play
    current_data = game.players[ctx.author.id]
    if current_data[1] != "playing":
        await ctx.send(f"{ctx.author.display_name}, your turn is over.")
        return

    # Deal a card
    new_card = game.deck.pop()
    current_data[0].append(new_card)
    
    # Update Score
    new_score = game.get_hand_value(current_data[0])
    current_data[2] = new_score

    hand_str = game.display_hand(current_data[0])

    if new_score > 21:
        current_data[1] = "busted"
        await ctx.send(f"**{ctx.author.display_name}** hits.. {hand_str} (**{new_score}**) -> BUSTED!")
        # If everyone is done, end the game
        if game.everyone_is_done():
            await end_game(ctx, game)
    else:
        await ctx.send(f"**{ctx.author.display_name}** hits.. {hand_str} (**{new_score}**)")

@bot.command()
async def stand(ctx):
    if ctx.channel.id not in active_games:
        return
    game = active_games[ctx.channel.id]
    if ctx.author.id not in game.players:
        return

    # Set status to "stood"
    game.players[ctx.author.id][1] = "stood"
    score = game.players[ctx.author.id][2]
    
    await ctx.send(f"**{ctx.author.display_name}** stands with **{score}**.")

    # Check if everyone is waiting for dealer
    if game.everyone_is_done():
        await end_game(ctx, game)

@bot.command()
async def deal(ctx):
    # Play again command
    if ctx.channel.id not in active_games:
        await ctx.send("No game running. Type `!blackjack` to start one.")
        return
    
    game = active_games[ctx.channel.id]
    
    # Check if round is finished
    if not game.everyone_is_done():
        await ctx.send("Wait for the current round to finish!")
        return
    
    # Reset the round
    game.reset_round()
    
    # Display dealer's new hand
    dealer_hand_str = game.display_hand(game.dealer_hand, hide_second_card=True)
    message = f"**New Round Started!**\n**Dealer**: {dealer_hand_str}\n\n"
    
    # Display all players' new hands
    for user_id, data in game.players.items():
        hand = data[0]
        score = data[2]
        member = ctx.guild.get_member(user_id)
        if member:
            name = member.display_name
        else:
            try:
                user = await bot.fetch_user(user_id)
                name = user.name
            except:
                name = "Unknown Player"
        
        hand_str = game.display_hand(hand)
        message += f"**{name}**: {hand_str} ({score})\n"
    
    await ctx.send(message)

@bot.command()
async def quit(ctx):
    # Leave the game
    if ctx.channel.id not in active_games:
        return
    
    game = active_games[ctx.channel.id]
    
    # Check if user is in the game
    if ctx.author.id not in game.players:
        await ctx.send("You're not in the game!")
        return
    
    # Remove player from game
    del game.players[ctx.author.id]
    await ctx.send(f"**{ctx.author.display_name}** left the game.")
    
    # Check if table is empty
    if len(game.players) == 0:
        del active_games[ctx.channel.id]
        await ctx.send("Game closed. No players remaining.")

if __name__ == "__main__":
    bot.run(TOKEN)
