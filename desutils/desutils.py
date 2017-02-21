import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from __main__ import send_cmd_help, settings
from cogs.utils import checks
import os
import aiohttp
import asyncio

# weird because 0 indexing
numbs = {
    "1⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
    "6⃣": 5,
    "7⃣": 6,
    "8⃣": 7,
    "9⃣": 8,
    "🔟": 9
}


class Desutils:
    def __init__(self, bot):
        self.bot = bot

    def _perms(self, ctx, perm):
        if ctx.message.author.id == settings.owner:
            return True

        ch = ctx.message.channel
        author = ctx.message.author
        resolved = ch.permissions_for(author)
        return resolved.perm

    async def _prompt(self, ctx, msg: str):
        await self.bot.say(msg)
        msg = await self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)
        return msg

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_owner()
    async def utilsmenu(self, ctx):
        menu = self.bot.get_cog("Menu")
        cmds = ["Send cog", "List cogs", "Perms"]

        result = await menu.number_menu(ctx, "Desutils selection menu", cmds, autodelete=True)
        cmd = cmds[result-1]

        if cmd == "Send cog" and self._perms(ctx, 'manage_roles'):
            return await ctx.invoke(self.sendcog)

        if cmd == "List cogs" and self._perms(ctx, 'manage_messages'):
            return await ctx.invoke(self.listcogs)

        if cmd == "Perms" and self._perms(ctx, 'manage_roles'):
            return await ctx.invoke(self.perms)

        if cmd is None:
            return await self.bot.say("Menu has expired.")

    @checks.is_owner()
    @commands.command(pass_context=True, no_pm=True)
    async def sendcog(self, ctx):
        fp = await self._prompt(ctx, ":thinking: What cog do you want to send?")
        fp = "cogs/{0}.py".format(fp.content)
        if os.path.exists(fp):
            await self.bot.send_file(ctx.message.channel, fp)
        else:
            await self.bot.say(":x: **Cog** ***not found!***")

    @checks.is_owner()
    @commands.command(pass_context=True, no_pm=True)
    async def listcogs(self, ctx):
        """Shows the status of cogs.
        + means the cog is loaded
        - means the cog is unloaded
        ? means the cog couldn't be found(it was probably removed manually)"""

        all_cogs = dataIO.load_json("data/red/cogs.json")
        loaded, unloaded, other = ("",)*3
        cogs = self.bot.cogs['Owner']._list_cogs()

        for x in all_cogs:
            if all_cogs.get(x):
                if x in cogs:
                    loaded += "+\t{0}\n".format(x.split('.')[1])
                else:
                    other += "?\t{0}\n".format(x.split('.')[1])
            elif x in cogs:
                unloaded += "-\t{0}\n".format(x.split('.')[1])
        msg = "```diff\n{0}{1}{2}```".format(loaded, unloaded, other)
        await self.bot.say(msg)

    @checks.is_owner()
    @commands.command(pass_context=True, no_pm=True)
    async def perms(self, ctx):
        user = await self._prompt(ctx, ":thinking: What user?")
        try:
            if user.mentions is not None:
                user = user.mentions[0]
        except:
            try:
                user = discord.utils.get(ctx.message.server.members, name=str(user.content))
            except:
                return await self.bot.say("User not found!:x:")
        perms = iter(ctx.message.channel.permissions_for(user))
        perms_we_have = "```diff\n"
        perms_we_dont = ""
        for x in perms:
            if "True" in str(x):
                perms_we_have += "+\t{0}\n".format(str(x).split('\'')[1])
            else:
                perms_we_dont += ("-\t{0}\n".format(str(x).split('\'')[1]))
        await self.bot.say("{0}{1}```".format(perms_we_have, perms_we_dont))


def setup(bot):
    n = Desutils(bot)
    bot.add_cog(n)