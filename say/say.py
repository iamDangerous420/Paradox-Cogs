import time
import discord
from discord.ext import commands
from .utils.chat_formatting import *
from random import randint
from random import choice as randchoice
import asyncio
from cogs.utils import checks
from cogs.utils.chat_formatting import box
from cogs.utils.chat_formatting import pagify
from random import choice
import datetime
import logging
import os

log = logging.getLogger("red.admin")

class say:
    """shitty ass say command made in 3 mins"""
    def __init__(self, bot):
        self.bot = bot
    @commands.command(pass_context=True)
    async def say(self, ctx, *, content):
        """Repeats your message"""
        channel = ctx.message.channel
        name = ctx.message.author.name
        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        em = discord.Embed(description=content, colour=discord.Colour(value=colour))
        await self.bot.send_message(channel, embed=em)
    @commands.command(pass_context=True)
    async def whisper(self, ctx, user : discord.Member, text):
        """Whisper to someone using the bot
        Same as dming But you use the bot !"""

        author = ctx.message.author
        channel = ctx.message.channel

        try:
            await self.bot.delete_message(ctx.message)
        except:
            raise Exception("Bruh i don't have delete messages perms delete your messaqe")

        prefix = "Ayoo Matey you Getting a Message from {} ({})".format(
            author.name, author.id)
        payload = "{}\n\n{}".format(prefix, text)

        try:
            for page in pagify(payload, delims=[" ", "\n"], shorten_by=10):
                await self.bot.send_message(user, box(page))
        except discord.errors.Forbidden:
            log.debug("I CAN'T FUCKING SEND MSGS TO {} FFS DID HE BLOCK Me ! Or maybe he just has that teng where randoms can't msg :thinking: o well ¯\_(ツ)_/¯".format(user))
        except (discord.errors.NotFound, discord.errors.InvalidArgument):
            log.debug("{} *404* Dis bitch not found~".format(user))
        else:
            reply = await self.bot.say("Whisper Mcfucking *** Delivered***  https://goo.gl/3qCxR4 ")
            await asyncio.sleep(5)
            await self.bot.delete_message(reply)
    @commands.command(pass_context=True, aliases=["esay"])
    async def embed(self, ctx, *, content):
        """Embed text"""
        channel = ctx.message.channel
        name = ctx.message.author.name
        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        em = discord.Embed(description=content, colour=discord.Colour(value=colour), timestamp=__import__('datetime').datetime.utcnow())
        avatar = self.bot.user.avatar_url if self.bot.user.avatar else self.bot.user.default_avatar_url
        em.set_author(name='{}'.format(name), icon_url=ctx.message.author.avatar_url)
        await self.bot.send_message(channel, embed=em)
    @checks.mod_or_permissions(manage_messages=True)
    @commands.command(pass_context = True)
    async def monkeysee(self, ctx):
        """Bot repeats :P"""
        channel = ctx.message.channel
        author = ctx.message.author
        await self.bot.send_message(channel, "***OOH OHH AH AH Monkey See*** Monkey **Do**\nType `exit` to quit")
        while True:
            torepeat = await self.bot.wait_for_message(author=author, channel=channel, timeout = None)
            await self.bot.send_message(channel, torepeat.content)
            if torepeat.content == "exit":
                break


    @commands.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def gsay(self, ctx, *, text):
        """ Ghost say ==> Says Something as the bot without the needs special rights And no o ne gets to know who said it unless you have a handy logging bot """

        try:
            await self.bot.delete_message(ctx.message)
        except:
            raise Exception("I do not have the permissions needed")

        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)

        data = discord.Embed(description="", colour=discord.Colour(value=colour))
        data.add_field(name=str(text), value=u"\u2063")

        try:
            await self.bot.say(embed=data)
        except:
            await self.bot.say("I need the `Embed links` permission "
                               "to send this")



def setup(bot):
    n = say(bot)
    bot.add_cog(n)
