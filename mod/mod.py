import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
from cogs.utils.chat_formatting import box, pagify
from __main__ import send_cmd_help, settings
from copy import deepcopy
from cogs.utils.dataIO import fileIO
from datetime import datetime
from collections import deque, defaultdict
from cogs.utils.chat_formatting import escape_mass_mentions, box
import os
import random
from random import randint
from random import choice as randchoice
import re
import urllib
import logging
import asyncio
import json
import aiohttp
import urllib.parse as up

log = logging.getLogger("red.admin")


ACTIONS_REPR = {
    "BAN"     : ("Ban", "\N{HAMMER}"),
    "KICK"    : ("Kick", "\N{WOMANS BOOTS}"),
    "SOFTBAN" : ("Softban", "\N{DASH SYMBOL} \N{HAMMER}"),
    "UNBAN"   : ("Unban", "\N{SCALES}")
}

ACTIONS_CASES = {
    "BAN"     : True,
    "KICK"    : True,
    "SOFTBAN" : True,
    "UNBAN"   : True
}

default_settings = {
    "ban_mention_spam" : False,
    "delete_repeats"   : False,
    "mod-log"          : None
}


for act, enabled in ACTIONS_CASES.items():
    act = act.lower() + '_cases'
    default_settings[act] = enabled


class ModError(Exception):
    pass


class UnauthorizedCaseEdit(ModError):
    pass


class CaseMessageNotFound(ModError):
    pass


class NoModLogChannel(ModError):
    pass


class TempCache:
    """
    This is how we avoid events such as ban and unban
    from triggering twice in the mod-log.
    Kinda hacky but functioning
    """
    def __init__(self, bot):
        self.bot = bot
        self._cache = []

    def add(self, user, server, action, seconds=1):
        tmp = (user.id, server.id, action)
        self._cache.append(tmp)

        async def delete_value():
            await asyncio.sleep(seconds)
            self._cache.remove(tmp)

        self.bot.loop.create_task(delete_value())

    def check(self, user, server, action):
        return (user.id, server.id, action) in self._cache


class Mod:
    """Moderation tools."""

    def __init__(self, bot):
        self.bot = bot
        self.whitelist_list = dataIO.load_json("data/mod/whitelist.json")
        self.blacklist_list = dataIO.load_json("data/mod/blacklist.json")
        self.ignore_list = dataIO.load_json("data/mod/ignorelist.json")
        self.filter = dataIO.load_json("data/mod/filter.json")
        self.past_names = dataIO.load_json("data/mod/past_names.json")
        self.past_nicknames = dataIO.load_json("data/mod/past_nicknames.json")
        settings = dataIO.load_json("data/mod/settings.json")
        self.settings = defaultdict(lambda: default_settings.copy(), settings)
        self.cache = defaultdict(lambda: deque(maxlen=3))
        self.cases = dataIO.load_json("data/mod/modlog.json")
        self.last_case = defaultdict(dict)
        self.temp_cache = TempCache(bot)
        perms_cache = dataIO.load_json("data/mod/perms_cache.json")
        self._perms_cache = defaultdict(dict, perms_cache)
        self.base_api_url = "https://discordapp.com/api/oauth2/authorize?"
        self.enabled = fileIO('data/autoapprove/enabled.json', 'load')
        self.session = aiohttp.ClientSession()
        self._settings = dataIO.load_json('data/admin/settings.json')
        self._settable_roles = self._settings.get("ROLES", {})
        self.ee = ["https://cdn.discordapp.com/attachments/158076636929982465/294277395362480128/HQGh7tL.gif", "https://cdn.discordapp.com/attachments/133251234164375552/321128248065130506/banned3.gif", "https://cdn.discordapp.com/attachments/269293047962009602/294289909458534427/banned.gif", "https://cdn.discordapp.com/attachments/269293047962009602/294290049565065226/azCR8D1.gif", "https://cdn.discordapp.com/attachments/269293047962009602/294292018442797056/giphy_7.gif"]



        self.eee = ["https://cdn.discordapp.com/attachments/269293047962009602/294298407797915648/oIfsv6s.gif", "https://cdn.discordapp.com/attachments/269293047962009602/294300122681049088/giphy_9.gif", "https://cdn.discordapp.com/attachments/269293047962009602/294300638106615818/giphy_8.gif", "https://cdn.discordapp.com/attachments/269293047962009602/294300898841329674/kicked.gif"]




    def __unload(self):
        self.session.close()

    def save_enabled(self):
        fileIO('data/autoapprove/enabled.json', 'save', self.enabled)

    def _get_selfrole_names(self, server):
        if server.id not in self._settable_roles:
            return None
        else:
            return self._settable_roles[server.id]

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

    def _save_settings(self):
        dataIO.save_json('data/admin/settings.json', self._settings)

    def _set_selfroles(self, server, rolelist):
        self._settable_roles[server.id] = rolelist
        self._settings["ROLES"] = self._settable_roles
        self._save_settings()
    @commands.group(no_pm=True, pass_context=True)
    @checks.serverowner_or_permissions(manage_server=True)
    async def autoapprove(self, ctx):
        server = ctx.message.server
        channel = ctx.message.channel
        me = server.me
        if not channel.permissions_for(me).manage_messages:
            await self.bot.say("I don't have manage_messages permissions."
                               " I do not recommend submitting your "
                               "authorization key until I do.")
            return
        if not channel.permissions_for(me).manage_server:
            await self.bot.say("I do not have manage_server. This cog is "
                               "useless until I do.")
            return
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @autoapprove.command(no_pm=True, pass_context=True, name="toggle")
    @checks.serverowner_or_permissions(manage_server=True)
    async def _autoapprove_toggle(self, ctx):
        server = ctx.message.server
        if server.id not in self.enabled:
            await self.bot.say('AutoApprove not set up for this server.')
        else:
            self.enabled[server.id]["ENABLED"] = \
                not self.enabled[server.id]["ENABLED"]
            self.save_enabled()
            if self.enabled[server.id]["ENABLED"]:
                await self.bot.say("AutoApprove enabled.")
            else:
                await self.bot.say("AutoApprove disabled.")

    @autoapprove.command(no_pm=True, pass_context=True, name="setup")
    @checks.serverowner_or_permissions(manage_server=True)
    async def _autoapprove_setup(self, ctx, authorization_key):
        """You will need to submit the user Authorization header key
            (can be found using dev tools in Chrome) of some user that will
            always have manage_server on this server."""
        server = ctx.message.server
        if server.id not in self.enabled:
            self.enabled[server.id] = {"ENABLED": False}
        self.enabled[server.id]['KEY'] = authorization_key
        self.save_enabled()
        await self.bot.delete_message(ctx.message)
        await self.bot.say('Key saved. Deleted message for security.'
                           ' Use `autoapprove toggle` to enable.')

    @commands.command(no_pm=True, pass_context=True)
    async def addbot(self, ctx, oauth_url):
        """Requires your OAUTH2 URL to automatically approve your bot to
            join"""
        server = ctx.message.server
        if server.id not in self.enabled:
            await self.bot.say('AutoApprove not set up for this server.'
                               ' Let the server owner know if you think it'
                               ' should be.')
            return
        elif not self.enabled[server.id]['ENABLED']:
            await self.bot.say('AutoApprove not enabled for this server.'
                               ' Let the server owner know if you think it'
                               ' should be.')
            return

        key = self.enabled[server.id]['KEY']
        parsed = up.urlparse(oauth_url)
        queryattrs = up.parse_qs(parsed.query)
        queryattrs['client_id'] = int(queryattrs['client_id'][0])
        queryattrs['scope'] = queryattrs['scope'][0]
        queryattrs.pop('permissions', None)
        full_url = self.base_api_url + up.urlencode(queryattrs)
        status = await self.get_bot_api_response(full_url, key, server.id)
        if status < 400:
            await self.bot.say("Succeeded!")
        else:
            await self.bot.say("Failed, error code {}. ".format(status))


    @commands.command(no_pm=True, pass_context=True, aliases=["rar"])
    @checks.admin_or_permissions(manage_roles=True)
    async def removeallroles(self, ctx, user: discord.Member=None):
        """removes all roles from a user bot must be above the user and have manage roles perms
        This will always return it removed shit cuz of @everyone role """
        author = ctx.message.author
        server = ctx.message.server
        channel = ctx.message.channel
        if user is None:
            await self.bot.send_cmd_help(ctx)
            return
        if not channel.permissions_for(server.me).manage_roles:
            await self.bot.say(' :bangbang: **Do you read ? I don\'t have manage_roles and it\'s a necessity for** ***ALL***  **role related operations.** 😐')
            return
        try:
            await self.bot.replace_roles(user)
            await self.bot.say(":bangbang: **I've** ***successfully***  **Removed** ***All roles from***  `{}` :thumbsup: :stuck_out_tongue_closed_eyes: ".format(user.name).replace("`", ""))
            return
            # This will always return ^ cuz of @everyone role
        except discord.HTTPException:
            await self.bot.say(" :bangbang:  Removing roles failed! Possibly due to role hierachy, or the bot not having perms:bangbang: ")
            return

    @commands.command(no_pm=True, pass_context=True, aliases=["ar"])
    @checks.admin_or_permissions(manage_roles=True)
    async def addrole(self, ctx, rolename, user: discord.Member=None):
        """Adds a role to a user, defaults to author
        Role name must be in quotes if there are spaces.
        if the user is not speciffied it will remove the role from the invoker if present"""
        author = ctx.message.author
        channel = ctx.message.channel
        server = ctx.message.server

        role = self._role_from_string(server, rolename)

        if role is None:
            await self.bot.say('That role cannot be found.')
            return

        if user is None:
            user = author

        if not channel.permissions_for(server.me).manage_roles:
            await self.bot.say('I don\'t have manage_roles.')
            return

        await self.bot.add_roles(user, role)
        await self.bot.say(":bangbang:  **Successfully** Added role ***{}***  to ***{}*** :thumbsup:".format(role.name, user.name).replace("`", ""))

    @commands.command(pass_context=True, no_pm=True, aliases=["cr"])
    @checks.admin_or_permissions(manage_roles=True)
    async def createrole(self, ctx, *, rolename: str = None):
        """Create a role using the bot The role will be listed at the bottom of role list."""
        if rolename is None:
            await self.bot.say("How am i supposed to **create a role** with no ***role name*** :thinking: :face_palm:")
            return
        server = ctx.message.server
        name = ''.join(rolename)
        await self.bot.create_role(server, name= '{}'.format(name))
        message = ":bangbang: **I've** ***successfully***  **created the role** ***`{}`*** :thumbsup:".format(name)
        await self.bot.say(message)

    @commands.command(pass_context=True, aliases=["dr"])
    @checks.admin_or_permissions(manage_roles=True)
    async def deleterole(self, ctx, rolename):
        """Deletes an existing role. Bot must be above the role "Role hierachy" mate"""
        channel = ctx.message.channel
        server = ctx.message.server

        role = self._role_from_string(server, rolename)

        if role is None:
            await self.bot.say(':no_good: That role cannot be found. :no_good:')
            return

        await self.bot.delete_role(server,role)
        message = " :call_me: **I've** ***successfully*** **deleted the role** ***`{}`*** :thumbsup:".format(rolename)
        await self.bot.say(message)

    @commands.group(pass_context=True, no_pm=True)
    async def adminset(self, ctx):
        """Manage Admin settings"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @adminset.command(pass_context=True, name="selfrolesclear")
    @checks.admin_or_permissions(manage_roles=True)
    async def adminset_selfroles_clear(self, ctx, *, rolelist=None):
        """Clears selfroles"""
        server = ctx.message.server
        if rolelist is None:
            await self.bot.say("**SelfRole List CLEARED** :thumbsup:")
            self._set_selfroles(server, [])
            return
    @adminset.command(pass_context=True, name="selfroles")
    @checks.admin_or_permissions(manage_roles=True)
    async def adminset_selfroles(self, ctx, *, rolelist=None):
        """Set which roles users can set themselves.
        COMMA SEPARATED LIST (e.g. Admin,Staff,Mod)"""
        server = ctx.message.server
        if rolelist is None:
            await self.bot.say("**RoleList Is none** If you're trying to clear the list please do `{}adminset selfrolesclear`".format(ctx.prefix))
            return
        unparsed_roles = list(map(lambda r: r.strip(), rolelist.split(',')))
        parsed_roles = list(map(lambda r: self._role_from_string(server, r),
                                unparsed_roles))
        if len(unparsed_roles) != len(parsed_roles):
            not_found = set(unparsed_roles) - {r.name for r in parsed_roles}
            await self.bot.say(
                ":x: These roles were **not found:** `{}`\n\nPlease"
                " try again. :frowning:".format(not_found))
        parsed_role_set = list({r.name for r in parsed_roles})
        self._set_selfroles(server, parsed_role_set)
        await self.bot.say(
            "Self roles successfully set to: **{}**".format(parsed_role_set))

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def removerole(self, ctx, rolename, user: discord.Member=None):
        """Removes a role from user, defaults to author
        Role name must be in quotes if there are spaces.
        if the user is not speciffied it will remove the role from the invoker if present"""
        server = ctx.message.server
        author = ctx.message.author

        role = self._role_from_string(server, rolename)
        if role is None:
            await self.bot.say("**Role not found.** :no_good:")
            return

        if user is None:
            user = author

        if role in user.roles:
            try:
                await self.bot.remove_roles(user, role)
                await self.bot.say(":thumbsup: Role `{}` **Successfully** removed From ***{}*** :bangbang:".format(rolename, user.name).replace("`", ""))
            except discord.Forbidden:
                await self.bot.say(" :bangbang: I don't have permissions to manage roles!:bangbang: ")
        else:
            await self.bot.say(" :bangbang: User does not have that role. :no_good: ")

    @commands.group(no_pm=True, pass_context=True, invoke_without_command=True)
    async def selfrole(self, ctx, *, rolename):
        """Allows users to set their own role.
        Configurable using `adminset`"""
        server = ctx.message.server
        author = ctx.message.author
        role_names = self._get_selfrole_names(server)
        if role_names is None:
            await self.bot.say(":no_good: **I have no user settable roles for this"
                               " server.** :frowning:")
            return

        roles = list(map(lambda r: self._role_from_string(server, r),
                         role_names))

        role_to_add = self._role_from_string(server, rolename, roles=roles)

        try:
            await self.bot.add_roles(author, role_to_add)
        except discord.errors.Forbidden:
            log.debug("{} just tried to add a role but I was forbidden".format(
                author.name))
            await self.bot.say("I don't have permissions to do that.")
        except AttributeError:  # role_to_add is NoneType
            log.debug("{} not found as settable on {}".format(rolename,
                                                              server.id))
            await self.bot.say("That role isn't user settable.")
        else:
            log.debug("Role {} added to {} on {}".format(rolename, author.name,
                                                         server.id))
            await self.bot.reply(":punch: I've **successfully Added the role** `{}` To you :smile:".format(rolename))

    @selfrole.command(no_pm=True, pass_context=True, name="remove")
    async def selfrole_remove(self, ctx, *, rolename):
        """Allows users to remove their own roles
        Configurable using `adminset`"""
        server = ctx.message.server
        author = ctx.message.author
        role_names = self._get_selfrole_names(server)
        if role_names is None:
            await self.bot.say("I have no user settable roles for this"
                               " server.")
            return

        roles = list(map(lambda r: self._role_from_string(server, r),
                         role_names))
        role_to_remove = self._role_from_string(server, rolename, roles=roles)

        try:
            await self.bot.remove_roles(author, role_to_remove)
        except discord.errors.Forbidden:
            log.debug("{} just tried to remove a role but I was"
                      " forbidden".format(author.name))
            await self.bot.say("I don't have permissions to do that.")
        except AttributeError:  # role_to_remove is NoneType
            log.debug("{} not found as removeable on {}".format(rolename,
                                                                server.id))
            await self.bot.say("That role isn't user removeable.")
        else:
            log.debug("Role {} removed from {} on {}".format(rolename,
                                                             author.name,
                                                             server.id))
            await self.bot.reply(":punch: I've **successfully Removed the role** `{}` from you :thumbsup:".format(rolename))

    @commands.group(pass_context=True, no_pm=True)
    @checks.serverowner_or_permissions(administrator=True)
    async def modset(self, ctx):
        """Manages server administration settings."""
        if ctx.invoked_subcommand is None:
            server = ctx.message.server
            await send_cmd_help(ctx)
            roles = settings.get_server(server).copy()
            _settings = {**self.settings[server.id], **roles}
            if "delete_delay" not in _settings:
                _settings["delete_delay"] = -1
            msg = ("Admin role: {ADMIN_ROLE}\n"
                   "Mod role: {MOD_ROLE}\n"
                   "Mod-log: {mod-log}\n"
                   "Delete repeats: {delete_repeats}\n"
                   "Ban mention spam: {ban_mention_spam}\n"
                   "Delete delay: {delete_delay}\n"
                   "".format(**_settings))
            await self.bot.say(box(msg))

    @modset.command(name="adminrole", pass_context=True, no_pm=True)
    async def _modset_adminrole(self, ctx, *, role_name: str):
        """Sets the admin role for this server, case insensitive."""
        server = ctx.message.server
        if server.id not in settings.servers:
            await self.bot.say("Remember to set modrole too.")
        settings.set_server_admin(server, role_name)
        await self.bot.say("Admin role set to '{}'".format(role_name))

    @modset.command(name="modrole", pass_context=True, no_pm=True)
    async def _modset_modrole(self, ctx, *, role_name: str):
        """Sets the mod role for this server, case insensitive."""
        server = ctx.message.server
        if server.id not in settings.servers:
            await self.bot.say("Remember to set adminrole too.")
        settings.set_server_mod(server, role_name)
        await self.bot.say("Mod role set to '{}'".format(role_name))

    @modset.command(pass_context=True, no_pm=True)
    async def modlog(self, ctx, channel : discord.Channel=None):
        """Sets a channel as mod log
        Leaving the channel parameter empty will deactivate it"""
        server = ctx.message.server
        if channel:
            self.settings[server.id]["mod-log"] = channel.id
            await self.bot.say("Mod events will be sent to {}"
                               "".format(channel.mention))
        else:
            if self.settings[server.id]["mod-log"] is None:
                await send_cmd_help(ctx)
                return
            self.settings[server.id]["mod-log"] = None
            await self.bot.say("Mod log deactivated.")
        dataIO.save_json("data/mod/settings.json", self.settings)

    @modset.command(pass_context=True, no_pm=True)
    async def banmentionspam(self, ctx, max_mentions : int=False):
        """Enables auto ban for messages mentioning X different people
        Accepted values: 5 or superior"""
        server = ctx.message.server
        if max_mentions:
            if max_mentions < 5:
                max_mentions = 5
            self.settings[server.id]["ban_mention_spam"] = max_mentions
            await self.bot.say("Autoban for mention spam enabled. "
                               "Anyone mentioning {} or more different people "
                               "in a single message will be autobanned."
                               "".format(max_mentions))
        else:
            if self.settings[server.id]["ban_mention_spam"] is False:
                await send_cmd_help(ctx)
                return
            self.settings[server.id]["ban_mention_spam"] = False
            await self.bot.say("Autoban for mention spam disabled.")
        dataIO.save_json("data/mod/settings.json", self.settings)

    @modset.command(pass_context=True, no_pm=True)
    async def deleterepeats(self, ctx):
        """Enables auto deletion of repeated messages"""
        server = ctx.message.server
        if not self.settings[server.id]["delete_repeats"]:
            self.settings[server.id]["delete_repeats"] = True
            await self.bot.say("Messages repeated up to 3 times will "
                               "be deleted.")
        else:
            self.settings[server.id]["delete_repeats"] = False
            await self.bot.say("Repeated messages will be ignored.")
        dataIO.save_json("data/mod/settings.json", self.settings)

    @modset.command(pass_context=True, no_pm=True)
    async def resetcases(self, ctx):
        """Resets modlog's cases"""
        server = ctx.message.server
        self.cases[server.id] = {}
        dataIO.save_json("data/mod/modlog.json", self.cases)
        await self.bot.say("Cases have been reset.")

    @modset.command(pass_context=True, no_pm=True)
    async def deletedelay(self, ctx, time: int=None):
        """Sets the delay until the bot removes the command message.
            Must be between -1 and 60.
        A delay of -1 means the bot will not remove the message."""
        server = ctx.message.server
        if time is not None:
            time = min(max(time, -1), 60)  # Enforces the time limits
            self.settings[server.id]["delete_delay"] = time
            if time == -1:
                await self.bot.say("Command deleting disabled.")
            else:
                await self.bot.say("Delete delay set to {}"
                                   " seconds.".format(time))
            dataIO.save_json("data/mod/settings.json", self.settings)
        else:
            try:
                delay = self.settings[server.id]["delete_delay"]
            except KeyError:
                await self.bot.say("Delete delay not yet set up on this"
                                   " server.")
            else:
                if delay != -1:
                    await self.bot.say("Bot will delete command messages after"
                                       " {} seconds. Set this value to -1 to"
                                       " stop deleting messages".format(delay))
                else:
                    await self.bot.say("I will not delete command messages.")

    @modset.command(pass_context=True, no_pm=True, name='cases')
    async def set_cases(self, ctx, action: str = None, enabled: bool = None):
        """Enables or disables case creation for each type of mod action

        Enabled can be 'on' or 'off'"""
        server = ctx.message.server

        if action == enabled:  # No args given
            await self.bot.send_cmd_help(ctx)
            msg = "Current settings:\n```py\n"
            maxlen = max(map(lambda x: len(x[0]), ACTIONS_REPR.values()))
            for action, name in ACTIONS_REPR.items():
                action = action.lower() + '_cases'
                value = self.settings[server.id].get(action,
                                                     default_settings[action])
                value = 'enabled' if value else 'disabled'
                msg += '%s : %s\n' % (name[0].ljust(maxlen), value)

            msg += '```'
            await self.bot.say(msg)

        elif action.upper() not in ACTIONS_CASES:
            msg = "That's not a valid action. Valid actions are: \n"
            msg += ', '.join(sorted(map(str.lower, ACTIONS_CASES)))
            await self.bot.say(msg)

        elif enabled == None:
            action = action.lower() + '_cases'
            value = self.settings[server.id].get(action,
                                                 default_settings[action])
            await self.bot.say('Case creation for %s is currently %s' %
                               (action, 'enabled' if value else 'disabled'))
        else:
            name = ACTIONS_REPR[action.upper()][0]
            action = action.lower() + '_cases'
            value = self.settings[server.id].get(action,
                                                 default_settings[action])
            if value != enabled:
                self.settings[server.id][action] = enabled
                dataIO.save_json("data/mod/settings.json", self.settings)
            msg = ('Case creation for %s actions %s %s.' %
                   (name.lower(),
                    'was already' if enabled == value else 'is now',
                    'enabled' if enabled else 'disabled')
                   )
            await self.bot.say(msg)

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(move_members=True)
    async def move(self, ctx, voicechannel: discord.Channel, *user: discord.Member):
        """
        Move two or more users at a time to a voice channel
        Case sensitime Which means it has to be in the exact format Or if you have developer mode you can Use id's
        Examples: ~move AFK @dangerous @teddy / ~move channel id : 199292534671802369 user ids: 187570149207834624 203649661611802624
        this also works if you do one id and one text like ~move 199292534671802369 @dangerous"""
        author = ctx.message.author
        server = ctx.message.server
        try:
            for user in ctx.message.mentions:
                await self.bot.move_member(user, voicechannel)
        except discord.Forbidden:
            await self.bot.say("***`Move members`*** **is a required permission for me to move members to voice channels** <:bruh:321371077941133322>__***PLEASE ASSIGN IT TO ME***__<:bruh:321371077941133322>")
        except discord.InvalidArgument:
            await self.bot.say(":x: **Channel must be a Voice Channel and not a Text Channel**")
        except discord.HTTPException:
            memberlist = " , ".join(m.display_name for m in ctx.message.mentions)
            await self.bot.say("<:xmark:314349398824058880> **An Error Occured.** **I was unable to move** ***``{}``***` **to** ***``{}``***🙅".format(memberlist, voicechannel))
        else:
            memberlist = " , ".join(m.display_name for m in ctx.message.mentions)
            await self.bot.say(':white_check_mark: **Done** <:check:314349398811475968> **Moved** ***``{0}``*** **to** ***`{1}`*** :thumbsup:'.format(memberlist, voicechannel))
    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(move_members=True)
    async def massmove(self, ctx, from_channel: discord.Channel, to_channel: discord.Channel):
        """Massmove users to another voice channel
        Channel id's can also be used"""
        await self._massmove(ctx, from_channel, to_channel)

    async def _massmove(self, ctx, from_channel, to_channel):
        """Internal function: Massmove users to another voice channel"""
        # check if channels are voice channels. Or moving will be very... interesting...
        type_from = str(from_channel.type)
        type_to = str(to_channel.type)
        if type_from == 'text':
            await self.bot.say('{} is not a valid voice channel'.format(from_channel.name))
            log.debug('SID: {}, from_channel not a voice channel'.format(from_channel.server.id))
        elif type_to == 'text':
            await self.bot.say('{} is not a valid voice channel'.format(to_channel.name))
            log.debug('SID: {}, to_channel not a voice channel'.format(to_channel.server.id))
        else:
            try:
                log.debug('Starting move on SID: {}'.format(from_channel.server.id))
                log.debug('Getting copy of current list to move')
                voice_list = list(from_channel.voice_members)
                for member in voice_list:
                    await self.bot.move_member(member, to_channel)
                    log.debug('Member {} moved to channel {}'.format(member.id, to_channel.id))
                    await asyncio.sleep(0.05)
            except discord.Forbidden:
                await self.bot.say('I have no permission to move members.')
            except discord.HTTPException:
                await self.bot.say('A error occured. Please try again')
            else:
                await self.bot.say(" :thumbsup: I am done moving Everyone in **{} to {}** :D".format(from_channel.name, to_channel.name))

    @commands.command(no_pm=True, pass_context=True, aliases=["km","mk","rk","reasonk","reasonkick","messagek","messagekick"])
    @checks.admin_or_permissions(kick_members=True)
    async def kickm(self, ctx, user: discord.Member, *, reason: str=None):
        """Kicks user.(Wit message(sends a message formated as reason to te banned user in dms))
        If words are typed after user it will format into the ban message and As the reason in logs."""
        author = ctx.message.author
        server = author.server
        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        try:  # We don't want blocked DMs preventing us from banning
            em = discord.Embed(title=":bellhop: You have been KICKED from {}.:hammer_pick:".format(server.name),
            colour=discord.Colour(value=colour), timestamp=__import__('datetime').datetime.utcnow())
            em.add_field(name="Reason ⚖", value="**{}**".format(reason))
            em.set_thumbnail(url=randchoice(self.eee))
            msg = await self.bot.send_message(user, embed=em)
            await self.bot.kick(user)
            logger.info("{}({}) kicked {}({})".format(
                author.name, author.id, user.name, user.id))
            if self.settings[server.id].get('kick_cases',
                                            default_settings['kick_cases']):
                await self.new_case(server,
                                    action="KICK",
                                    mod=author,
                                    user=user,
                                    reason=reason)
            await self.bot.say(" :ballot_box_with_check:️ Alrighty! :white_check_mark: **I've kicked** ***`{}`*** ***successfully*** :thumbsup:***Message sent**:white_check_mark:* ".format(user.name).replace("`", ""))
        except discord.errors.Forbidden:
            await self.bot.say(" :no_entry: Not Allowed to kick or Kick that specified user Bruv ¯\_(ツ)_/¯ :no_entry: sorry")
            await self.bot.delete_message(msg)
            return
        except discord.errors.HTTPException:
                await self.bot.kick(user)
                logger.info("{}({}) kicked {}({})".format(
                    author.name, author.id, user.name, user.id))
                logger.info("{}({}) banned {}({})wit message {}".format(
                    author.name, author.id, user.name, user.id, reason))
                if self.settings[server.id].get('kick_cases',
                                                default_settings['kick_cases']):
                    await self.new_case(server,
                                        action="KICK",
                                        mod=ctx.message.author,
                                        user=user,
                                        reason=reason)
                await self.bot.say("**I could not have sent a dm to `{}` So instead i just Kicked the faggot no worries.**".format(user.name))
        except Exception as e:
            print(e)

    @commands.command(no_pm=True, pass_context=True, aliases=["bm","mb","rb","reasonb","reasonban","messageb","messageban"])
    @checks.admin_or_permissions(ban_members=True)
    async def banm(self, ctx, user: discord.Member, *, reason: str=None):
        """Bans user.(Wit message(sends a message formated as reason to te banned user in dms))
        If words are typed after user it will format into the ban message As the reason."""
        author = ctx.message.author
        server = author.server
        channel = ctx.message.channel
        can_ban = channel.permissions_for(server.me).ban_members
        colour = ''.join([randchoice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        if can_ban:
            try:  # We don't want blocked DMs preventing us from banning
                self.temp_cache.add(user, server, "BAN")
                em = discord.Embed(title=":bellhop: You have been BANNED from {}.:hammer_pick:".format(server.name),
                colour=discord.Colour(value=colour), timestamp=__import__('datetime').datetime.utcnow())
                em.add_field(name="Reason ⚖", value="**{}**".format(reason))
                em.set_thumbnail(url=randchoice(self.ee))
                msg = await self.bot.send_message(user, embed=em)
                pass
                await self.bot.ban(user)
                await self.bot.say(" :punch: **I've** **successfully Banned** ***`{}`*** <:banzy:322839986300780554>***Message sent***:white_check_mark:".format(user.name).replace("`", ""))
                logger.info("{}({}) banned {}({})wit message {}".format(
                    author.name, author.id, user.name, user.id, reason))
                if self.settings[server.id].get('ban_cases',
                                                default_settings['ban_cases']):
                    await self.new_case(server,
                                        action="BAN",
                                        mod=author,
                                        user=user,
                                        reason=reason)
            except discord.errors.Forbidden:
                await self.bot.say(":bangbang:Not Allowed to Ban or ban that specified user ¯\_(ツ)_/¯ :x: ")
                await self.bot.delete_message(msg)

                return
            except discord.errors.HTTPException:
                await self.bot.ban(user)
                self.temp_cache.add(user, server, "BAN")
                logger.info("{}({}) banned {}({})wit message {}".format(
                    author.name, author.id, user.name, user.id, reason))
                if self.settings[server.id].get('ban_cases',
                                                default_settings['ban_cases']):
                    await self.new_case(server,
                                        action="BAN",
                                        mod=ctx.message.author,
                                        user=user,
                                        reason=reason)
                await self.bot.say("**I could not have sent a dm to `{}` So instead i just banned the faggot no worries.**".format(user.name))
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(1)

#    @commands.command(pass_context=True)
#    async def banlist(self, ctx):
        """Displays the server's banlist"""
        try:
            banlist = await self.bot.get_bans(ctx.message.server)
        except discord.errors.Forbidden:
            await self.bot.say("I do not have the `Ban Members` permission")
            return
        bancount = len(banlist)
        if bancount == 0:
            banlist = "No users are banned from this server"
        else:
            banlist = ", ".join(map(str, banlist))
        await self.bot.say("Total bans: `{}`\n```{}```".format(bancount, banlist))


    @commands.command(no_pm=True, pass_context=True, aliases=["k","ks","silentk","silentkick"])
    @checks.admin_or_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason: str=None):
        """Kicks user.(Silently(Baisically it doesnt add a message like banm/kickm))
        If words are typed after user it will format into the Kick log As the reason."""
        author = ctx.message.author
        server = author.server
        try:
            await self.bot.kick(user)
            logger.info("{}({}) kicked {}({})".format(
                author.name, author.id, user.name, user.id))
            if self.settings[server.id].get('kick_cases',
                                            default_settings['kick_cases']):
                await self.new_case(server,
                                    action="KICK",
                                    mod=author,
                                    user=user,
                                    reason=reason)
            await self.bot.say(" :ballot_box_with_check:️ Alrighty! :white_check_mark: **I've Silently kicked** ***`{}`*** ***successfully*** :thumbsup: ".format(user.name).replace("`", ""))
        except discord.errors.Forbidden:
            await self.bot.say(" :no_entry: Not Allowed to kick or Kick that specified user  Bruv ¯\_(ツ)_/¯ :no_entry: sorry")
        except Exception as e:
            print(e)

    @commands.command(no_pm=True, pass_context=True, aliases=["b","bs","silentb","silentban"])
    @checks.admin_or_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member, *, reason: str=None):
        """Bans user.(Silently(Baisically it doesnt add a message like banm/kickm))
        If words are typed after user it will format into the ban log As the reason."""
        author = ctx.message.author
        server = author.server
        channel = ctx.message.channel
        can_ban = channel.permissions_for(server.me).ban_members
        if can_ban:
            try:  # We don't want blocked DMs preventing us from banning
                self.temp_cache.add(user, server, "BAN")
                await self.bot.ban(user)
                await self.bot.say(" :punch: I've **successfully Banned** ***`{}`*** **🤐Silently🙊** <:ban:322839828544749568>:white_check_mark:".format(user.name).replace("`", ""))
                logger.info("{}({}) banned {}({})".format(
                    author.name, author.id, user.name, user.id))
                if self.settings[server.id].get('ban_cases',
                                                default_settings['ban_cases']):
                    await self.new_case(server,
                                        action="BAN",
                                        mod=author,
                                        user=user,
                                        reason=reason)
            except discord.errors.Forbidden:
                    await self.bot.say(":bangbang:Not Allowed to Ban or Ban that specified user ¯\_(ツ)_/¯ :x: ")
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(1)
    @commands.command(no_pm=True, pass_context=True, aliases=["hb"])
    @checks.admin_or_permissions(ban_members=True)
    async def hackban(self, ctx, *, user_id: str):
        """bans users by ID.
        """
        server = ctx.message.server.id
        user = "<@{}>".format(user_id)
        try:
            await self.bot.http.ban(user_id, server)
            await self.bot.say(":punch: I've **successfully Banned** <@{}> :hammer::white_check_mark:".format(user_id))
        except discord.errors.Forbidden:
            await self.bot.say("***Failed to ban. Either `Lacking Permissions` or `User cannot be found`.***")
    @commands.command(no_pm=True, pass_context=True, aliases=["ub"])
    @checks.admin_or_permissions(ban_members=True)
    async def unban(self, ctx, *, user_id: str):
        """Unbans users by ID."""
        author = ctx.message.author
        server = ctx.message.server
        userr = "<@{}>".format(user_id)
        try:
            await self.bot.http.unban(user_id, server.id)
            await self.bot.say(":punch: <@{}> ***Unbanned***:thumbsup:".format(user_id))
        except discord.errors.Forbidden:
            await self.bot.say("**Failed to unban.\n**I am** ***`Lacking Permissions`***")
        except discord.HTTPException:
            await self.bot.say("**Failed to unban.** ***`User cannot be found.`***")
    @commands.command(no_pm=True, pass_context=True, aliases=["sb"])
    @checks.admin_or_permissions(ban_members=True)
    async def softban(self, ctx, user: discord.Member, *, reason: str = None):
        """Kicks the user, deleting 1 day worth of messages."""
        server = ctx.message.server
        channel = ctx.message.channel
        can_ban = channel.permissions_for(server.me).ban_members
        author = ctx.message.author
        try:
            invite = await self.bot.create_invite(server, max_age=3600*24)
        except:
            invite = ""
        if can_ban:
            try:
                try:  # We don't want blocked DMs preventing us from banning
                    msg = await self.bot.send_message(user, "**You've Been Softbanned!**\N{DASH SYMBOL} \N{HAMMER}\n"
                              "As a Means Deleting your messages.\n"
                              "You can now join the server again.\n{} ".format(invite))
                except:
                    pass
                self.temp_cache.add(user, server, "BAN")
                await self.bot.ban(user, 1)
                logger.info("{}({}) softbanned {}({}), deleting 1 day worth "
                    "of messages".format(author.name, author.id, user.name,
                     user.id))
                if self.settings[server.id].get('softban_cases',
                                                default_settings['softban_cases']):
                    await self.new_case(server,
                                        action="SOFTBAN",
                                        mod=author,
                                        user=user,
                                        reason=reason)
                self.temp_cache.add(user, server, "UNBAN")
                await self.bot.unban(server, user)
                await self.bot.say("**My work here is Done. :thumbsup:**\nUser **{}** Has been **Soft** ***BANNED*** \N{DASH SYMBOL} \N{HAMMER}".format(user.name))
            except discord.errors.Forbidden:
                await self.bot.say("My role is not high enough to softban that user.")
                await self.bot.delete_message(msg)
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(1)
                self._tmp_banned_cache.remove(user)
        else:
            await self.bot.say("I'm not allowed to do that.")

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_nicknames=True)
    async def rename(self, ctx, user : discord.Member, *, nickname=""):
        """Changes user's nickname

        Leaving the nickname empty will remove it."""
        nickname = nickname.strip()
        if nickname == "":
            nickname = None
        try:
            await self.bot.change_nickname(user, nickname)
            await self.bot.say("***Done.*** I've renamed **{}** to ***{}***".format(user.name, nickname))
        except discord.Forbidden:
            await self.bot.say("I cannot do that, I lack the "
                "\"Manage Nicknames\" permission.")

    @commands.command(pass_context = True)
    @checks.mod_or_permissions(manage_messages=True)
    async def botclean(self, ctx, limit : int = None):
        """Cleans all of the bot messages in the channel"""
        channel = ctx.message.channel
        server = channel.server
        has_permissions = channel.permissions_for(server.me).manage_messages
        if limit is None:
            limit = 100
        elif limit > 100:
            limit = 100
        if not has_permissions:
            await self.bot.say("**Congratulations,**\n***You played yourself.***:tada:\n**I do not have** ***`manage_messages`*** **permissions.**")
            return

        await self.bot.delete_message(ctx.message)
        deleted = await self.bot.purge_from(ctx.message.channel, limit=limit, before=ctx.message, check= lambda e: e.author.bot)
        reply = await self.bot.say('***Successfully pruned `{}` messages. :ok_hand:<:check:314349398811475968>***'.format(len(deleted)))
        await asyncio.sleep(3)
        await self.bot.delete_message(reply)

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    @checks.mod_or_permissions(administrator=True)
    async def bmute(self, ctx, user : discord.Member):
        """Bmutes A user"""
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.channel_mute, user=user)

    @bmute.command(name="channel", pass_context=True, no_pm=True)
    async def channel_mute(self, ctx, user : discord.Member):
        """Bmutes user in the current channel"""
        channel = ctx.message.channel
        overwrites = channel.overwrites_for(user)
        if overwrites.send_messages is False:
            await self.bot.say(" `{}` ***can't send messages in this channel.***")
            return
        self._perms_cache[user.id][channel.id] = overwrites.send_messages
        overwrites.send_messages = False
        try:
            await self.bot.edit_channel_permissions(channel, user, overwrites)
        except discord.Forbidden:
            await self.bot.say("**Due to role Hierarchy I cannot be lower than the user i am muting.\nI also need manage roles, manage channel and server perms**")
        else:
            dataIO.save_json("data/mod/perms_cache.json", self._perms_cache)
            await self.bot.say("**I've Muted** ***{}***  ***Channelly***".format(user.name))

    @bmute.command(name="server", pass_context=True, no_pm=True)
    async def server_mute(self, ctx, user : discord.Member):
        """Bmutes a user serverwide."""
        server = ctx.message.server
        register = {}
        for channel in server.channels:
            if channel.type != discord.ChannelType.text:
                continue
            overwrites = channel.overwrites_for(user)
            if overwrites.send_messages is False:
                continue
            register[channel.id] = overwrites.send_messages
            overwrites.send_messages = False
            try:
                await self.bot.edit_channel_permissions(channel, user,
                                                        overwrites)
            except discord.Forbidden:
                await self.bot.say("**Due to role Hierarchy I cannot be lower than the user i am muting.\nI also need manage roles, manage channel and server perms**")
                return
            else:
                await asyncio.sleep(0.1)
        if not register:
            await self.bot.say(":x: :no_good: *** {} is already muted in all channels.***".format(user.name))
            return
        self._perms_cache[user.id] = register
        dataIO.save_json("data/mod/perms_cache.json", self._perms_cache)
        await self.bot.say("**I've Muted** ***{}***  ***Serverly***".format(user.name))

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    @checks.mod_or_permissions(administrator=True)
    async def bunmute(self, ctx, user : discord.Member):
        """Bunmute a user"""
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.channel_unmute, user=user)

    @bunmute.command(name="channel", pass_context=True, no_pm=True)
    async def channel_unmute(self, ctx, user : discord.Member):
        """Bunmute in channel"""
        channel = ctx.message.channel
        overwrites = channel.overwrites_for(user)
        if overwrites.send_messages:
            await self.bot.say("`{}` ***Is not muted in*** `{}`".format(user.name,channel.name))
            return
        if user.id in self._perms_cache:
            old_value = self._perms_cache[user.id].get(channel.id, None)
        else:
            old_value = None
        overwrites.send_messages = old_value
        is_empty = self.are_overwrites_empty(overwrites)
        try:
            if not is_empty:
                await self.bot.edit_channel_permissions(channel, user,
                                                        overwrites)
            else:
                await self.bot.delete_channel_permissions(channel, user)
        except discord.Forbidden:
            await self.bot.say("**Due to role Hierarchy I cannot be lower than the user i am muting.\nI also need manage roles, manage channel and server perms**")
        else:
            try:
                del self._perms_cache[user.id][channel.id]
            except KeyError:
                pass
            if user.id in self._perms_cache and not self._perms_cache[user.id]:
                del self._perms_cache[user.id] #cleanup
            dataIO.save_json("data/mod/perms_cache.json", self._perms_cache)
            await self.bot.say("**I've Unmuted** ***{}***  ***(Channel Wise)***".format(user.name))

    @commands.group(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def cleanup(self, ctx):
        """Deletes messages."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @cleanup.command(pass_context=True, no_pm=True)
    async def text(self, ctx, text: str, number: int):
        """Deletes last X messages matching the specified text.

        Example:
        cleanup text \"test\" 5
        cleant texthere 59

        Remember to use double quotes."""

        channel = ctx.message.channel
        author = ctx.message.author
        server = author.server
        is_bot = self.bot.user.bot
        has_permissions = channel.permissions_for(server.me).manage_messages

        def check(m):
            if text in m.content:
                return True
            elif m == ctx.message:
                return True
            else:
                return False

        to_delete = [ctx.message]

        if not has_permissions:
            await self.bot.say("**Congratulations,**\n***You played yourself.***:tada:\n**I do not have** ***`manage_messages`*** **permissions.**")
            return

        tries_left = 5
        tmp = ctx.message

        while tries_left and len(to_delete) - 1 < number:
            async for message in self.bot.logs_from(channel, limit=100,
                                                    before=tmp):
                if len(to_delete) - 1 < number and check(message):
                    to_delete.append(message)
                tmp = message
            tries_left -= 1

        logger.info("{}({}) deleted {} messages "
                    " containing '{}' in channel {}".format(author.name,
                    author.id, len(to_delete), text, channel.id))

        if is_bot:
            await self.mass_purge(to_delete)
        else:
            await self.slow_deletion(to_delete)
        reply = await self.bot.say("♻ **I've successfully pruned** ***`{}`*** **messages containing** ***`{}`*** ♻".format(len(to_delete), text))
        await asyncio.sleep(2)
        await self.bot.delete_message(reply)

    @cleanup.command(pass_context=True, no_pm=True)
    async def user(self, ctx, user: discord.Member, number: int):
        """Deletes last X messages from specified user.

        Examples:
        cleanup user @\u200bfag 2
        cleanup user gayboy 6
        cleanu @Paradox 100"""

        channel = ctx.message.channel
        author = ctx.message.author
        server = author.server
        is_bot = self.bot.user.bot
        has_permissions = channel.permissions_for(server.me).manage_messages

        def check(m):
            if m.author == user:
                return True
            elif m == ctx.message:
                return True
            else:
                return False

        to_delete = [ctx.message]

        if not has_permissions:
            await self.bot.say("**Congratulations,**\n***You played yourself.***:tada:\n**I do not have** ***`manage_messages`*** **permissions.**")
            return

        tries_left = 5
        tmp = ctx.message

        while tries_left and len(to_delete) - 1 < number:
            async for message in self.bot.logs_from(channel, limit=100,
                                                    before=tmp):
                if len(to_delete) - 1 < number and check(message):
                    to_delete.append(message)
                tmp = message
            tries_left -= 1

        logger.info("{}({}) deleted {} messages "
                    " made by {}({}) in channel {}"
                    "".format(author.name, author.id, len(to_delete),
                              user.name, user.id, channel.name))

        if is_bot:
            await self.mass_purge(to_delete)
        else:
            await self.slow_deletion(to_delete)
        reply = await self.bot.say("**I've successfully pruned** ***`{}`*** **of** ***`{} 's`*** **messages** <:check:314349398811475968>".format(number, user.name))
        await asyncio.sleep(3)
        await self.bot.delete_message(reply)
    @cleanup.command(pass_context=True, no_pm=True)
    async def after(self, ctx, message_id : int):
        """Deletes all messages after specified message

        To get a message id, enable developer mode in Discord's
        settings, 'appearance' tab. Then right click a message
        and copy its id.

        This command only works on bots running as bot accounts.
        alias is cleana
        """

        channel = ctx.message.channel
        author = ctx.message.author
        server = channel.server
        is_bot = self.bot.user.bot
        has_permissions = channel.permissions_for(server.me).manage_messages

        if not is_bot:
            await self.bot.say("This command can only be used on bots with "
                               "bot accounts.")
            return

        to_delete = []

        after = await self.bot.get_message(channel, message_id)

        if not has_permissions:
            await self.bot.say("**Congratulations,**\n***You played yourself.***:tada:\n**I do not have** ***`manage_messages`*** **permissions.**")
            return
        elif not after:
            await self.bot.say("Message not found.")
            return

        async for message in self.bot.logs_from(channel, limit=2000,
                                                after=after):
            to_delete.append(message)

        logger.info("{}({}) deleted {} messages in channel {}"
                    "".format(author.name, author.id,
                              len(to_delete), channel.name))

        await self.mass_purge(to_delete)

    @cleanup.command(pass_context=True, no_pm=True)
    async def messages(self, ctx, number: int):
        """Deletes last X messages.

        Example:
        cleanup messages 26
        Cleanu 10"""

        channel = ctx.message.channel
        author = ctx.message.author
        server = author.server
        is_bot = self.bot.user.bot
        has_permissions = channel.permissions_for(server.me).manage_messages

        to_delete = []

        if not has_permissions:
            await self.bot.say("**Congratulations,**\n***You played yourself.***:tada:\n**I do not have** ***`manage_messages`*** **permissions.**")
            return

        async for message in self.bot.logs_from(channel, limit=number+1):
            to_delete.append(message)

        logger.info("{}({}) deleted {} messages in channel {}"
                    "".format(author.name, author.id,
                              number, channel.name))

        if is_bot:
            await self.mass_purge(to_delete)
        else:
            await self.slow_deletion(to_delete)
        reply = await self.bot.say('***Successfully pruned `{}` messages. :ok_hand:<:check:314349398811475968>***'.format(number))
        await asyncio.sleep(2)
        await self.bot.delete_message(reply)

    @cleanup.command(pass_context=True, no_pm=True, name='bot')
    async def cleanup_bot(self, ctx, number: int):
        """Cleans up command messages and messages from the bot
        an alias is prune"""

        channel = ctx.message.channel
        author = ctx.message.author
        server = channel.server
        is_bot = self.bot.user.bot
        has_permissions = channel.permissions_for(server.me).manage_messages

        prefixes = self.bot.command_prefix
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        elif callable(prefixes):
            if asyncio.iscoroutine(prefixes):
                await self.bot.say('Coroutine prefixes not yet implemented.')
                return
            prefixes = prefixes(self.bot, ctx.message)

        # In case some idiot sets a null prefix
        if '' in prefixes:
            prefixes.pop('')

        def check(m):
            if m.author.id == self.bot.user.id:
                return True
            elif m == ctx.message:
                return True
            p = discord.utils.find(m.content.startswith, prefixes)
            if p and len(p) > 0:
                return m.content[len(p):].startswith(tuple(self.bot.commands))
            return False

        to_delete = [ctx.message]

        if not has_permissions:
            await self.bot.say("**Congratulations,**\n***You played yourself.***:tada:\n**I do not have** ***`manage_messages`*** **permissions.**")
            return

        tries_left = 5
        tmp = ctx.message

        while tries_left and len(to_delete) - 1 < number:
            async for message in self.bot.logs_from(channel, limit=100,
                                                    before=tmp):
                if len(to_delete) - 1 < number and check(message):
                    to_delete.append(message)
                tmp = message
            tries_left -= 1

        logger.info("{}({}) deleted {} "
                    " command messages in channel {}"
                    "".format(author.name, author.id, len(to_delete),
                              channel.name))

        if is_bot:
            await self.mass_purge(to_delete)
        else:
            await self.slow_deletion(to_delete)

    @cleanup.command(pass_context=True, name='self')
    async def cleanup_self(self, ctx, number: int, match_pattern: str = None):
        """Cleans up messages owned by the bot.

        By default, all messages are cleaned. If a third argument is specified,
        it is used for pattern matching: If it begins with r( and ends with ),
        then it is interpreted as a regex, and messages that match it are
        deleted. Otherwise, it is used in a simple substring test.

        Some helpful regex flags to include in your pattern:
        Dots match newlines: (?s); Ignore case: (?i); Both: (?si)
        """
        channel = ctx.message.channel
        author = ctx.message.author
        is_bot = self.bot.user.bot

        # You can always delete your own messages, this is needed to purge
        can_mass_purge = False
        if type(author) is discord.Member:
            me = channel.server.me
            can_mass_purge = channel.permissions_for(me).manage_messages

        use_re = (match_pattern and match_pattern.startswith('r(') and
                  match_pattern.endswith(')'))

        if use_re:
            match_pattern = match_pattern[1:]  # strip 'r'
            match_re = re.compile(match_pattern)

            def content_match(c):
                return bool(match_re.match(c))
        elif match_pattern:
            def content_match(c):
                return match_pattern in c
        else:
            def content_match(_):
                return True

        def check(m):
            if m.author.id != self.bot.user.id:
                return False
            elif content_match(m.content):
                return True
            return False

        to_delete = []
        # Selfbot convenience, delete trigger message
        if author == self.bot.user:
            to_delete.append(ctx.message)
            number += 1

        tries_left = 5
        tmp = ctx.message

        while tries_left and len(to_delete) < number:
            async for message in self.bot.logs_from(channel, limit=100,
                                                    before=tmp):
                if len(to_delete) < number and check(message):
                    to_delete.append(message)
                tmp = message
            tries_left -= 1

        if channel.name:
            channel_name = 'channel ' + channel.name
        else:
            channel_name = str(channel)

        logger.info("{}({}) deleted {} messages "
                    "sent by the bot in {}"
                    "".format(author.name, author.id, len(to_delete),
                              channel_name))

        if is_bot and can_mass_purge:
            await self.mass_purge(to_delete)
        else:
            await self.slow_deletion(to_delete)

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def reason(self, ctx, case, *, reason : str=""):
        """Lets you specify a reason for mod-log's cases
        Defaults to last case assigned to yourself, if available."""
        author = ctx.message.author
        server = author.server
        try:
            case = int(case)
            if not reason:
                await send_cmd_help(ctx)
                return
        except:
            if reason:
                reason = "{} {}".format(case, reason)
            else:
                reason = case
            case = self.last_case[server.id].get(author.id)
            if case is None:
                await send_cmd_help(ctx)
                return
        try:
            await self.update_case(server, case=case, mod=author,
                                   reason=reason)
        except UnauthorizedCaseEdit:
            await self.bot.say("That case is not yours.🤔")
        except KeyError:
            await self.bot.say("That case doesn't exist.🤔")
        except NoModLogChannel:
            await self.bot.say("There's no mod-log channel set.🤔")
        except CaseMessageNotFound:
            await self.bot.say("Couldn't find the case's message.🤔")
        else:
            await self.bot.say("***Case `#{}` Updated.***:thumbsup: ".format(case))

    @commands.group(pass_context=True)
    @checks.is_owner()
    async def blacklist(self, ctx):
        """Bans user from using the bot"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @blacklist.command(name="add")
    async def _blacklist_add(self, user: discord.Member):
        """Adds user to bot's blacklist"""
        if user.id not in self.blacklist_list:
            self.blacklist_list.append(user.id)
            dataIO.save_json("data/mod/blacklist.json", self.blacklist_list)
            await self.bot.say("User has been added to blacklist.")
        else:
            await self.bot.say("User is already blacklisted.")

    @blacklist.command(name="remove")
    async def _blacklist_remove(self, user: discord.Member):
        """Removes user from bot's blacklist"""
        if user.id in self.blacklist_list:
            self.blacklist_list.remove(user.id)
            dataIO.save_json("data/mod/blacklist.json", self.blacklist_list)
            await self.bot.say("User has been removed from blacklist.")
        else:
            await self.bot.say("User is not in blacklist.")

    @blacklist.command(name="clear")
    async def _blacklist_clear(self):
        """Clears the blacklist"""
        self.blacklist_list = []
        dataIO.save_json("data/mod/blacklist.json", self.blacklist_list)
        await self.bot.say("Blacklist is now empty.")

    @commands.group(pass_context=True)
    @checks.is_owner()
    async def whitelist(self, ctx):
        """Users who will be able to use the bot"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @whitelist.command(name="add")
    async def _whitelist_add(self, user: discord.Member):
        """Adds user to bot's whitelist"""
        if user.id not in self.whitelist_list:
            if not self.whitelist_list:
                msg = "\nAll users not in whitelist will be ignored (owner, admins and mods excluded)"
            else:
                msg = ""
            self.whitelist_list.append(user.id)
            dataIO.save_json("data/mod/whitelist.json", self.whitelist_list)
            await self.bot.say("User has been added to whitelist." + msg)
        else:
            await self.bot.say("User is already whitelisted.")

    @whitelist.command(name="remove")
    async def _whitelist_remove(self, user: discord.Member):
        """Removes user from bot's whitelist"""
        if user.id in self.whitelist_list:
            self.whitelist_list.remove(user.id)
            dataIO.save_json("data/mod/whitelist.json", self.whitelist_list)
            await self.bot.say("User has been removed from whitelist.")
        else:
            await self.bot.say("User is not in whitelist.")

    @whitelist.command(name="clear")
    async def _whitelist_clear(self):
        """Clears the whitelist"""
        self.whitelist_list = []
        dataIO.save_json("data/mod/whitelist.json", self.whitelist_list)
        await self.bot.say("Whitelist is now empty.")

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_channels=True)
    async def ignore(self, ctx):
        """Adds servers/channels to ignorelist"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            await self.bot.say(self.count_ignored())

    @ignore.command(name="channel", pass_context=True)
    async def ignore_channel(self, ctx, channel: discord.Channel=None):
        """Ignores channel
        Defaults to current one"""
        current_ch = ctx.message.channel
        if not channel:
            if current_ch.id not in self.ignore_list["CHANNELS"]:
                self.ignore_list["CHANNELS"].append(current_ch.id)
                dataIO.save_json("data/mod/ignorelist.json", self.ignore_list)
                await self.bot.say("Channel added to ignore list.")
            else:
                await self.bot.say("Channel already in ignore list.")
        else:
            if channel.id not in self.ignore_list["CHANNELS"]:
                self.ignore_list["CHANNELS"].append(channel.id)
                dataIO.save_json("data/mod/ignorelist.json", self.ignore_list)
                await self.bot.say("Channel added to ignore list.")
            else:
                await self.bot.say("Channel already in ignore list.")

    @ignore.command(name="server", pass_context=True)
    async def ignore_server(self, ctx):
        """Ignores current server"""
        server = ctx.message.server
        if server.id not in self.ignore_list["SERVERS"]:
            self.ignore_list["SERVERS"].append(server.id)
            dataIO.save_json("data/mod/ignorelist.json", self.ignore_list)
            await self.bot.say("This server has been added to the ignore list.")
        else:
            await self.bot.say("This server is already being ignored.")

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_channels=True)
    async def unignore(self, ctx):
        """Removes servers/channels from ignorelist"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            await self.bot.say(self.count_ignored())

    @unignore.command(name="channel", pass_context=True)
    async def unignore_channel(self, ctx, channel: discord.Channel=None):
        """Removes channel from ignore list
        Defaults to current one"""
        current_ch = ctx.message.channel
        if not channel:
            if current_ch.id in self.ignore_list["CHANNELS"]:
                self.ignore_list["CHANNELS"].remove(current_ch.id)
                dataIO.save_json("data/mod/ignorelist.json", self.ignore_list)
                await self.bot.say("This channel has been removed from the ignore list.")
            else:
                await self.bot.say("This channel is not in the ignore list.")
        else:
            if channel.id in self.ignore_list["CHANNELS"]:
                self.ignore_list["CHANNELS"].remove(channel.id)
                dataIO.save_json("data/mod/ignorelist.json", self.ignore_list)
                await self.bot.say("Channel removed from ignore list.")
            else:
                await self.bot.say("That channel is not in the ignore list.")

    @unignore.command(name="server", pass_context=True)
    async def unignore_server(self, ctx):
        """Removes current server from ignore list"""
        server = ctx.message.server
        if server.id in self.ignore_list["SERVERS"]:
            self.ignore_list["SERVERS"].remove(server.id)
            dataIO.save_json("data/mod/ignorelist.json", self.ignore_list)
            await self.bot.say("This server has been removed from the ignore list.")
        else:
            await self.bot.say("This server is not in the ignore list.")

    def count_ignored(self):
        msg = "```Currently ignoring:\n"
        msg += str(len(self.ignore_list["CHANNELS"])) + " channels\n"
        msg += str(len(self.ignore_list["SERVERS"])) + " servers\n```\n"
        return msg

    @commands.group(name="filter", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def _filter(self, ctx):
        """Adds/removes words from filter
        Use double quotes to add/remove sentences
        Using this command with no subcommands will send
        the list of the server's filtered words."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            server = ctx.message.server
            author = ctx.message.author
            msg = ""
            if server.id in self.filter.keys():
                if self.filter[server.id] != []:
                    word_list = self.filter[server.id]
                    for w in word_list:
                        msg += '"' + w + '" '
                    await self.bot.send_message(author, "Words filtered in this server: " + msg)

    @_filter.command(name="add", pass_context=True)
    async def filter_add(self, ctx, *words: str):
        """Adds words to the filter
        Use double quotes to add sentences
        Examples:
        filter add word1 word2 word3
        filter add \"This is a sentence\""""
        if words == ():
            await send_cmd_help(ctx)
            return
        server = ctx.message.server
        added = 0
        if server.id not in self.filter.keys():
            self.filter[server.id] = []
        for w in words:
            if w.lower() not in self.filter[server.id] and w != "":
                self.filter[server.id].append(w.lower())
                added += 1
        if added:
            dataIO.save_json("data/mod/filter.json", self.filter)
            await self.bot.say("Words added to filter.")
        else:
            await self.bot.say("Words already in the filter.")

    @_filter.command(name="remove", pass_context=True)
    async def filter_remove(self, ctx, *words: str):
        """Remove words from the filter
        Use double quotes to remove sentences
        Examples:
        filter remove word1 word2 word3
        filter remove \"This is a sentence\""""
        if words == ():
            await send_cmd_help(ctx)
            return
        server = ctx.message.server
        removed = 0
        if server.id not in self.filter.keys():
            await self.bot.say("There are no filtered words in this server.")
            return
        for w in words:
            if w.lower() in self.filter[server.id]:
                self.filter[server.id].remove(w.lower())
                removed += 1
        if removed:
            dataIO.save_json("data/mod/filter.json", self.filter)
            await self.bot.say("Words removed from filter.")
        else:
            await self.bot.say("Those words weren't in the filter.")

    @commands.group(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def editrole(self, ctx):
        """Edits A role & it's settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @editrole.command(aliases=["color"], pass_context=True)
    async def colour(self, ctx, role: discord.Role, value: discord.Colour):
        """Edits a role's colour
        Use double quotes if the role contains spaces.
        Colour must be in hexadecimal format.
        \"http://www.w3schools.com/colors/colors_picker.asp\"
        Examples:
        !editrole colour \"gay\" #ff0000
        !editrole colour Test #ff9900"""
        author = ctx.message.author
        try:
            await self.bot.edit_role(ctx.message.server, role, color=value)
            logger.info("{}({}) changed the colour of role '{}'".format(
                author.name, author.id, role.name))
            await self.bot.say("***Successfully***  **Changed the colour of `{}` To `{}`:thumbsup:**".format(role.name, value))
        except discord.Forbidden:
            await self.bot.say(":bangbang: **I need permissions to manage roles first.** :x:")
        except Exception as e:
            print(e)
            await self.bot.say(":bangbang: **Something went wrong.** :x:")

    @editrole.command(name="position", aliases=["pos"], pass_context=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def edit_role_position(self, ctx, role: discord.Role, position : int):
        """Edits the roles position in the servers role hierachy
        The way this works the bot has to be higher than the role you're moving
        It also needs manage roles
        Where 1 = the lowest area aka the bottom next to @everyone because you can't do 0 cause fuck logic idk """
        server = ctx.message.server
        if role.name is "@everyone":
            message = "😐 I can't move the servers default role :face_palm:"
            return
        if position is "0":
            await self.bot.say("you can't do 0 cause fuck logic idk Probs cause 0 is under the server default role aka `@everyone`")
            return
        try:
            await self.bot.move_role(server, role, position)
            message = ":bangbang: I've **successfully** moved the role `{}` :thumbsup:".format(role.name)
            await self.bot.say(message)
        except discord.Forbidden:
            await self.bot.say(":x: ***I have no permission to move members.***😐")
        except discord.HTTPException:
            await self.bot.say("😐 **Moving the role failed, or you are of too low rank to move the role.** 😐")

    @editrole.command(name="name", pass_context=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def edit_role_name(self, ctx, role: discord.Role, name: str):
        """Edits a role's name
        Use double quotes if the role or the name contain spaces.
        Examples:
        !editrole name \"Tdangerous\" gay"""
        if name == "":
            await self.bot.say(":bangbang: **Name cannot be empty.**")
            return
        try:
            author = ctx.message.author
            old_name = role.name  # probably not necessary?
            await self.bot.edit_role(ctx.message.server, role, name=name)
            logger.info("{}({}) changed the name of role '{}' to '{}'".format(
                author.name, author.id, old_name, name))
            await self.bot.say("***Successfully***  **Changed the Name of `{}` To `{}`:thumbsup:**".format(role.name, name))
        except discord.Forbidden:
            await self.bot.say(":bangbang: **I need permissions to manage roles first.** :x:")
        except Exception as e:
            print(e)
            await self.bot.say(":bangbang: **Something went wrong.** :x:")


    @commands.command()
    async def names(self, user : discord.Member):
        """Show previous names/nicknames of a user"""
        server = user.server
        names = self.past_names[user.id] if user.id in self.past_names else None
        try:
            nicks = self.past_nicknames[server.id][user.id]
            nicks = [escape_mass_mentions(nick) for nick in nicks]
        except:
            nicks = None
        msg = ""
        if names:
            names = [escape_mass_mentions(name) for name in names]
            msg += "**Past 20 names**:\n"
            msg += ", ".join(names)
        if nicks:
            if msg:
                msg += "\n\n"
            msg += "**Past 20 nicknames**:\n"
            msg += ", ".join(nicks)
        if msg:
            await self.bot.say(msg)
        else:
            await self.bot.say("That user doesn't have any recorded name or "
                               "nickname change.")

    async def mass_purge(self, messages):
        while messages:
            if len(messages) > 1:
                await self.bot.delete_messages(messages[:100])
                messages = messages[100:]
            else:
                await self.bot.delete_message(messages[0])
                messages = []
            await asyncio.sleep(1.5)

    async def slow_deletion(self, messages):
        for message in messages:
            try:
                await self.bot.delete_message(message)
            except:
                pass

    def is_admin_or_superior(self, obj):
        if isinstance(obj, discord.Message):
            user = obj.author
        elif isinstance(obj, discord.Member):
            user = obj
        elif isinstance(obj, discord.Role):
            pass
        else:
            raise TypeError('Only messages, members or roles may be passed')

        server = obj.server
        admin_role = settings.get_server_admin(server)

        if isinstance(obj, discord.Role):
            return obj.name == admin_role

        if user.id == settings.owner:
            return True
        elif discord.utils.get(user.roles, name=admin_role):
            return True
        else:
            return False

    def is_mod_or_superior(self, obj):
        if isinstance(obj, discord.Message):
            user = obj.author
        elif isinstance(obj, discord.Member):
            user = obj
        elif isinstance(obj, discord.Role):
            pass
        else:
            raise TypeError('Only messages, members or roles may be passed')

        server = obj.server
        admin_role = settings.get_server_admin(server)
        mod_role = settings.get_server_mod(server)

        if isinstance(obj, discord.Role):
            return obj.name in [admin_role, mod_role]

        if user.id == settings.owner:
            return True
        elif discord.utils.get(user.roles, name=admin_role):
            return True
        elif discord.utils.get(user.roles, name=mod_role):
            return True
        else:
            return False

    async def new_case(self, server, *, action, mod=None, user, reason=None, until=None, channel=None):
        mod_channel = server.get_channel(self.settings[server.id]["mod-log"])
        if mod_channel is None:
            return

        if server.id not in self.cases:
            self.cases[server.id] = {}

        case_n = len(self.cases[server.id]) + 1

        case = {
            "case"         : case_n,
            "created"      : datetime.utcnow().timestamp(),
            "modified"     : None,
            "action"       : action,
            "channel"      : channel.id if channel else None,
            "user"         : user.name,
            "user_id"      : user.id,
            "reason"       : reason,
            "moderator"    : mod.name if mod is not None else None,
            "moderator_id" : mod.id if mod is not None else None,
            "amended_by"   : None,
            "amended_id"   : None,
            "message"      : None,
            "until"        : None,
        }

        case_msg = self.format_case_msg(case)

        try:
            msg = await self.bot.send_message(mod_channel, case_msg)
            case["message"] = msg.id
        except:
            pass

        self.cases[server.id][str(case_n)] = case

        if mod:
            self.last_case[server.id][mod.id] = case_n

        dataIO.save_json("data/mod/modlog.json", self.cases)

    async def update_case(self, server, *, case, mod=None, reason=None,
                          until=False):
        channel = server.get_channel(self.settings[server.id]["mod-log"])
        if channel is None:
            raise NoModLogChannel()

        case = str(case)
        case = self.cases[server.id][case]

        if case["moderator_id"] is not None:
            if case["moderator_id"] != mod.id:
                if self.is_admin_or_superior(mod):
                    case["amended_by"] = mod.name
                    case["amended_id"] = mod.id
                else:
                    raise UnauthorizedCaseEdit()
        else:
            case["moderator"] = mod.name
            case["moderator_id"] = mod.id

        if case["reason"]:  # Existing reason
            case["modified"] = datetime.utcnow().timestamp()
        case["reason"] = reason

        if until is not False:
            case["until"] = until

        case_msg = self.format_case_msg(case)

        dataIO.save_json("data/mod/modlog.json", self.cases)

        msg = await self.bot.get_message(channel, case["message"])
        if msg:
            await self.bot.edit_message(msg, case_msg)
        else:
            raise CaseMessageNotFound()

    def format_case_msg(self, case):
        tmp = case.copy()
        if case["reason"] is None:
            tmp["reason"] = "***Type  `[p]reason %i <reason>` to add it***" % tmp["case"]
        if case["moderator"] is None:
            tmp["moderator"] = "Unknown"
            tmp["moderator_id"] = "Nobody has claimed responsibility yet"
        if case["action"] in ACTIONS_REPR:
            tmp["action"] = ' '.join(ACTIONS_REPR[tmp["action"]])

        channel = case.get("channel")
        if channel:
            channel = self.bot.get_channel(channel)
            tmp["action"] += ' in ' + channel.mention

        case_msg = (
            "**Case #{case}** | {action}\n"
            "**User:** {user} ***`({user_id})`***\n"
            "**Moderator:** {moderator} ***`({moderator_id})`***\n"
        ).format(**tmp)

        created = case.get('created')
        until = case.get('until')
        if created and until:
            start = datetime.fromtimestamp(created)
            end = datetime.fromtimestamp(until)
            end_fmt = end.strftime('%Y-%m-%d %H:%M:%S UTC')
            duration = end - start
            dur_fmt = strfdelta(duration)
            case_msg += ("**Until:** {}\n"
                         "**Duration:** {}\n").format(end_fmt, dur_fmt)

        amended = case.get('amended_by')
        if amended:
            amended_id = case.get('amended_id')
            case_msg += "**Amended by:** %s (%s)\n" % (amended, amended_id)

        modified = case.get('modified')
        if modified:
            modified = datetime.fromtimestamp(modified)
            modified_fmt = modified.strftime('%Y-%m-%d %H:%M:%S UTC')
            case_msg += "**Last modified:** %s\n" % modified_fmt

        case_msg += "**Reason:** %s\n" % tmp["reason"]

        return case_msg

    async def check_filter(self, message):
        server = message.server
        if server.id in self.filter.keys():
            for w in self.filter[server.id]:
                if w in message.content.lower():
                    try:
                        await self.bot.delete_message(message)
                        logger.info("Message deleted in server {}."
                                    "Filtered: {}"
                                    "".format(server.id, w))
                        return True
                    except:
                        pass
        return False

    async def check_duplicates(self, message):
        server = message.server
        author = message.author
        if server.id not in self.settings:
            return False
        if self.settings[server.id]["delete_repeats"]:
            if not message.content:
                return False
            self.cache[author].append(message)
            msgs = self.cache[author]
            if len(msgs) == 3 and \
                    msgs[0].content == msgs[1].content == msgs[2].content:
                try:
                    await self.bot.delete_message(message)
                    return True
                except:
                    pass
        return False

    async def check_mention_spam(self, message):
        server = message.server
        author = message.author
        if server.id not in self.settings:
            return False
        if self.settings[server.id]["ban_mention_spam"]:
            max_mentions = self.settings[server.id]["ban_mention_spam"]
            mentions = set(message.mentions)
            if len(mentions) >= max_mentions:
                try:
                    self.temp_cache.add(author, server, "BAN")
                    await self.bot.ban(author, 1)
                except:
                    logger.info("Failed to ban member for mention spam in "
                                "server {}".format(server.id))
                else:
                    await self.new_case(server,
                                        action="BAN",
                                        mod=server.me,
                                        user=author,
                                        reason="Mention spam (Autoban)")
                    return True
        return False

    async def on_command(self, command, ctx):
        """Currently used for:
            * delete delay"""
        server = ctx.message.server
        message = ctx.message
        try:
            delay = self.settings[server.id]["delete_delay"]
        except KeyError:
            # We have no delay set
            return
        except AttributeError:
            # DM
            return

        if delay == -1:
            return

        async def _delete_helper(bot, message):
            try:
                await bot.delete_message(message)
                logger.debug("Deleted command msg {}".format(message.id))
            except discord.errors.Forbidden:
                # Do not have delete permissions
                logger.debug("Wanted to delete mid {} but no"
                             " permissions".format(message.id))

        await asyncio.sleep(delay)
        await _delete_helper(self.bot, message)

    async def on_message(self, message):
        if message.channel.is_private or self.bot.user == message.author \
         or not isinstance(message.author, discord.Member):
            return
        elif self.is_mod_or_superior(message):
            return
        deleted = await self.check_filter(message)
        if not deleted:
            deleted = await self.check_duplicates(message)
        if not deleted:
            deleted = await self.check_mention_spam(message)

    async def on_member_ban(self, member):
        server = member.server
        if not self.temp_cache.check(member, server, "BAN"):
            await self.new_case(server,
                                user=member,
                                action="BAN")

    async def on_member_unban(self, server, user):
        if not self.temp_cache.check(user, server, "UNBAN"):
            await self.new_case(server,
                                user=user,
                                action="UNBAN")

    async def check_names(self, before, after):
        if before.name != after.name:
            if before.id not in self.past_names:
                self.past_names[before.id] = [after.name]
            else:
                if after.name not in self.past_names[before.id]:
                    names = deque(self.past_names[before.id], maxlen=20)
                    names.append(after.name)
                    self.past_names[before.id] = list(names)
            dataIO.save_json("data/mod/past_names.json", self.past_names)

        if before.nick != after.nick and after.nick is not None:
            server = before.server
            if server.id not in self.past_nicknames:
                self.past_nicknames[server.id] = {}
            if before.id in self.past_nicknames[server.id]:
                nicks = deque(self.past_nicknames[server.id][before.id],
                              maxlen=20)
            else:
                nicks = []
            if after.nick not in nicks:
                nicks.append(after.nick)
                self.past_nicknames[server.id][before.id] = list(nicks)
                dataIO.save_json("data/mod/past_nicknames.json",
                                 self.past_nicknames)

    def are_overwrites_empty(self, overwrites):
        """There is currently no cleaner way to check if a
        PermissionOverwrite object is empty"""
        original = [p for p in iter(overwrites)]
        empty = [p for p in iter(discord.PermissionOverwrite())]
        return original == empty


def strfdelta(delta):
    s = []
    if delta.days:
        ds = '%i day' % delta.days
        if delta.days > 1:
            ds += 's'
        s.append(ds)
    hrs, rem = divmod(delta.seconds, 60*60)
    if hrs:
        hs = '%i hr' % hrs
        if hrs > 1:
            hs += 's'
        s.append(hs)
    mins, secs = divmod(rem, 60)
    if mins:
        s.append('%i min' % mins)
    if secs:
        s.append('%i sec' % secs)
    return ' '.join(s)

    async def get_bot_api_response(self, url, key, serverid):
        data = {"guild_id": serverid, "permissions": 0, "authorize": True}
        data = json.dumps(data).encode('utf-8')
        headers = {'authorization': key, 'content-type': 'application/json'}
        async with self.session.post(url, data=data, headers=headers) as r:
            status = r.status
        return status

    def are_overwrites_empty(self, overwrites):
        """There is currently no cleaner way to check if a
        PermissionOverwrite object is empty"""
        original = [p for p in iter(overwrites)]
        empty = [p for p in iter(discord.PermissionOverwrite())]
        return original == empty


def check_folders():
    folders = ("data", "data/mod/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)





def check_folders():
    folders = ("data", "data/mod/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

    if not os.path.exists("data/autoapprove"):
        print("Creating data/autoapprove folder...")
        os.makedirs("data/autoapprove")


def check_files():
    ignore_list = {"SERVERS": [], "CHANNELS": []}

    files = {
        "blacklist.json"      : [],
        "whitelist.json"      : [],
        "ignorelist.json"     : ignore_list,
        "filter.json"         : {},
        "past_names.json"     : {},
        "past_nicknames.json" : {},
        "settings.json"       : {},
        "modlog.json"         : {},
        "perms_cache.json"    : {}
    }

    for filename, value in files.items():
        if not os.path.isfile("data/mod/{}".format(filename)):
            print("Creating empty {}".format(filename))
            dataIO.save_json("data/mod/{}".format(filename), value)

    if not os.path.exists('data/admin/settings.json'):
        try:
            os.mkdir('data/admin')
        except FileExistsError:
            pass
        else:
            dataIO.save_json('data/admin/settings.json', {})

    enabled = {}

    f = "data/autoapprove/enabled.json"
    if not fileIO(f, "check"):
        print("Creating default autoapprove's enabled.json...")
        fileIO(f, "save", enabled)



def setup(bot):
    global logger
    check_folders()
    check_files()
    logger = logging.getLogger("mod")
    # Prevents the logger from being loaded again in case of module reload
    if logger.level == 0:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(
            filename='data/mod/mod.log', encoding='utf-8', mode='a')
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(message)s', datefmt="[%d/%m/%Y %H:%M]"))
        logger.addHandler(handler)
    n = Mod(bot)
    bot.add_listener(n.check_names, "on_member_update")
    bot.add_cog(n)
