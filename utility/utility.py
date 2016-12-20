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
        message = ctx.message
        channel = ctx.message.channel
        await self.bot.send_typing(ctx.message.channel)
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
        channel = ctx.message.channel
        await self.bot.send_typing(ctx.message.channel)

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
    @commands.command(pass_context=True)
    async def membercount(self, ctx):
        """member number count."""
        server = ctx.message.server
        channel = ctx.message.channel
        colour = ''.join([random.choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        await self.bot.send_typing(ctx.message.channel)
        msg = discord.Embed(description=":raised_hand:***Collecting Stats*** :raised_hand:",
        colour=discord.Colour(value=colour))
        lolol = await self.bot.say(embed=msg)
        data = discord.Embed(
            description="***{}'s***  **Member Stats**".format(server.name),
            colour=discord.Colour(value=colour), timestamp=__import__('datetime').datetime.utcnow())
        data.add_field(name="**<:vpOnline:212789758110334977>Online Users**", value="***{}***".format(len([e.name for e in server.members if e.status == discord.Status.online])))
        data.add_field(name="**<:vpAway:212789859071426561>Idle Users**", value="***{}***".format(len([e.name for e in server.members if e.status == discord.Status.idle])))
        data.add_field(name="**<:vpDnD:236744731088912384>Dnd Users**", value="***{}***".format(len([e.name for e in server.members if e.status == discord.Status.dnd])))
        data.add_field(name="**<:vpOffline:212790005943369728>Offline Users**", value="***{}***".format(len([e.name for e in server.members if e.status == discord.Status.offline])))
        data.add_field(name="**👤 Total Humans**", value="***{}***".format(len([e.name for e in server.members if not e.bot])))
        data.add_field(name="**🤖Total Bots**", value="***{}***".format(len([e.name for e in server.members if e.bot])))
        data.add_field(name="**👤🤖Total Bots & Humans🤖👤**", value="***{}***".format(len([e.name for e in server.members])))
        data.set_footer(text="Count as of =>")
        if server.icon_url:
            data.set_author(name="", url=server.icon_url)
            data.set_thumbnail(url=server.icon_url)
        else:
            data.set_author(name="")
        await self.bot.edit_message(lolol, embed=data)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def bstats(self, ctx):
        """Stats for Danger's servers"""
        server = ctx.message.server
        channel = ctx.message.channel
        colour = ''.join([random.choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        msg = discord.Embed(description=":raised_hand:***Collecting Stats*** :raised_hand:",
        colour=discord.Colour(value=colour))
        await self.bot.send_typing(ctx.message.channel)
        fuckmyass699696 = await self.bot.say(embed=msg)
        await asyncio.sleep(0.7)
        data = discord.Embed(
            description=self.bot.user.name+"'s User Statistics",
            colour=discord.Colour(value=colour), timestamp=__import__('datetime').datetime.utcnow())
        data.add_field(name="**<:vpOnline:212789758110334977>Online Users**", value=(len([e.name for e in self.bot.get_all_members() if e.status == discord.Status.online])))
        data.add_field(name="**<:vpAway:212789859071426561>Idle Users**", value=(len([e.name for e in self.bot.get_all_members() if e.status == discord.Status.idle])))
        data.add_field(name="**<:vpDnD:236744731088912384>Dnd Users**", value=(len([e.name for e in self.bot.get_all_members() if e.status == discord.Status.dnd])))
        data.add_field(name="**<:vpOffline:212790005943369728>Offline Users**", value=(len([e.name for e in self.bot.get_all_members() if e.status == discord.Status.offline])))
        data.add_field(name="**Total Humans**", value=(len([e.name for e in self.bot.get_all_members() if not e.bot])))
        data.add_field(name="**Total Bots**", value=(len([e.name for e in self.bot.get_all_members() if e.bot])))
        data.set_footer(text=" I count {} Total Bots & Humans From {} servers as of ".format(len([e.name for e in self.bot.get_all_members()]), len(self.bot.servers)))
        await self.bot.edit_message(fuckmyass699696, embed=data)

        if server.icon_url:
            data.set_author(name="", url=self.bot.user.avatar_url)
            data.set_thumbnail(url=self.bot.user.avatar_url)
        else:
            data.set_author(name="")
        await self.bot.edit_message(fuckmyass699696, embed=data)

    @commands.command(pass_context=True)
    async def bots(self, ctx):
        """Lists teh bots"""
        channel = ctx.message.channel
        await self.bot.send_typing(ctx.message.channel)

        list = "\n".join([m.name for m in ctx.message.server.members if m.bot])
        for page in pagify(list, ["\n"], shorten_by=7, page_length=2000):
            await self.bot.say(box(page))

    @commands.command(pass_context=True)
    async def roles(self, ctx):
        """States roles from highest to lowest"""

        list = "\n".join([x.name for x in ctx.message.server.role_hierarchy if x.name != "@everyone"])
        for page in pagify(list, ["\n"], shorten_by=7, page_length=2000):
            await self.bot.say(box(page))

def setup(bot):
    n = Utility(bot)
    bot.add_cog(n)