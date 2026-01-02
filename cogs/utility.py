"""
Utility Cog

Utility and informational commands:
- ping: Test bot responsiveness
- commands: List all available commands
- purge: Delete messages from channel (moderation)
- translate: Translate text to another language
- serverinfo: Display server statistics
- userinfo: Display user profile information
- avatar: Display user's avatar in full size
- fakeping: Fake ping someone (deletes instantly)
- chaos: Randomly move users between voice channels
- mock: Transform text into mocking SpongeBob case

Requires permissions: Manage Messages (purge), Move Members (chaos)
"""

import discord
from discord.ext import commands
import asyncio
import random
import aiohttp


class Utility(commands.Cog):
    """Server utilities, information commands, and fun tools"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Utility cog loaded")
    
    @commands.command()
    async def ping(self, ctx):
        """ Simple test command that responds with "Pong!" """
        await ctx.send("Pong!")
    
    @commands.command(name='commands')
    async def commands_list(self, ctx):
        """ Display all available commands """
        commands_text = """
**🤖 Bugg Bot Commands**

**Utility:** 
`!ping` `!commands` `!purge [amount]` `!translate <lang> <text>`
`!serverinfo` `!userinfo [@user]` `!avatar [@user]` `!fakeping @user`

**Monitoring:**
`!metrics` `!lasterror` `!health` `!shardinfo` `!ratelimit` `!market <item>`

**Games:**
`!coinflip` `!roll [dice]` `!8ball <question>` `!random [args]`
`!slots` `!roulette` `!duel @user` `!mock [text]`

**Board Games:**
`!blackjack` `!deathroll` `!tictactoe @user` `!connect4 @user`

**Word Games:**
`!hangman [category]` `!wordle` `!akinator` `!typerace`

**Pokémon:**
`!battle [difficulty]` `!challenge @user` `!attack [move]` `!flee`

**Math & Art:**
`!plot <formula>` `!fractal` `!julia [c_real] [c_imag]` `!cube` `!war`

**APIs:**
`!weather <city>` `!space [date]` `!trivia`

**Timers:**
`!remindme <time> <task>` `!pomodoro [minutes]` `!stop`

**Artifact:**
`!artifact_status` `!touch` `!disturb`

**Admin (Owner Only):**
`!load <cog>` `!unload <cog>` `!reload <cog>` `!reloadall` `!cogs`
"""
        await ctx.send(commands_text)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 5):
        """ Delete a specified number of messages from the channel """
        # Delete 'amount' messages plus the command message itself
        await ctx.channel.purge(limit=amount + 1)
        
        # Send a confirmation that deletes itself after 3 seconds so it doesn't clutter chat
        await ctx.send(f"🧹 Cleared {amount} messages.", delete_after=3)
    
    @commands.command()
    async def translate(self, ctx, target_lang: str, *, text: str):
        """ Translate text to another language (e.g., !translate es Hello world) """
        try:
            # Use Google Translate API via googletrans library
            # Language codes: en (English), es (Spanish), fr (French), de (German), ja (Japanese), etc.
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",  # Auto-detect source language
                "tl": target_lang,
                "dt": "t",
                "q": text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract translated text from nested response
                        translated = ""
                        for sentence in data[0]:
                            if sentence[0]:
                                translated += sentence[0]
                        
                        # Create embed for clean display
                        embed = discord.Embed(title="🌐 Translation", color=discord.Color.blue())
                        embed.add_field(name="Original", value=text, inline=False)
                        embed.add_field(name=f"Translated ({target_lang})", value=translated, inline=False)
                        embed.set_footer(text="Common codes: en, es, fr, de, ja, ko, zh-CN, pt, ru, ar, hi")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"❌ Translation failed! Make sure the language code is valid.\n"
                                      f"Examples: `en` (English), `es` (Spanish), `fr` (French), `de` (German)")
        except Exception as e:
            await ctx.send(f"❌ Translation error: {e}\nExample usage: `!translate es Hello world`")
    
    @commands.command()
    async def serverinfo(self, ctx):
        """ Display server statistics and information """
        guild = ctx.guild
        
        embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blue())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic stats
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="👥 Members", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        
        # Channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        embed.add_field(name="💬 Text Channels", value=text_channels, inline=True)
        embed.add_field(name="🔊 Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        
        # Boost info
        embed.add_field(name="✨ Boost Level", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="💎 Boosts", value=guild.premium_subscription_count or 0, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """ Display user profile information """
        member = member or ctx.author
        
        embed = discord.Embed(title=f"👤 {member.display_name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Basic info
        embed.add_field(name="Username", value=f"{member.name}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        if member.joined_at:
            embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y"), inline=True)
        
        # Roles (excluding @everyone)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        if roles:
            embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        """ Display user's avatar in full size """
        member = member or ctx.author
        
        embed = discord.Embed(title=f"🖼️ {member.display_name}'s Avatar", color=member.color)
        embed.set_image(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def fakeping(self, ctx, member: discord.Member):
        """ Fake ping someone (mentions them but deletes instantly) """
        msg = await ctx.send(f"{member.mention}")
        await asyncio.sleep(0.5)
        await msg.delete()
        await ctx.message.delete()
    
    @commands.command()
    @commands.has_permissions(move_members=True)
    async def chaos(self, ctx):
        """ Move users randomly between voice channels """
        # Check if user is in a voice channel
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to use this command!")
            return
        
        # Get the voice channel the user is in
        source_channel = ctx.author.voice.channel
        
        # Get all voice channels in the server
        voice_channels = ctx.guild.voice_channels
        
        if len(voice_channels) < 2:
            await ctx.send("Need at least 2 voice channels to create chaos!")
            return
        
        # Get all members in the source channel, excluding those who are streaming
        members_to_move = [member for member in source_channel.members 
                           if not member.voice.self_stream and not member.voice.self_video]
        
        # Count how many were skipped
        streaming_count = len(source_channel.members) - len(members_to_move)
        
        if len(members_to_move) == 0:
            if streaming_count > 0:
                await ctx.send("No one to move! (All members are streaming/sharing video)")
            else:
                await ctx.send("No one to move!")
            return
        
        moved_count = 0
        try:
            # Move each member to a random voice channel
            for member in members_to_move:
                # Pick a random channel (could be the same one)
                target_channel = random.choice(voice_channels)
                try:
                    await member.move_to(target_channel)
                    moved_count += 1
                except discord.Forbidden:
                    await ctx.send("❌ I don't have permission to move members! Grant me 'Move Members' permission.")
                    return
                except:
                    pass  # Skip if member can't be moved
            
            # Send success message
            result_msg = f"🌪️ **CHAOS!** Moved {moved_count} member(s) randomly!"
            if streaming_count > 0:
                result_msg += f"\n(Skipped {streaming_count} streaming/video member(s))"
            await ctx.send(result_msg)
        
        except Exception as e:
            await ctx.send(f"❌ Error creating chaos: {e}")
    
    @commands.command()
    async def mock(self, ctx, *, text: str = None):
        """ Transform text into mocking SpongeBob case """
        # Check if they are replying to a message
        if ctx.message.reference:
            # Fetch the message they replied to
            original_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            text = original_msg.content
        
        # If no text provided and no reply
        if not text:
            await ctx.send("Provide text or reply to a message!")
            return

        # The transformation logic - alternate between lowercase and uppercase
        result = ""
        for i, char in enumerate(text):
            # If index is even, lowercase. If odd, uppercase.
            if i % 2 == 0:
                result += char.lower()
            else:
                result += char.upper()

        # Send it and delete the original command for seamlessness
        await ctx.message.delete()
        await ctx.send(f"🥴 {result} 🥴")


async def setup(bot):
    await bot.add_cog(Utility(bot))
