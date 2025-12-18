"""
Board Games Cog

Commands for multi-turn board and card games:
- Blackjack: blackjack, join, hit, stand, deal, quit
- Death Roll: deathroll, drjoin, drroll, drquit
- Tic-Tac-Toe: tictactoe, move
- Connect Four: connect4, drop

State tracking:
- bot.active_blackjack: Tracks active Blackjack games by channel_id
- bot.active_deathroll: Tracks active Death Roll games by channel_id
- bot.active_tictactoe: Tracks active Tic-Tac-Toe games by channel_id
- bot.active_connect4: Tracks active Connect Four games by channel_id
"""

import discord
from discord.ext import commands

# Import game logic from the games module (helper file)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helper.games import BlackjackGame, DeathRollGame, TicTacToeGame, Connect4Game


class BoardGames(commands.Cog):
    """Multi-turn board and card games"""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize state dictionaries on the bot object
        if not hasattr(bot, 'active_blackjack'):
            bot.active_blackjack = {}
        if not hasattr(bot, 'active_deathroll'):
            bot.active_deathroll = {}
        if not hasattr(bot, 'active_tictactoe'):
            bot.active_tictactoe = {}
        if not hasattr(bot, 'active_connect4'):
            bot.active_connect4 = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ BoardGames cog loaded")
    
    # === Blackjack Commands ===
    
    @commands.command(name='blackjack')
    async def blackjack(self, ctx):
        """Start a blackjack game"""
        if ctx.channel.id in self.bot.active_blackjack:
            await ctx.send("A game is already in progress here! Finish it first.")
            return

        # Create and store the game
        game = BlackjackGame(ctx.channel.id, dealer_id=self.bot.user.id)
        self.bot.active_blackjack[ctx.channel.id] = game
        
        # Add the player who started it
        hand = game.add_player(ctx.author.id)
        
        # Send display
        player_hand_str = game.display_hand(hand)
        dealer_hand_str = game.display_hand(game.dealer_hand, hide_second_card=True)
        
        await ctx.send(f"**Game Started!**\n"
                       f"**{ctx.author.display_name}**: {player_hand_str} ({game.get_hand_value(hand)})\n"
                       f"**Dealer**: {dealer_hand_str}\n"
                       f"Type `!hit`, `!stand`, or `!join`.")
    
    @commands.command(name='join')
    async def join(self, ctx):
        """Join an active blackjack game"""
        if ctx.channel.id not in self.bot.active_blackjack:
            await ctx.send("No game running. Type `!blackjack` to start one.")
            return

        game = self.bot.active_blackjack[ctx.channel.id]

        if ctx.author.id in game.players:
            await ctx.send("You are already in the game!")
            return

        hand = game.add_player(ctx.author.id)
        player_hand_str = game.display_hand(hand)

        await ctx.send(f"**{ctx.author.display_name}** joined!\n"
                       f"Your Hand: {player_hand_str} ({game.get_hand_value(hand)})")
    
    @commands.command(name='hit')
    async def hit(self, ctx):
        """Draw another card in blackjack"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        game = self.bot.active_blackjack[ctx.channel.id]
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
                await self.end_game(ctx, game)
        else:
            await ctx.send(f"**{ctx.author.display_name}** hits.. {hand_str} (**{new_score}**)")
    
    @commands.command(name='stand')
    async def stand(self, ctx):
        """End your turn in blackjack"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        game = self.bot.active_blackjack[ctx.channel.id]
        if ctx.author.id not in game.players:
            return

        # Set status to "stood"
        game.players[ctx.author.id][1] = "stood"
        score = game.players[ctx.author.id][2]
        
        await ctx.send(f"**{ctx.author.display_name}** stands with **{score}**.")

        # Check if everyone is waiting for dealer
        if game.everyone_is_done():
            await self.end_game(ctx, game)
    
    @commands.command(name='deal')
    async def deal(self, ctx):
        """Start a new round of blackjack"""
        if ctx.channel.id not in self.bot.active_blackjack:
            await ctx.send("No game running. Type `!blackjack` to start one.")
            return
        
        game = self.bot.active_blackjack[ctx.channel.id]
        
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
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except:
                    name = "Unknown Player"
            
            hand_str = game.display_hand(hand)
            message += f"**{name}**: {hand_str} ({score})\n"
        
        await ctx.send(message)
    
    @commands.command(name='quit')
    async def quit(self, ctx):
        """Leave the blackjack game"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        
        game = self.bot.active_blackjack[ctx.channel.id]
        
        # Check if user is in the game
        if ctx.author.id not in game.players:
            await ctx.send("You're not in the game!")
            return
        
        # Remove player from game
        del game.players[ctx.author.id]
        await ctx.send(f"**{ctx.author.display_name}** left the game.")
        
        # Check if table is empty
        if len(game.players) == 0:
            del self.bot.active_blackjack[ctx.channel.id]
            await ctx.send("Game closed. No players remaining.")
    
    async def end_game(self, ctx, game):
        """Helper function to end a blackjack round"""
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
                    user = await self.bot.fetch_user(user_id)
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
    
    # === Death Roll Commands ===
    
    @commands.command(name='deathroll')
    async def deathroll(self, ctx, ceiling: int = 100):
        """Start a death roll game"""
        if ctx.channel.id in self.bot.active_deathroll:
            await ctx.send("A death roll is already active here! Finish it first with `!drquit`")
            return
        
        if ceiling < 2 or ceiling > 10000:
            await ctx.send("Ceiling must be between 2 and 10,000!")
            return
        
        # Create new death roll game
        game = DeathRollGame(ctx.author.id, start_cap=ceiling)
        self.bot.active_deathroll[ctx.channel.id] = game
        
        await ctx.send(f"💀 **Death Roll Started!**\n"
                       f"**{ctx.author.display_name}** is waiting for an opponent!\n"
                       f"Starting ceiling: **{ceiling}**\n"
                       f"Type `!drjoin` to join, then `!drroll` to roll!")
    
    @commands.command(name='drjoin')
    async def drjoin(self, ctx):
        """Join a death roll game"""
        if ctx.channel.id not in self.bot.active_deathroll:
            await ctx.send("No death roll game active! Start one with `!deathroll <ceiling>`")
            return
        
        game = self.bot.active_deathroll[ctx.channel.id]
        
        if len(game.players) >= 2:
            await ctx.send("Game is full! Only 2 players allowed.")
            return
        
        if ctx.author.id in game.players:
            await ctx.send("You're already in this game!")
            return
        
        game.players.append(ctx.author.id)
        await ctx.send(f"**{ctx.author.display_name}** joined the death roll!\n"
                       f"Type `!drroll` to start rolling!")
    
    @commands.command(name='drroll')
    async def drroll(self, ctx):
        """Take your turn in death roll"""
        if ctx.channel.id not in self.bot.active_deathroll:
            return
        
        game = self.bot.active_deathroll[ctx.channel.id]
        
        if ctx.author.id not in game.players:
            await ctx.send("You're not in this game!")
            return
        
        if len(game.players) < 2:
            await ctx.send("Need 2 players to start rolling!")
            return
        
        # Check if it's their turn
        current_player_id = game.players[game.turn_index]
        if ctx.author.id != current_player_id:
            member = ctx.guild.get_member(current_player_id)
            name = member.display_name if member else "Unknown"
            await ctx.send(f"It's **{name}**'s turn!")
            return
        
        # Roll!
        roll_result, is_loss = game.take_turn()
        
        if is_loss:
            await ctx.send(f"🎲 **{ctx.author.display_name}** rolled **{roll_result}**\n"
                           f"💀 **{ctx.author.display_name} LOSES!** 💀")
            del self.bot.active_deathroll[ctx.channel.id]
        else:
            # Move to next player's turn
            game.turn_index = (game.turn_index + 1) % len(game.players)
            next_player_id = game.players[game.turn_index]
            next_member = ctx.guild.get_member(next_player_id)
            next_name = next_member.display_name if next_member else "Unknown"
            
            await ctx.send(f"🎲 **{ctx.author.display_name}** rolled **{roll_result}**\n"
                           f"New ceiling: **{game.current_cap}**\n"
                           f"**{next_name}**'s turn! Roll `!drroll`")
    
    @commands.command(name='drquit')
    async def drquit(self, ctx):
        """Cancel/quit the death roll game"""
        if ctx.channel.id not in self.bot.active_deathroll:
            return
        
        del self.bot.active_deathroll[ctx.channel.id]
        await ctx.send("💀 Death roll cancelled.")
    
    # === Tic Tac Toe Commands ===
    
    @commands.command()
    async def tictactoe(self, ctx, opponent: discord.Member):
        """Start a tic-tac-toe game"""
        if opponent.bot or opponent == ctx.author:
            await ctx.send("You can only play against other humans!")
            return
        
        if ctx.channel.id in self.bot.active_tictactoe:
            await ctx.send("A tic-tac-toe game is already active in this channel!")
            return
        
        game = TicTacToeGame(ctx.author.id, opponent.id)
        self.bot.active_tictactoe[ctx.channel.id] = game
        
        await ctx.send(f"⭕❌ **Tic-Tac-Toe Started!**\n"
                       f"{ctx.author.mention} (❌) vs {opponent.mention} (⭕)\n"
                       f"{game.get_board_display()}\n"
                       f"{ctx.author.mention}'s turn! Type `!move <1-9>` to place your mark.")
    
    @commands.command()
    async def move(self, ctx, position: int):
        """Make a move in tic-tac-toe"""
        if ctx.channel.id not in self.bot.active_tictactoe:
            return
        
        game = self.bot.active_tictactoe[ctx.channel.id]
        success, result = game.make_move(ctx.author.id, position)
        
        if not success:
            if result == "not_your_turn":
                await ctx.send("❌ It's not your turn!")
            elif result == "invalid":
                await ctx.send("❌ Invalid position! Use 1-9.")
            elif result == "occupied":
                await ctx.send("❌ That spot is already taken!")
            return
        
        if result == "win":
            await ctx.send(f"{game.get_board_display()}\n"
                          f"🎉 **{ctx.author.mention} wins!**")
            del self.bot.active_tictactoe[ctx.channel.id]
        elif result == "draw":
            await ctx.send(f"{game.get_board_display()}\n"
                          f"🤝 **It's a draw!**")
            del self.bot.active_tictactoe[ctx.channel.id]
        else:
            next_player = ctx.guild.get_member(game.current_turn)
            await ctx.send(f"{game.get_board_display()}\n"
                          f"{next_player.mention}'s turn!")
    
    # === Connect 4 Commands ===
    
    @commands.command()
    async def connect4(self, ctx, opponent: discord.Member):
        """Start a Connect Four game"""
        if opponent.bot or opponent == ctx.author:
            await ctx.send("You can only play against other humans!")
            return
        
        if ctx.channel.id in self.bot.active_connect4:
            await ctx.send("A Connect Four game is already active in this channel!")
            return
        
        game = Connect4Game(ctx.author.id, opponent.id)
        self.bot.active_connect4[ctx.channel.id] = game
        
        await ctx.send(f"🔴🟡 **Connect Four Started!**\n"
                       f"{ctx.author.mention} (🔴) vs {opponent.mention} (🟡)\n"
                       f"{game.get_board_display()}\n"
                       f"{ctx.author.mention}'s turn! Type `!drop <1-7>` to drop a piece.")
    
    @commands.command()
    async def drop(self, ctx, column: int):
        """Drop a piece in Connect Four"""
        if ctx.channel.id not in self.bot.active_connect4:
            return
        
        game = self.bot.active_connect4[ctx.channel.id]
        success, result = game.drop_piece(ctx.author.id, column)
        
        if not success:
            if result == "not_your_turn":
                await ctx.send("❌ It's not your turn!")
            elif result == "invalid":
                await ctx.send("❌ Invalid column! Use 1-7.")
            elif result == "column_full":
                await ctx.send("❌ That column is full!")
            return
        
        if result == "win":
            await ctx.send(f"{game.get_board_display()}\n"
                          f"🎉 **{ctx.author.mention} wins!**")
            del self.bot.active_connect4[ctx.channel.id]
        elif result == "draw":
            await ctx.send(f"{game.get_board_display()}\n"
                          f"🤝 **It's a draw!**")
            del self.bot.active_connect4[ctx.channel.id]
        else:
            next_player = ctx.guild.get_member(game.current_turn)
            await ctx.send(f"{game.get_board_display()}\n"
                          f"{next_player.mention}'s turn!")


async def setup(bot):
    await bot.add_cog(BoardGames(bot))
