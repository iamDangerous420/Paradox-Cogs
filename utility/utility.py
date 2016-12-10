import discord
from discord.ext import commands
from .utils.chat_formatting import *
import random
from random import randint
from random import choice as randchoice
import datetime
from __main__ import send_cmd_help
import re
import urllib
import time
import aiohttp
import asyncio
from cogs.utils.dataIO import dataIO
import io, os
import logging
from __main__ import send_cmd_help, user_allowed
from cogs.utils import checks
from cogs.utils.dataIO import dataIO
from cogs.utils.chat_formatting import box, pagify, escape_mass_mentions
from random import choice
from copy import deepcopy
from cogs.utils.settings import Settings

log = logging.getLogger("red.admin")

class Utility:
    """Utility commands."""

    def __init__(self, bot):
        self.bot = bot

    def _role_from_string(self, server, rolename, roles=None):
        if roles is None:
            roles = server.roles
        role = discord.utils.find(lambda r: r.name.lower() == rolename.lower(),
                                  roles)
        try:
            log.debug("Role {} found from rolename {}".format(
                role.name, rolename))
        except:
            log.debug("Role not found for rolename {}".format(rolename))
        return role

    @commands.command(pass_context=True)
    async def inrole(self, ctx, *, rolename):
        """Check members in the role totally didn't copy dex's eye emoji"""
        server = ctx.message.server
        check = " ".join(rolename).lower()
        if "@everyone" in check or "@here" in check:
            await self.bot.reply("Well At least you tried but i have counter messures against that ¯\_(ツ)_/¯")
            return
        therole = discord.utils.find(lambda r: r.name.lower() == rolename.lower(), ctx.message.server.roles)
        if therole is not None and len([m for m in server.members if therole in m.roles]) < 50:
            lolies = await self.bot.say(" :raised_hand: Wait up Getting Names :bookmark: ")
            await asyncio.sleep(1) #taking time to retrieve the names
            server = ctx.message.server
            member = " :bookmark_tabs:  ***{1}*** Members found in the ***{0}*** Role, :bookmark_tabs: \n".format(rolename, len([m for m in server.members if therole in m.roles]))
            member += "```diff\n+"
            member += " \n+".join(m.display_name for m in server.members if therole in m.roles)
            member += "```"
            await self.bot.edit_message(lolies, member)
        elif len([m for m in server.members if therole in m.roles]) > 50:
            awaiter = await self.bot.say("Getting Member Names")
            await asyncio.sleep(1)
            await self.bot.edit_message(awaiter, " :raised_hand: Woah way too many people in **{0}** Role, **{1}** Members found\n".format(rolename,  len([m for m in server.members if therole in m.roles])))
        else:
            await self.bot.say("`` Couldn't Find that role (╯°□°）╯︵ ┻━┻``")

    @commands.command(pass_context=True)
    async def uid(self, ctx, user : discord.Member = None):
        """get your user id"""
        if user is None:
            user = ctx.message.author
        await self.bot.say(':id: of **{}** ==> ***__{}__***'.format(user.name, user.id))
    @commands.command(pass_context=True)
    async def sid(self, ctx,):
        """get your server id"""
        server = ctx.message.server
        await self.bot.say(':regional_indicator_s: :regional_indicator_e: :regional_indicator_v: :regional_indicator_e: :regional_indicator_r: :id: of **{}** ==> ***__{}__***'.format(server.name, server.id))
    @commands.command(pass_context=True)
    async def cid(self, ctx, *, channel : discord.Channel=None):
        """get your channel id"""
        author = ctx.message.channel
        server = ctx.message.server
        if not channel:
            channel = author
        await self.bot.say(':regional_indicator_c: :id: of **{}** ==> ***__{}__***'.format(channel.name, channel.id))
    @commands.command(pass_context=True)
    async def rid(self, ctx, rolename):
        """get your role id"""
        channel = ctx.message.channel
        server = ctx.message.server

        role = self._role_from_string(server, rolename)

        if role is None:
            await self.bot.say('That role cannot be found.')
            return

        await self.bot.say(':regional_indicator_r: :regional_indicator_o: :regional_indicator_l: :regional_indicator_e:  :id:  of **{}** ==> ***__{}__***'.format(rolename, role.id))
    @commands.command(pass_context=True)
    async def elist(self, ctx):
        """ServerEmote List"""
        server = ctx.message.server
        
        list = [e for e in server.emojis if not e.managed]
        emoji = ''
        for emote in list:
            emoji += "<:{0.name}:{0.id}> ".format(emote)
        try:
            await self.bot.say(emoji)
        except:
            await self.bot.say("**This server has no facking emotes what is this a ghost town ???**")
def setup(bot):
    n = Utility(bot)
    bot.add_cog(n)