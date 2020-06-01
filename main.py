import discord
import os
from discord.ext import commands

bot = commands.Bot(command_prefix = '.')

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == int('YOUR ID HERE')
    return commands.check(predicate)

class Meta(commands.Cog):
    """Owner commands only."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @commands.command()
    @is_owner()
    async def load(self, ctx, extension):
        """loads cog."""
        bot.load_extension(f'cogs.{extension}')

    @commands.command()
    @is_owner()
    async def unload(self, ctx, extension):
        """unloads cog."""
        bot.unload_extension(f'cogs.{extension}')

    @commands.command()
    @is_owner()
    async def reload(self, ctx, extension):
        """reloads cog."""
        bot.reload_extension(f'cogs.{extension}')

    @commands.command()
    @is_owner()
    async def reload_all(self, ctx):
        """reloads every cog."""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                bot.reload_extension(f'cogs.{filename[:-3]}')

    @commands.command()
    @is_owner()
    async def quit(self, ctx):
        """closes bot."""
        print("closing")
        await bot.logout()

bot.add_cog(Meta(bot))

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run('YOUR TOKEN HERE')