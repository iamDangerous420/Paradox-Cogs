import discord
from .utils import checks
from __main__ import settings
from discord.ext import commands
from discord.errors import DiscordException

class spam:
    """Spams."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def spam(self, ctx, user : discord.Member, number : int=30):
        """Spam a bitch x amt of times Default is 30 doe. made by dangerous"""
		if user.id == "187570149207834624" or user.id == "217256996309565441":
           await self.bot.say("Oh **HELLL NAH** I aint spamming that dude **HIS NAME IS** ***DANGEROUS*** **WHAT DO YOU NOT UNDERSTAND FROM THAT**")
            return
        if number> 499:
                await self.bot.reply("Cannot spam more than 490 msgs")
                return
        counter = 0
        while counter < number:
            await self.bot.send_message(user, "***You got spamed punk (╯°□°）╯︵ ┻━┻!*** By **{} ¯\_(ツ)_/¯!**.".format(counter, ctx.message.author))
            counter = counter + 1
        await self.bot.say("**Feeling foken sorry for {} they got spammed alright**".format(user.name))
    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def gspam(self, ctx, user : discord.Member, spamtext, number : int=30):
        """Ghost spam same as normal spam but they will never know it was you eyes emoji. default 30"""
       if user.id == "187570149207834624" or user.id == "217256996309565441":
           await self.bot.say("Oh **HELLL NAH** I aint spamming that dude **HIS NAME IS** ***DANGEROUS*** **WHAT DO YOU NOT UNDERSTAND FROM THAT**")
            return
        if number> 499:
                await self.bot.reply("Cannot spam more than 490 msgs")
                return
        counter = 0
        while counter < number:
            await self.bot.delete_message(ctx.message)
            await self.bot.send_message(user, "***You got spamed (╯°□°）╯︵ ┻━┻! ***MESSAGE IS:*** ***```{}```*** *** By ***Anonymous*** ** ¯\_(ツ)_/¯!**.\n".format(spamtext))
            counter = counter + 1
        await self.bot.say("**spammed {}**".format(user.name))
    @commands.command(pass_context=True)
    @checks.mod_or_permissions()
    async def cspam(self, ctx, spamtext, number : int=10):
        """Spams the channel, default =10."""
        user = ctx.message.author
        counter = 0
        while counter < number:
            await self.bot.say("{}, sent by **{}**.".format(spamtext, user.name))
            counter = counter + 1
    @commands.command(pass_context=True)
    @checks.mod_or_permissions()
    async def gcspam(self, ctx, spamtext, number : int=10):
        """Spams x times in the channel anonymously, default is 10."""

        counter = 0
        while counter < number:
            await self.bot.delete_message(ctx.message)
            counter = counter + 1
        await self.bot.say("{} Sent By ***Anonymous***".format(spamtext))

def setup(bot):
    bot.add_cog(spam(bot))