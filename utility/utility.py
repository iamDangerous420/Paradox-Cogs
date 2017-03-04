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
import operator
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
    @checks.serverowner_or_permissions(administrator=True)
    async def serverprefix(self, ctx, *prefixes):
        """Sets Dmx's prefixes for this server

        Accepts multiple prefixes separated by a space. Enclose in double
        quotes if a prefix contains spaces.
        Example: set serverprefix ! $ ? "two words"

        Issuing this command with no parameters will reset the server
        prefixes and the global ones will be used instead."""
        server = ctx.message.server

        if prefixes == ():
            self.bot.settings.set_server_prefixes(server, [])
            current_p = ", ".join(self.bot.settings.prefixes)
            await self.bot.say("**Server prefixes reset. Current prefixes:** "
                               "`{}`".format(current_p))
            return

        prefixes = sorted(prefixes, reverse=True)
        self.bot.settings.set_server_prefixes(server, prefixes)
        log.debug("Setting server's {} prefixes to:\n\t{}"
                  "".format(server.id, self.bot.settings.prefixes))

        await self.bot.say("**I set the prefixes to** :`{}`  **for this server.\n"
                           "To go back to the global prefixes, do**"
                           " `{}set serverprefix` ".format(prefixes, prefixes[0]))

    @commands.command(pass_context=True, no_pm=True, aliases=["nick","setnick","setnickname"])
    @checks.admin_or_permissions(manage_nicknames=True)
    async def nickname(self, ctx, *, nickname=""):
        """Sets dmx's nickname (serverwise)

        Leaving this empty will remove it."""
        nickname = nickname.strip()
        if nickname == "":
            await self.bot.change_nickname(ctx.message.server.me, self.bot.user.name)
            await self.bot.say(":thumbsup: Nickname **reverted** to ***`{}`***  :white_check_mark: ".format(self.bot.user.name))
            return
        try:
            await self.bot.change_nickname(ctx.message.server.me, nickname)
            await self.bot.say(":thumbsup: Nickname changed to ***`{}`***  :white_check_mark: \n:bangbang:Please Note this change is only Serverwise and the bots default name is ***{}***".format(nickname, self.bot.user.name))
        except discord.Forbidden:
            await self.bot.say(":x:***I cannot do that, I lack the "
                "\"Change Nickname\" permission.***:no_good:")

    @commands.command(pass_context=True,aliases=["ir","role","in"])
    async def inrole(self, ctx, *, rolename):
        """Check members in the role"""
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
            await self.bot.say(':no_good: That role cannot be found. :no_good:')
            return

        await self.bot.say(':regional_indicator_r: :regional_indicator_o: :regional_indicator_l: :regional_indicator_e:  :id:  of **{}** ==> ***__{}__***'.format(rolename, role.id))
    @commands.command(pass_context=True, aliases=["emotes","serveremotes","emotelist"])
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

    @commands.command(pass_context=True, aliases=["ri"])
    async def roleinfo(self, ctx, rolename):
        """Get your role info !!!
        If dis dun work first trry use "" quotes on te role"""
        channel = ctx.message.channel
        server = ctx.message.server
        colour = ''.join([random.choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        await self.bot.send_typing(ctx.message.channel)
        therole = discord.utils.find(lambda r: r.name.lower() == rolename.lower(), ctx.message.server.roles)
        since_created = (ctx.message.timestamp - therole.created_at).days
        created_on = "{} days ago".format(since_created)
        if therole is None:
            await bot.say(':no_good: That role cannot be found. :no_good:')
            return
        if therole is not None:
            perms = iter(therole.permissions)
            perms_we_have = ""
            perms_we_dont = ""
            for x in perms:
                if "True" in str(x):
                    perms_we_have += "<:vpGreenTick:257437292820561920> {0}\n".format(str(x).split('\'')[1])
                else:
                    perms_we_dont += ("<:vpRedTick:257437215615877129> {0}\n".format(str(x).split('\'')[1]))
            msg = discord.Embed(description=":raised_hand:***`Collecting Role Stats`*** :raised_hand:",
            colour=therole.color)
            if therole.color is None:
                therole.color = discord.Colour(value=colour)
            lolol = await self.bot.say(embed=msg)
            em = discord.Embed(
                description="***`{}'s`***  ***Role Stats***".format(therole.name),
                colour=therole.colour,)
            em.add_field(name="UsersinRole", value=len([m for m in server.members if therole in m.roles]))
            em.add_field(name="Id", value=therole.id)
            em.add_field(name="Color", value=therole.color)
            em.add_field(name="Position", value=therole.position)
            em.add_field(name="Valid Perms", value="{}".format(perms_we_have))
            em.add_field(name="Invalid Perms", value="{}".format(perms_we_dont))
            em.set_thumbnail(url="https://cdn.discordapp.com/attachments/269292528719626240/276485689887948800/unknown.png")
            em.set_footer(text="{} Was created {}".format(therole.name, created_on), icon_url = self.bot.user.avatar_url)
        try:    
            await self.bot.edit_message(lolol, embed=em)
        except discord.HTTPException:
            permss = "```diff\n"
            therole = discord.utils.find(lambda r: r.name.lower() == rolename.lower(), ctx.message.server.roles)
            if therole is None:
                await bot.say(':no_good: That role cannot be found. :no_good:')
                return
            if therole is not None:
                perms = iter(therole.permissions)
                perms_we_have2 = ""
                perms_we_dont2 = ""
                for x in perms:
                    if "True" in str(x):
                        perms_we_have2 += "+{0}\n".format(str(x).split('\'')[1])
                    else:
                        perms_we_dont2 += ("-{0}\n".format(str(x).split('\'')[1]))
            await self.bot.say("{}{}'s Role Stats,\nUsersinRole : {}\nId : {}\nColor : {}\nPosition : {}\nValid Perms : \n{}\nInvalid Perms : \n{}\n{} Was created {}```".format(permss, therole.name, len([m for m in server.members if therole in m.roles]), therole.id, therole.color, therole.position, perms_we_have2, perms_we_dont2,therole.name, created_on))
            await self.bot.delete_message(lolol)

    @commands.command(pass_context=True, aliases=["mcount"])
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
        data.add_field(name=":busts_in_silhouette: **Total Humans**:busts_in_silhouette: ", value=(len([e.name for e in self.bot.get_all_members() if not e.bot])))
        data.add_field(name=":robot: **Total Bots**:robot: ", value=(len([e.name for e in self.bot.get_all_members() if e.bot])))
        data.set_footer(text=" I count {} Total Bots🤖 & Humans 👥 From {} servers as of ".format(len([e.name for e in self.bot.get_all_members()]), len(self.bot.servers)))
        await self.bot.edit_message(fuckmyass699696, embed=data)

        if server.icon_url:
            data.set_author(name="", url=self.bot.user.avatar_url)
            data.set_thumbnail(url=self.bot.user.avatar_url)
        else:
            data.set_author(name="")
        await self.bot.edit_message(fuckmyass699696, embed=data)

    @commands.command(pass_context=True)
    async def mods(self, ctx):
        """Lists mods Based on manage roles"""
        colour = "".join([random.choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        server = ctx.message.server
        online = [e.name for e in server.members if e.permissions_in(ctx.message.channel).manage_roles and not e.bot and e.status == discord.Status.online]
        away = [e.name for e in server.members if e.permissions_in(ctx.message.channel).manage_roles and not e.bot and e.status == discord.Status.idle]
        dnd = [e.name for e in server.members if e.permissions_in(ctx.message.channel).manage_roles and not e.bot and e.status == discord.Status.dnd]
        offline = [e.name for e in server.members if e.permissions_in(ctx.message.channel).manage_roles and not e.bot and e.status == discord.Status.offline]
        stream = [e.name for e in server.members if e.permissions_in(ctx.message.channel).manage_roles and not e.bot and e.game is not None and e.game.url is True]
        em = discord.Embed(description="Listing mods for "+server.name, colour=discord.Colour(value=colour), timestamp=__import__('datetime').datetime.utcnow())
        if online:
            em.add_field(name="<:vpOnline:212789758110334977>Online Mods", value="<:vpOnline:212789758110334977>{0}".format((" \n<:vpOnline:212789758110334977> ".join(online)).replace("`", "")), inline=False)
        if away:
            em.add_field(name="<:vpAway:212789859071426561> IDLE Mods", value="<:vpAway:212789859071426561>{0}".format((" \n:<:vpAway:212789859071426561>Idle ".join(away)).replace("`", "")), inline=False)
        if dnd:
            em.add_field(name="<:vpDnD:236744731088912384>DND Mods", value="<:vpDnD:236744731088912384>{0}".format((" \n<:vpDnD:236744731088912384> ".join(dnd)).replace("`", "")), inline=False)
        if offline:
            em.add_field(name="<:vpOffline:212790005943369728>Offline/Invisible Mods", value="<:vpOffline:212790005943369728>{0}".format((" \n<:vpOffline:212790005943369728>".join(offline)).replace("`", "")), inline=False)
        if stream:
            em.add_field(name="<:vpStreaming:212789640799846400>Streaming Mods", value="<:vpStreaming:212789640799846400>{0}".format((" \n<:vpStreaming:212789640799846400> ".join(streaming)).replace("`", "")), inline=False)
        if server.icon_url:
            em.set_thumbnail(url=server.icon_url)
        em.set_footer(text="ModList As of ==>")
        await self.bot.say(embed=em)
    @commands.command(pass_context=True)
    async def admins(self, ctx):
        """Lists admins based on administratior perms"""
        colour = "".join([random.choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        server = ctx.message.server
        online = [e.name for e in server.members if e.permissions_in(ctx.message.channel).administrator and not e.bot and e.status == discord.Status.online]
        away = [e.name for e in server.members if e.permissions_in(ctx.message.channel).administrator and not e.bot and e.status == discord.Status.idle]
        dnd = [e.name for e in server.members if e.permissions_in(ctx.message.channel).administrator and not e.bot and e.status == discord.Status.dnd]
        offline = [e.name for e in server.members if e.permissions_in(ctx.message.channel).administrator and not e.bot and e.status == discord.Status.offline]
        stream = [e.name for e in server.members if e.permissions_in(ctx.message.channel).administrator and not e.bot and e.game is not None and e.game.url is True]
        em = discord.Embed(description="Listing admins for "+server.name, colour=discord.Colour(value=colour), timestamp=__import__('datetime').datetime.utcnow())
        if online:
            em.add_field(name="<:vpOnline:212789758110334977>Online Admins", value="<:vpOnline:212789758110334977>{0}".format((" \n<:vpOnline:212789758110334977> ".join(online)).replace("`", "")), inline=False)
        if away:
            em.add_field(name="<:vpAway:212789859071426561> IDLE Admins", value="<:vpAway:212789859071426561>{0}".format((" \n:<:vpAway:212789859071426561>Idle ".join(away)).replace("`", "")), inline=False)
        if dnd:
            em.add_field(name="<:vpDnD:236744731088912384> DND Admins", value="<:vpDnD:236744731088912384>{0}".format((" \n<:vpDnD:236744731088912384> ".join(dnd)).replace("`", "")), inline=False)
        if offline:
            em.add_field(name="<:vpOffline:212790005943369728>Offline/Invisible Admins", value="<:vpOffline:212790005943369728>{0}".format((" \n<:vpOffline:212790005943369728>".join(offline)).replace("`", "")), inline=False)
        if stream:
            em.add_field(name="<:vpStreaming:212789640799846400>Streaming Admins", value="<:vpStreaming:212789640799846400>{0}".format((" \n<:vpStreaming:212789640799846400> ".join(streaming)).replace("`", "")), inline=False)
        if server.icon_url:
            em.set_thumbnail(url=server.icon_url)
        em.set_footer(text="AdminList As of ==>")
        await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def bots(self, ctx):
        """Lists teh bots"""
        channel = ctx.message.channel
        await self.bot.send_typing(ctx.message.channel)

        list = "\n".join([m.name for m in ctx.message.server.members if m.bot])
        for page in pagify(list, ["\n"], shorten_by=7, page_length=2000):
            await self.bot.say(box(page))

    @commands.command(pass_context=True, hidden=True)
    async def roless(self, ctx):
        """States roles from highest to lowest"""
        colour = ''.join([random.choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        list=discord.Embed(description="**Role list for {}.**".format(ctx.message.server.name), colour=discord.Colour(value=colour))
        list.add_field(name="═══════════════  ஜ۩۞۩ஜ  ═══════════════", value="\n ".join([x.name for x in ctx.message.server.role_hierarchy if x.name != "@everyone"]))
        await self.bot.say(embed=list)

    @commands.command(pass_context=True)
    async def roles(self, ctx):
        """States roles from highest to lowest"""

        list = "\n".join([x.name for x in ctx.message.server.role_hierarchy if x.name != "@everyone"])
        for page in pagify(list, ["\n"], shorten_by=7, page_length=2000):
            await self.bot.say(box(page))

    @commands.command(pass_context=True, no_pm=True, aliases=["wp"])
    async def whoplays(self, ctx, *, game):
        """Shows a list of all the people playing a game.
        Ty Stevy(91988142223036416)(Original Idea&Code By him)"""
        if len(game) <= 2:
            await self.bot.say(":x:***At least 3 characters are Required.***:no_good:")
            return

        colour = ''.join([random.choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        user = ctx.message.author
        server = ctx.message.server
        members = server.members

        playing_game = ""
        playing_game2 = []
        for member in members:
            if member != None and member.game != None and member.game.name != None and not member.bot:
                if game.lower() in member.game.name.lower():
                    playing_game += "• {} ({})\n".format(member.name, member.game.name)
                    playing_game2.append(member.name)

        if playing_game == "":
            await self.bot.say(":confused: No one is playing that game.")
        else:
            msg = playing_game
            em = discord.Embed(description=msg, colour=colour)
            em.set_author(name="Current Users Playing {}: \n".format(game))
            if playing_game2 is not [] and len(playing_game2) is not 1:
                em.set_footer(text="{} users Playing {}".format(len(playing_game2), game))
        try:
            await self.bot.say(embed = em)
        except discord.HTTPException:
            if len(game) <= 2:
                await self.bot.say(":x:***At least 3 characters are Required.***:no_good:")
                return

            d = "```diff\n"
            playing_game = ""
            playing_game2 = []
            for member in members:
                    if member != None and member.game != None and member.game.name != None and not member.bot:
                        if game.lower() in member.game.name.lower():
                            playing_game += "+ {} ({})\n".format(member.name, member.game.name)
                            playing_game2.append(member.name)

            if playing_game == "":
                await self.bot.say(":confused: No one is playing that game.")
            else:
                msg = playing_game
                await self.bot.say("{}-                  Current Users Playing {}  : \n\n{}\n-                  {} users Playing {} ```".format(d, game, msg, len(playing_game2), game))
    @commands.command(pass_context=True, no_pm=True, aliases=["mpgames","games"])
    async def cgames(self, ctx):
        """Shows the currently most played games Stevy<3"""
        user = ctx.message.author
        server = ctx.message.server
        members = server.members

        freq_list = {}
        for member in members:
            if member != None and member.game != None and member.game.name != None and not member.bot:
                if member.game.name not in freq_list:
                    freq_list[member.game.name] = 0
                freq_list[member.game.name]+=1
#Code By Stevy(91988142223036416) 
        sorted_list = sorted(freq_list.items(), key=operator.itemgetter(1), reverse = True)    

        if not freq_list:
            await self.bot.say(":bangbang:**What is this place?** ***This Ghostown Named `{}` has `0` people playing anything***".format(server.name))
        else:            
            # create display
            msg = ""
            max_games = min(len(sorted_list), 10)
            for i in range(max_games):
                game, freq = sorted_list[i]
                msg+= "▸ **{}**:  ***__{}__***\n".format(game, freq_list[game])

            em = discord.Embed(description=msg, colour=user.colour)
            em.set_author(name="These are the server's most played games at the moment:")

        try:
            await self.bot.say(embed = em)

        except discord.HTTPException:
            freq_list = {}
            for member in members:
                if member != None and member.game != None and member.game.name != None and not member.bot:
                    if member.game.name not in freq_list:
                        freq_list[member.game.name] = 0
                    freq_list[member.game.name]+=1

            sorted_list = sorted(freq_list.items(), key=operator.itemgetter(1), reverse = True)    

            if not freq_list:
                await self.bot.say(":bangbang:**What is this place?** ***This Ghostown Named `{}` has `0` people playing anything***".format(server.name))
            else:            
                msg = ""
                d = "```diff\n"
                max_games = min(len(sorted_list), 10)
                for i in range(max_games):
                    game, freq = sorted_list[i]
                    msg+= "+ {}:  {}\n".format(game, freq_list[game])
                await self.bot.say("{}-                  These are the server's most played games at the moment:\n{}```".format(d, msg))
def setup(bot):
    n = WhoPlays(bot)
    bot.add_cog(n)

def setup(bot):
    n = Utility(bot)
    bot.add_cog(n)