"""
Word Games Cog

Commands for word-based and message-driven games:
- Hangman: hangman, quithangman (+ on_message for letter guesses)
- Wordle: wordle, guess, quitwordle
- Akinator: akinator, quitakinator (+ on_message for yes/no answers)
- TypeRace: typerace, quittyperace (+ on_message for submissions)

State tracking:
- bot.active_hangman: Tracks active Hangman games by channel_id
- bot.active_wordle: Tracks active Wordle games by user_id
- bot.active_akinator: Tracks active Akinator games by user_id
- bot.active_typerace: Tracks active TypeRace games by user_id

Note: This cog includes an on_message listener that handles game
interactions for all four game types with priority checking.
"""

import discord
from discord.ext import commands

# Import game logic from the games module (helper file)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helper.games import HangmanGame, WordleGame, AkinatorGame, TypeRaceGame


class WordGames(commands.Cog):
    """Word-based and message-driven games"""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize state dictionaries on the bot object
        if not hasattr(bot, 'active_hangman'):
            bot.active_hangman = {}
        if not hasattr(bot, 'active_wordle'):
            bot.active_wordle = {}
        if not hasattr(bot, 'active_akinator'):
            bot.active_akinator = {}
        if not hasattr(bot, 'active_typerace'):
            bot.active_typerace = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ WordGames cog loaded")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle message-based game interactions"""
        if message.author.bot:
            return
        
        # Check for active Akinator game
        if message.author.id in self.bot.active_akinator:
            content = message.content.lower()
            if content in ["yes", "y", "no", "n"] and not message.content.startswith("!"):
                game = self.bot.active_akinator[message.author.id]
                
                status = game.answer_question(content)
                
                if status == "guess_ready":
                    guess = game.make_guess()
                    await message.channel.send(f"🔮 I think you're thinking of: **{guess}**\n"
                                             f"Was I right? (yes/no)")
                elif status == "stumped":
                    await message.channel.send(f"🤯 I give up! I couldn't figure it out. You win!")
                    del self.bot.active_akinator[message.author.id]
                elif status == "continue":
                    question = game.get_current_question()
                    question_num = game.current_question_index + 1
                    await message.channel.send(f"**Question {question_num}:** {question}")
                
                # Don't process as command
                return
            elif content in ["yes", "y", "no", "n"] and message.content.startswith("!"):
                # This is checking the final guess
                if content in ["yes", "y"]:
                    await message.channel.send(f"🎉 I win! Thanks for playing!")
                else:
                    await message.channel.send(f"😢 Aw, I was so close! Good game!")
                del self.bot.active_akinator[message.author.id]
                return
        
        # Check for active Type Race game
        if message.author.id in self.bot.active_typerace:
            if not message.content.startswith("!"):
                game = self.bot.active_typerace[message.author.id]
                results = game.finish(message.content)
                
                if results["correct"]:
                    await message.channel.send(
                        f"🏁 **Perfect!**\n"
                        f"⏱️ Time: {results['time']:.2f}s\n"
                        f"⌨️ WPM: {results['wpm']:.1f}\n"
                        f"✅ Accuracy: {results['accuracy']:.1f}%"
                    )
                else:
                    await message.channel.send(
                        f"⌨️ **Type Race Complete!**\n"
                        f"⏱️ Time: {results['time']:.2f}s\n"
                        f"⌨️ WPM: {results['wpm']:.1f}\n"
                        f"✅ Accuracy: {results['accuracy']:.1f}%\n"
                        f"❌ Not quite perfect, but great effort!"
                    )
                
                del self.bot.active_typerace[message.author.id]
                return
        
        # Check if there's an active hangman game in this channel
        if message.channel.id in self.bot.active_hangman:
            # Check if message is a single letter
            if len(message.content) == 1 and message.content.isalpha():
                game = self.bot.active_hangman[message.channel.id]
                letter = message.content.lower()
                
                status = game.guess_letter(letter)
                
                if status == "already_guessed":
                    await message.channel.send(f"❌ You already guessed '{letter}'!")
                elif status == "won":
                    await message.channel.send(f"{game.get_hangman_art()}\n"
                                             f"Word: {game.get_display_word()}\n\n"
                                             f"🎉 **Congratulations!** You won! The word was **{game.word}**")
                    del self.bot.active_hangman[message.channel.id]
                elif status == "lost":
                    await message.channel.send(f"{game.get_hangman_art()}\n"
                                             f"Word: {game.get_display_word()}\n\n"
                                             f"💀 **Game Over!** The word was **{game.word}**")
                    del self.bot.active_hangman[message.channel.id]
                else:
                    # Game continues
                    result = "✅ Correct!" if status == "correct" else f"❌ Wrong! '{letter}' is not in the word."
                    await message.channel.send(f"{result}\n"
                                             f"{game.get_hangman_art()}\n"
                                             f"Word: {game.get_display_word()}\n"
                                             f"Guessed: {', '.join(sorted(game.guessed_letters))}\n"
                                             f"Wrong guesses: {game.wrong_guesses}/{game.max_wrong}")
    
    # === Hangman Commands ===
    
    @commands.command()
    async def hangman(self, ctx, category: str = "random"):
        """Start a hangman game"""
        valid_categories = ["animals", "food", "countries", "movies", "random"]
        
        if category not in valid_categories:
            await ctx.send(f"❌ Invalid category! Choose from: {', '.join(valid_categories)}")
            return
        
        if ctx.channel.id in self.bot.active_hangman:
            await ctx.send("A hangman game is already active in this channel!")
            return
        
        game = HangmanGame(category)
        self.bot.active_hangman[ctx.channel.id] = game
        
        await ctx.send(f"🎯 **Hangman Started!** Category: **{game.category}**\n"
                       f"{game.get_hangman_art()}\n"
                       f"Word: {game.get_display_word()}\n"
                       f"Guessed: {', '.join(sorted(game.guessed_letters)) if game.guessed_letters else 'None'}\n"
                       f"Wrong guesses: {game.wrong_guesses}/{game.max_wrong}\n\n"
                       f"Type a letter to guess!")
    
    @commands.command()
    async def quithangman(self, ctx):
        """Quit the current hangman game"""
        if ctx.channel.id not in self.bot.active_hangman:
            await ctx.send("No active hangman game!")
            return
        
        game = self.bot.active_hangman[ctx.channel.id]
        await ctx.send(f"Game ended. The word was **{game.word}**")
        del self.bot.active_hangman[ctx.channel.id]
    
    # === Wordle Commands ===
    
    @commands.command()
    async def wordle(self, ctx):
        """Start a Wordle game"""
        if ctx.author.id in self.bot.active_wordle:
            await ctx.send("You already have an active Wordle game! Use `!guess <word>` to play or `!quitwordle` to end it.")
            return
        
        game = WordleGame()
        self.bot.active_wordle[ctx.author.id] = game
        
        await ctx.send(f"🟩 **Wordle Started!**\n"
                       f"Guess a 5-letter word! You have 6 attempts.\n"
                       f"```\n{game.get_board_display()}```\n"
                       f"Type `!guess <word>` to make a guess!\n\n"
                       f"🟩 = Correct letter, correct position\n"
                       f"🟨 = Correct letter, wrong position\n"
                       f"⬜ = Letter not in word")
    
    @commands.command()
    async def guess(self, ctx, word: str):
        """Make a guess in Wordle"""
        if ctx.author.id not in self.bot.active_wordle:
            await ctx.send("You don't have an active Wordle game! Start one with `!wordle`")
            return
        
        game = self.bot.active_wordle[ctx.author.id]
        feedback, status = game.make_guess(word)
        
        if status == "invalid_length":
            await ctx.send("❌ Word must be 5 letters!")
            return
        elif status == "invalid_chars":
            await ctx.send("❌ Word must only contain letters!")
            return
        elif status == "no_attempts":
            await ctx.send("❌ You're out of attempts!")
            return
        
        # Display feedback for this guess
        guess_display = " ".join([color for letter, color in feedback])
        letter_display = " ".join([letter for letter, color in feedback])
        
        if status == "won":
            await ctx.send(f"{letter_display}\n{guess_display}\n\n"
                          f"🎉 **Congratulations!** You guessed the word in {len(game.attempts)} attempt(s)!")
            del self.bot.active_wordle[ctx.author.id]
        elif status == "lost":
            await ctx.send(f"{letter_display}\n{guess_display}\n\n"
                          f"💀 **Game Over!** The word was **{game.word}**")
            del self.bot.active_wordle[ctx.author.id]
        else:
            remaining = game.max_attempts - len(game.attempts)
            await ctx.send(f"{letter_display}\n{guess_display}\n\n"
                          f"Attempts remaining: {remaining}")
    
    @commands.command()
    async def quitwordle(self, ctx):
        """Quit your current Wordle game"""
        if ctx.author.id not in self.bot.active_wordle:
            await ctx.send("You don't have an active Wordle game!")
            return
        
        game = self.bot.active_wordle[ctx.author.id]
        await ctx.send(f"Game ended. The word was **{game.word}**")
        del self.bot.active_wordle[ctx.author.id]
    
    # === Akinator Commands ===
    
    @commands.command()
    async def akinator(self, ctx):
        """Play 20 questions - the bot tries to guess what you're thinking"""
        if ctx.author.id in self.bot.active_akinator:
            await ctx.send("You already have an active Akinator game! Answer with yes/no or type `!quitakinator`")
            return
        
        game = AkinatorGame()
        self.bot.active_akinator[ctx.author.id] = game
        
        question = game.get_current_question()
        await ctx.send(f"🔮 **Akinator Started!**\n"
                       f"Think of something and I'll try to guess it!\n\n"
                       f"**Question 1:** {question}\n"
                       f"Answer with **yes** or **no**")
    
    @commands.command()
    async def quitakinator(self, ctx):
        """Quit your current Akinator game"""
        if ctx.author.id not in self.bot.active_akinator:
            await ctx.send("You don't have an active Akinator game!")
            return
        
        del self.bot.active_akinator[ctx.author.id]
        await ctx.send("🔮 Akinator game ended. Thanks for playing!")
    
    # === Type Race Commands ===
    
    @commands.command()
    async def typerace(self, ctx):
        """Start a typing speed challenge"""
        if ctx.author.id in self.bot.active_typerace:
            await ctx.send("You already have an active typing race! Finish it first.")
            return
        
        game = TypeRaceGame()
        self.bot.active_typerace[ctx.author.id] = game
        game.start()
        
        await ctx.send(f"⌨️ **Type Race Started!**\n"
                       f"Type this sentence as fast and accurately as you can:\n\n"
                       f"```{game.sentence}```\n"
                       f"Type it exactly as shown!")
    
    @commands.command()
    async def quittyperace(self, ctx):
        """Quit your current type race"""
        if ctx.author.id not in self.bot.active_typerace:
            await ctx.send("You don't have an active type race!")
            return
        
        del self.bot.active_typerace[ctx.author.id]
        await ctx.send("⌨️ Type race ended.")


async def setup(bot):
    await bot.add_cog(WordGames(bot))
