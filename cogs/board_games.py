"""
Board Games Cog

Commands for multi-turn board and card games:
- Blackjack: blackjack, join, hit, stand, double, split, hands, deal, quit
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
        print("BoardGames cog loaded")
    
    # === Blackjack Commands ===

    @commands.command(name='blackjack')
    async def blackjack(self, ctx):
        """Start a blackjack game"""
        if ctx.channel.id in self.bot.active_blackjack:
            await ctx.send("A game is already in progress here! Finish it first.")
            return

        game = BlackjackGame(ctx.channel.id, dealer_id=self.bot.user.id)
        self.bot.active_blackjack[ctx.channel.id] = game

        hand = game.add_player(ctx.author.id)
        score = game.get_hand_value(hand)
        dealer_str = game.display_hand(game.dealer_hand, hide_second_card=True)

        msg = (f"**🃏 Blackjack Started!**\n"
               f"**{ctx.author.display_name}**: {game.display_hand(hand)} (**{score}**)\n"
               f"**Dealer**: {dealer_str}\n")

        if game.is_natural_blackjack(ctx.author.id):
            msg += "🌟 **Natural Blackjack!** Wait for other players or type `!stand`."
        else:
            msg += "Type `!hit`, `!stand`, `!double`, `!split`, or `!join`."

        await ctx.send(msg)

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
        score = game.get_hand_value(hand)

        msg = (f"**{ctx.author.display_name}** joined!\n"
               f"Your Hand: {game.display_hand(hand)} (**{score}**)\n")

        if game.is_natural_blackjack(ctx.author.id):
            msg += "🌟 **Natural Blackjack!**"
        else:
            msg += "Type `!hit`, `!stand`, `!double`, or `!split`."

        await ctx.send(msg)

    @commands.command(name='hit')
    async def hit(self, ctx):
        """Draw another card in blackjack"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        game = self.bot.active_blackjack[ctx.channel.id]
        if ctx.author.id not in game.players:
            return

        if game.get_active_status(ctx.author.id) != 'playing':
            await ctx.send(f"{ctx.author.display_name}, your current hand is done. Use `!stand` to finish or wait.")
            return

        hand, score, busted = game.hit(ctx.author.id)
        hand_str = game.display_hand(hand)

        if busted:
            await ctx.send(f"**{ctx.author.display_name}** hits → {hand_str} (**{score}**) 💥 **BUSTED!**")
            # Try to advance to the next split hand
            if game.advance_hand(ctx.author.id):
                next_hand = game.get_active_hand(ctx.author.id)
                p = game._p(ctx.author.id)
                hand_num = p['active'] + 1
                await ctx.send(f"➡️ Playing Hand {hand_num}: {game.display_hand(next_hand)} (**{game.get_hand_value(next_hand)}**)")
            elif game.everyone_is_done():
                await self.end_game(ctx, game)
        else:
            await ctx.send(f"**{ctx.author.display_name}** hits → {hand_str} (**{score}**)")

    @commands.command(name='stand')
    async def stand(self, ctx):
        """Stand your current hand in blackjack"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        game = self.bot.active_blackjack[ctx.channel.id]
        if ctx.author.id not in game.players:
            return

        score = game.stand(ctx.author.id)
        await ctx.send(f"**{ctx.author.display_name}** stands with **{score}**.")

        # Advance to next split hand if any
        if game.advance_hand(ctx.author.id):
            next_hand = game.get_active_hand(ctx.author.id)
            p = game._p(ctx.author.id)
            hand_num = p['active'] + 1
            await ctx.send(f"➡️ Playing Hand {hand_num}: {game.display_hand(next_hand)} (**{game.get_hand_value(next_hand)}**)")
        elif game.everyone_is_done():
            await self.end_game(ctx, game)

    @commands.command(name='double')
    async def double(self, ctx):
        """Double down: draw one card and auto-stand"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        game = self.bot.active_blackjack[ctx.channel.id]
        if ctx.author.id not in game.players:
            return

        if not game.can_double(ctx.author.id):
            await ctx.send("❌ You can only double down on your first two cards!")
            return

        hand, score, busted = game.double_down(ctx.author.id)
        hand_str = game.display_hand(hand)

        if busted:
            await ctx.send(f"**{ctx.author.display_name}** doubles → {hand_str} (**{score}**) 💥 **BUSTED!**")
        else:
            await ctx.send(f"**{ctx.author.display_name}** doubles → {hand_str} (**{score}**) ✅ Auto-stood.")

        if game.advance_hand(ctx.author.id):
            next_hand = game.get_active_hand(ctx.author.id)
            p = game._p(ctx.author.id)
            hand_num = p['active'] + 1
            await ctx.send(f"➡️ Playing Hand {hand_num}: {game.display_hand(next_hand)} (**{game.get_hand_value(next_hand)}**)")
        elif game.everyone_is_done():
            await self.end_game(ctx, game)

    @commands.command(name='split')
    async def split(self, ctx):
        """Split a pair into two separate hands"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        game = self.bot.active_blackjack[ctx.channel.id]
        if ctx.author.id not in game.players:
            return

        if not game.can_split(ctx.author.id):
            await ctx.send("❌ You can only split two cards of the same rank!")
            return

        hand1, hand2 = game.do_split(ctx.author.id)
        await ctx.send(
            f"✂️ **{ctx.author.display_name}** splits!\n"
            f"**Hand 1**: {game.display_hand(hand1)} (**{game.get_hand_value(hand1)}**)\n"
            f"**Hand 2**: {game.display_hand(hand2)} (**{game.get_hand_value(hand2)}**)\n"
            f"Play Hand 1 first — `!hit`, `!stand`, or `!double`."
        )

    @commands.command(name='hands')
    async def hands(self, ctx):
        """Show all your current blackjack hands"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return
        game = self.bot.active_blackjack[ctx.channel.id]
        if ctx.author.id not in game.players:
            await ctx.send("You're not in the game!")
            return

        p = game._p(ctx.author.id)
        lines = []
        for i, (hand, status, score) in enumerate(zip(p['hands'], p['statuses'], p['scores'])):
            marker = " ← active" if i == p['active'] else ""
            lines.append(f"**Hand {i+1}** [{status}]{marker}: {game.display_hand(hand)} (**{score}**)")

        await ctx.send(f"🃏 **{ctx.author.display_name}'s hands:**\n" + "\n".join(lines))

    @commands.command(name='deal')
    async def deal(self, ctx):
        """Start a new round of blackjack"""
        if ctx.channel.id not in self.bot.active_blackjack:
            await ctx.send("No game running. Type `!blackjack` to start one.")
            return

        game = self.bot.active_blackjack[ctx.channel.id]

        if not game.everyone_is_done():
            await ctx.send("Wait for the current round to finish!")
            return

        game.reset_round()
        dealer_str = game.display_hand(game.dealer_hand, hide_second_card=True)
        message = f"**🃏 New Round!**\n**Dealer**: {dealer_str}\n\n"

        for user_id, p in game.players.items():
            hand = p['hands'][0]
            score = p['scores'][0]
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else "Unknown"
            message += f"**{name}**: {game.display_hand(hand)} ({score})\n"

        await ctx.send(message)

    @commands.command(name='quit')
    async def quit(self, ctx):
        """Leave the blackjack game"""
        if ctx.channel.id not in self.bot.active_blackjack:
            return

        game = self.bot.active_blackjack[ctx.channel.id]

        if ctx.author.id not in game.players:
            await ctx.send("You're not in the game!")
            return

        del game.players[ctx.author.id]
        await ctx.send(f"**{ctx.author.display_name}** left the game.")

        if len(game.players) == 0:
            del self.bot.active_blackjack[ctx.channel.id]
            await ctx.send("Game closed. No players remaining.")

    async def end_game(self, ctx, game):
        """End the round, reveal dealer, and determine winners across all hands"""
        await ctx.send("--- All players done! Dealer's Turn ---")

        dealer_score = game.dealer_play()
        await ctx.send(f"**Dealer** reveals: {game.display_hand(game.dealer_hand)} (**{dealer_score}**)")

        final_message = ""
        for user_id, p in game.players.items():
            member = ctx.guild.get_member(user_id)
            try:
                name = member.display_name if member else (await self.bot.fetch_user(user_id)).name
            except:
                name = "Unknown"

            for i, (hand, status, score) in enumerate(zip(p['hands'], p['statuses'], p['scores'])):
                label = f"**{name}**" if len(p['hands']) == 1 else f"**{name} (Hand {i+1})**"
                if status == 'busted':
                    final_message += f"{label} busted! ({score})\n"
                elif status == 'doubled':
                    if dealer_score > 21 or score > dealer_score:
                        final_message += f"{label} wins with a double! ({score} vs {dealer_score}) 💰\n"
                    elif score == dealer_score:
                        final_message += f"{label} pushed on double. (Tie)\n"
                    else:
                        final_message += f"{label} lost on double. ({score} vs {dealer_score})\n"
                elif len(p['hands'][i]) == 2 and score == 21:
                    final_message += f"{label} 🌟 Natural Blackjack! Wins!\n"
                elif dealer_score > 21:
                    final_message += f"{label} wins! Dealer busted.\n"
                elif score > dealer_score:
                    final_message += f"{label} wins! ({score} vs {dealer_score})\n"
                elif score == dealer_score:
                    final_message += f"{label} pushed (Tie).\n"
                else:
                    final_message += f"{label} lost. ({score} vs {dealer_score})\n"

        await ctx.send(final_message)
        await ctx.send("Round Over! Type `!deal` to play again or `!quit` to leave.")
    
    # === Death Roll Commands ===
    
    @commands.command(name='deathroll')
    async def deathroll(self, ctx, ceiling: int = None):
        """Start a death roll game. Usage: !deathroll <number>"""
        if ceiling is None:
            await ctx.send("⚠️ You need to provide a starting number!\nUsage: `!deathroll <number>` (e.g. `!deathroll 1000`)")
            return

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
