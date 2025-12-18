"""
Admin Cog

Commands for bot management and hot-reloading (Owner only):
- load: Load a specific cog
- unload: Unload a specific cog (cannot unload admin itself)
- reload: Reload a specific cog
- reloadall: Reload all cogs (shows success/failure for each)
- cogs: List all currently loaded cogs

All commands require bot owner permissions.
"""

import discord
from discord.ext import commands


class Admin(commands.Cog):
    """Admin commands for managing cogs and bot operations"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Admin cog loaded")
    
    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        """Load a cog"""
        try:
            await self.bot.load_extension(f'cogs.{cog}')
            await ctx.send(f"✅ Loaded cog: **{cog}**")
        except Exception as e:
            await ctx.send(f"❌ Failed to load **{cog}**: {e}")
    
    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        """Unload a cog"""
        if cog.lower() == 'admin':
            await ctx.send("❌ Cannot unload the admin cog!")
            return
        
        try:
            await self.bot.unload_extension(f'cogs.{cog}')
            await ctx.send(f"✅ Unloaded cog: **{cog}**")
        except Exception as e:
            await ctx.send(f"❌ Failed to unload **{cog}**: {e}")
    
    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        """Reload a cog (hot reload)"""
        try:
            await self.bot.reload_extension(f'cogs.{cog}')
            await ctx.send(f"🔄 Reloaded cog: **{cog}**")
        except Exception as e:
            await ctx.send(f"❌ Failed to reload **{cog}**: {e}")
    
    @commands.command()
    @commands.is_owner()
    async def reloadall(self, ctx):
        """Reload all cogs"""
        success = []
        failed = []
        
        for extension in list(self.bot.extensions.keys()):
            cog_name = extension.split('.')[-1]
            try:
                await self.bot.reload_extension(extension)
                success.append(cog_name)
            except Exception as e:
                failed.append(f"{cog_name}: {e}")
        
        msg = "🔄 **Reload Complete**\n"
        if success:
            msg += f"✅ Success: {', '.join(success)}\n"
        if failed:
            msg += f"❌ Failed:\n" + "\n".join(failed)
        
        await ctx.send(msg)
    
    @commands.command()
    async def cogs(self, ctx):
        """List all loaded cogs"""
        loaded = [ext.split('.')[-1] for ext in self.bot.extensions.keys()]
        
        embed = discord.Embed(
            title="📦 Loaded Cogs",
            description="\n".join(f"• {cog}" for cog in sorted(loaded)),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Total: {len(loaded)} cogs")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))
