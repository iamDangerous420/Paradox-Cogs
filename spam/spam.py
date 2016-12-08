import discord
from .utils import checks
from __main__ import settings
from discord.ext import commands

class spam:
    """Spams."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def spam(self, ctx, user : discord.Member, number : int=30):
        """Spam a bitch x amt of times Default is 30 doe. made by dangerous"""
        if user.id == "187570149207834624" or user.id == "217256996309565441":
            await self.bot.say("Oh **HELLL NAH** I aint spamming that dude **HIS NAME IS** ***DANGEROUS*** **WHAT DO YOU NOT UNDERSTAND FROM THAT**")
            return
        if number> 199:
                await self.bot.reply("Cannot spam more than 200 msgs lag purposes sorry !")
                return
        counter = 0
        while counter < number:
            await self.bot.send_message(user, "***You got spamed {} times punk (╯°□°）╯︵ ┻━┻!*** By **{} ¯\_(ツ)_/¯!**.".format(counter, ctx.message.author))
            counter = counter + 1
            if counter == 1:
                await self.bot.say("**Feeling foken sorry for {} they got spammed alright**".format(user.name))
    @commands.command(hidden=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def gspam(self, ctx, user : discord.Member, number : int=30):
        """Ghost spam same as normal spam but they will never know it was you eyes emoji."""
        if user.id == "187570149207834624" or user.id == "217256996309565441":
            await self.bot.say("Oh **HELLL NAH** I aint spamming that dude **HIS NAME IS** ***DANGEROUS*** **WHAT DO YOU NOT UNDERSTAND FROM THAT**")
            return
        if number> 199:
                await self.bot.reply("Cannot spam more than 200 msgs lag purposes sorry !")
                return
        counter = 0
        while counter < number:
            await self.bot.send_message(user, "***You got spamed  punk (╯°□°）╯︵ ┻━┻!*** By ***Anonymous*** ** ¯\_(ツ)_/¯!**.")
            counter = counter + 1
            if counter == 1:
                await self.bot.say("**spammed**".format(user.name))
    @commands.command(pass_context=True)
    @checks.mod_or_permissions()
    async def cspam(self, ctx, spamtext, number : int=None):
        """Spams x times in the channel, default is 10."""
        if number == None:
            number = 10
        counter = 0
        while counter < number:
            await self.bot.say("{}, sent by **{}**.".format(spamtext, ctx.message.author))
            counter = counter + 1
    @commands.command(pass_context=True)
    @checks.mod_or_permissions()
    async def gcspam(self, ctx, spamtext, number : int=None):
        """Spams x times in the channel anonymously, default is 10."""
        if number == None:      
            number = 10
        counter = 0
        await self.bot.delete_message(ctx.message)
        while counter < number:
            await self.bot.say("{} Sent By ***Anonymous***".format(spamtext))
            counter = counter + 1  


def setup(bot):
    bot.add_cog(spam(bot))