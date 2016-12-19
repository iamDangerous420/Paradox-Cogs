import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
from cogs.utils.chat_formatting import box, pagify
from __main__ import settings, send_cmd_help
from copy import deepcopy
from cogs.utils.dataIO import fileIO
from collections import deque, defaultdict
from cogs.utils.chat_formatting import escape_mass_mentions, box
import os
import re
import logging
import asyncio
import json
import aiohttp
import urllib.parse as up

log = logging.getLogger("red.admin")

default_settings = {
    "ban_mention_spam" : False,
    "delete_repeats"   : False,
    "mod-log"          : None
                   }


class ModError(Exception):
    pass


class UnauthorizedCaseEdit(ModError):
    pass


class CaseMessageNotFound(ModError):
    pass


class NoModLogChannel(ModError):
    pass


class Mod:
    """Moderation tools."""

    def __init__(self, bot):
        self.bot = bot
        self.whitelist_list = dataIO.load_json("data/mod/whitelist.json")
        self.blacklist_list = dataIO.load_json("data/mod/blacklist.json")
        self.ignore_list = dataIO.load_json("data/mod/ignorelist.json")
        self.filter = dataIO.load_json("data/mod/filter.json")
        self.past_names = dataIO.load_json("data/mod/past_names.json")
        self._settings = dataIO.load_json('data/admin/settings.json')
        self._settable_roles = self._settings.get("ROLES", {})
        self.past_nicknames = dataIO.load_json("data/mod/past_nicknames.json")
        settings = dataIO.load_json("data/mod/settings.json")
        self.settings = defaultdict(lambda: default_settings.copy(), settings)
        self.cache = defaultdict(lambda: deque(maxlen=3))
        self.cases = dataIO.load_json("data/mod/modlog.json")
        self.last_case = defaultdict(dict)
        self._tmp_banned_cache = []
        perms_cache = dataIO.load_json("data/mod/perms_cache.json")
        self._perms_cache = defaultdict(dict, perms_cache)
        self.base_api_url = "https://discordapp.com/api/oauth2/authorize?"
        self.enabled = fileIO('data/autoapprove/enabled.json', 'load')
        self.session = aiohttp.ClientSession()
        self.location = 'data/antilink/settings.json'
        self.json = dataIO.load_json(self.location)
        self.regex = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.gg|discordapp\.com\/invite)\b([-a-zA-Z0-9/]*)>?")
        self.regex_discordme = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.me\/)\b([-a-zA-Z0-9/]*)>?")

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


    @commands.group(pass_context=True, no_pm=True)
    async def antilink(self, ctx):
        """Manages the settings for antilink."""
        serverid = ctx.message.server.id
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
        if serverid not in self.json:
            self.json[serverid] = {'toggle': False, 'message': '', 'dm': False}

    @antilink.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggle(self, ctx):
        """Enable/disables antilink in the server"""
        serverid = ctx.message.server.id
        if self.json[serverid]['toggle'] is True:
            self.json[serverid]['toggle'] = False
            await self.bot.say(':no_good: ***Anti Invite DISABLED*** :x: ')
        elif self.json[serverid]['toggle'] is False:
            self.json[serverid]['toggle'] = True
            await self.bot.reply(':bangbang: ***Antiinvite SET*** :bangbang: :punch:')
        dataIO.save_json(self.location, self.json)

    @antilink.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def message(self, ctx, *, text):
        """Set the message for when the user sends a illegal discord link"""
        serverid = ctx.message.server.id
        self.json[serverid]['message'] = text
        dataIO.save_json(self.location, self.json)
        await self.bot.say(':heavy_check_mark: ***Message Successfully set*** :thumbsup:')
        if self.json[serverid]['dm'] is False:
            await self.bot.say(':bangbang:**Please Remember** Direct Messages on removal is **disabled!**\nEnable it with ==> ``antilink toggledm``')

    @antilink.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggledm(self, ctx):
        serverid = ctx.message.server.id
        if self.json[serverid]['dm'] is False:
            self.json[serverid]['dm'] = True
            await self.bot.say('**Enabled DMs on removal of invite links** :thumbsup:')
        elif self.json[serverid]['dm'] is True:
            self.json[serverid]['dm'] = False
            await self.bot.say('**Disabled DMs on removal of invite links** :thumbsup:')
        dataIO.save_json(self.location, self.json)

    async def _new_message(self, message):
        """Finds the message and checks it for regex"""
        user = message.author
        if message.server is None:
            pass
        if message.server.id in self.json:
            if self.json[message.server.id]['toggle'] is True:
                if self.regex.search(message.content) is not None or self.regex_discordme.search(message.content) is not None:
                    roles = [r.name for r in user.roles]
                    bot_admin = settings.get_server_admin(message.server)
                    bot_mod = settings.get_server_mod(message.server)
                    if user.id == settings.owner:
                        pass
                    elif bot_admin in roles:
                        pass
                    elif bot_mod in roles:
                        pass
                    elif user.permissions_in(message.channel).manage_messages is True:
                        pass
                    else:
                        asyncio.sleep(0.5)
                        await self.bot.delete_message(message)
                        if self.json[message.server.id]['dm'] is True:
                            await self.bot.send_message(message.author, self.json[message.server.id]['message'])

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def addrole(self, ctx, rolename, user: discord.Member=None):
        """Adds a role to a user, defaults to author
        Role name must be in quotes if there are spaces."""
        author = ctx.message.author
        channel = ctx.message.channel
        server = ctx.message.server

        if user is None:
            user = author

        role = self._role_from_string(server, rolename)

        if role is None:
            await self.bot.say(':no_good: Cannot find the role {} :thinking:'.format(rolename))
            return

        if not channel.permissions_for(server.me).manage_roles:
            await self.bot.say('I don\'t have manage_roles. :| ')
            return

        await self.bot.add_roles(user, role)
        await self.bot.say(':bangbang:  **Succesfully** Added role ***{}***  to ***{}*** :thumbsup:'.format(role.name, user.name))

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_roles=True)
    async def createrole(self, ctx, *, rolename: str = None):
        """Create a role using the bot The role will be listed at the bottom of role list."""
        if rolename is None:
            await self.bot.say("How am i supposed to **create a role** with no ***role name*** :thinking: :face_palm:")
            return
        server = ctx.message.server
        name = ''.join(rolename)
        await self.bot.create_role(server, name= '{}'.format(name))
        message = ":bangbang: I've **Succesfully** created the role `{}` :thumbsup:".format(name)
        await self.bot.say(message)

    @commands.command(pass_context=True)
    async def deleterole(self, ctx, rolename):
        """Deletes an existing role. Bot must be above the role "Role hierachy" mate"""
        channel = ctx.message.channel
        server = ctx.message.server

        role = self._role_from_string(server, rolename)

        if role is None:
            await self.bot.say(':no_good: That role cannot be found. :no_good:')
            return

        await self.bot.delete_role(server,role)
        message = " :call_me: I've **Succesfully** deleted the role `{}` :thumbsup:".format(rolename)
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
        Role name must be in quotes if there are spaces."""
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
                await self.bot.say(":thumbsup: Role `{}` **Successfully** removed From ***{}*** :bangbang:".format(rolename, user.name))
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
            await self.bot.reply(":punch: I've **Succesfully Added the role** `{}` To you :smile:".format(rolename))

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
            await self.bot.reply(":punch: I've **Succesfully Removed the role** `{}` from you :thumbsup:".format(rolename))

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
    async def _modset_adminrole(self, ctx, role_name: str):
        """Sets the admin role for this server, case insensitive."""
        server = ctx.message.server
        if server.id not in settings.servers:
            await self.bot.say("Remember to set modrole too.")
        settings.set_server_admin(server, role_name)
        await self.bot.say("Admin role set to '{}'".format(role_name))

    @modset.command(name="modrole", pass_context=True, no_pm=True)
    async def _modset_modrole(self, ctx, role_name: str):
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


    @commands.command(pass_context=True)
    @checks.admin_or_permissions(move_members=True)
    async def move(self, ctx, channel: discord.Channel, *users: discord.Member):
        """
        Move two or more users at a time to a voice channel
        Case sensitime Which means it has to be in the exact format Or if you have developer mode you can Use id's
        Examples: ~move AFK @dangerous @teddy / ~move channel id : 199292534671802369 user ids: 187570149207834624 203649661611802624 
        this also works if you do one id and one text like ~move 199292534671802369 @dangerous"""

        for user in users:
            await self.bot.move_member(user, channel)
            await self.bot.say("Moved **{0}** to ***__{1}__*** :heavy_check_mark: ".format(user, channel))
            await asyncio.sleep(0.1)
        await self.bot.say("***:white_check_mark: Im done moving those fags to the vc *** :v: ")  

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(move_members=True)
    async def massmove(self, ctx, from_channel: discord.Channel, to_channel: discord.Channel):
        """Massmove users to another voice channel"""
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
    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason: str=None):
        """Kicks user."""
        author = ctx.message.author
        server = author.server
        try:
            await self.bot.send_message(user, ":tools: :bangbang:️**You have been** ***KICKED*** **from** ***{}.***\n :scales: *Reason:*  **{}**".format(server.name, reason))
            await self.bot.kick(user)
            logger.info("{}({}) kicked {}({})".format(
                author.name, author.id, user.name, user.id))
            await self.new_case(server,
                                action="Kick\N{WOMANS BOOTS}",
                                mod=author,
                                user=user)
            await self.bot.say(" :ballot_box_with_check:️ Alrighty! :white_check_mark: I've kicked {} outta Here :thumbsup: ".format(user.name))
        except discord.errors.Forbidden:
            await self.bot.say(" :no_entry: Not Allowed to kick/Kick that specified user  Bruv ¯\_(ツ)_/¯ :no_entry: sorry")
        except Exception as e:
            print(e)

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member, *, reason: str=None):
        """Bans user and deletes last X days worth of messages."""
        author = ctx.message.author
        server = author.server
        channel = ctx.message.channel
        can_ban = channel.permissions_for(server.me).ban_members
        if can_ban:
            try:  # We don't want blocked DMs preventing us from banning
                await self.bot.send_message(user, ":bellhop: :hammer_pick: ️**You have been** ***BANNED***  **from** ***{}.***\n :scales: *Reason:*  **{}**".format(server.name, reason))
                pass
                self._tmp_banned_cache.append(user)
                await self.bot.ban(user)
                logger.info("{}({}) banned {}({}), deleting {} days worth of messages".format(author.name, author.id, user.name, user.id))
                await self.new_case(server, action="Ban \N{HAMMER}", mod=author, user=user)
                await self.bot.say(" :punch: I've Succesfully Banned {} :hammer: The Fok outta here :heavy_check_mark::heavy_check_mark:".format(user.name))
            except discord.errors.Forbidden:
                await self.bot.say(":bangbang:Not Allowed to kick/Kick that specified user  Bruv ¯\_(ツ)_/¯ :x: ")
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(1)
                self._tmp_banned_cache.remove(user)

    @commands.command(pass_context = True, hidden = True, no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def unban(self, ctx, user : discord.User):
        """dun work"""
        server = ctx.message.server
        channel = ctx.message.channel
        can_ban = channel.permissions_for(server.me).ban_members
        author = ctx.message.author
        
        member = discord.utils.find(lambda mem: mem.id == str(user_id), message.channel.server.members)
        try:
            await self.bot.unban(server, user)
        except discord.Forbidden:
            await self.bot.say('I do not have permissions to unban members.')
        except discord.HTTPException:
            await self.bot.say('Unbanning failed.')
        else:
            await self.bot.say('{0} has been Unbanned from this server.'.format(member.name))
    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def softban(self, ctx, user: discord.Member):
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
                              "You can now join the server again.\n {} ".format(invite))
                except:
                    pass
                self._tmp_banned_cache.append(user)
                await self.bot.ban(user, 1)
                logger.info("{}({}) softbanned {}({}), deleting 1 day worth "
                    "of messages".format(author.name, author.id, user.name,
                     user.id))
                await self.new_case(server,
                                    action="Softban \N{DASH SYMBOL} \N{HAMMER}",
                                    mod=author,
                                    user=user)
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
            await self.bot.say("Done.")
        except discord.Forbidden:
            await self.bot.say("I cannot do that, I lack the "
                "\"Manage Nicknames\" permission.")

    @commands.command(pass_context = True)
    @checks.mod_or_permissions(manage_messages=True)
    async def botclean(self, ctx, limit : int = None):
        """Cleans all of the bot messages in the channel"""
        if limit is None:
            limit = 100
        elif limit > 100:
            limit = 100
        deleted = await self.bot.purge_from(ctx.message.channel, limit=limit, before=ctx.message, check= lambda e: e.author.bot)
        reply = await self.bot.say('***:thumbsup: :ok_hand: Ayeee  {} messages deleted :thumbsup: :ok_hand: ***'.format(len(deleted)))
        await asyncio.sleep(3)
        await self.bot.delete_message(reply)

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
            await self.bot.say("I'm not allowed to delete messages.")
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
        reply = await self.bot.say("I've **Succesfully** pruned **{}** Messages containing `{}`".format(number, text))
        await asyncio.sleep(2)
        await self.bot.delete_message(reply)

    @cleanup.command(pass_context=True, no_pm=True)
    async def user(self, ctx, user: discord.Member, number: int):
        """Deletes last X messages from specified user.

        Examples:
        cleanup user @\u200bTwentysix 2
        cleanup user Red 6"""

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
            await self.bot.say("I'm not allowed to delete messages.")
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
        reply = await self.bot.say("I've **Succesfully** pruned **{}** of `{}` Messages".format(number, user.name))
        await asyncio.sleep(3)
        await self.bot.delete_message(reply)
    @cleanup.command(pass_context=True, no_pm=True)
    async def after(self, ctx, message_id : int):
        """Deletes all messages after specified message

        To get a message id, enable developer mode in Discord's
        settings, 'appearance' tab. Then right click a message
        and copy its id.

        This command only works on bots running as bot accounts.
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
            await self.bot.say("I'm not allowed to delete messages.")
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
        cleanup messages 26"""

        channel = ctx.message.channel
        author = ctx.message.author
        server = author.server
        is_bot = self.bot.user.bot
        has_permissions = channel.permissions_for(server.me).manage_messages

        to_delete = []

        if not has_permissions:
            await self.bot.say("I'm not allowed to delete messages.")
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
        reply = await self.bot.say('***:thumbsup: :ok_hand: Ayeee  {} messages deleted :thumbsup: :ok_hand: ***'.format(number))
        await asyncio.sleep(2)
        await self.bot.delete_message(reply)

    @cleanup.command(pass_context=True, no_pm=True, name='bot')
    async def cleanup_bot(self, ctx, number: int):
        """Cleans up command messages and messages from the bot"""

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
            await self.bot.say("I'm not allowed to delete messages.")
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
            case = self.last_case[server.id].get(author.id, None)
            if case is None:
                await send_cmd_help(ctx)
                return
        try:
            await self.update_case(server, case=case, mod=author,
                                   reason=reason)
        except UnauthorizedCaseEdit:
            await self.bot.say("That case is not yours.")
        except KeyError:
            await self.bot.say("That case doesn't exist.")
        except NoModLogChannel:
            await self.bot.say("There's no mod-log channel set.")
        except CaseMessageNotFound:
            await self.bot.say("Couldn't find the case's message.")
        else:
            await self.bot.say("Case #{} updated.".format(case))

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
        """Edits roles settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @editrole.command(aliases=["color"], pass_context=True)
    async def colour(self, ctx, role: discord.Role, value: discord.Colour):
        """Edits a role's colour

        Use double quotes if the role contains spaces.
        Colour must be in hexadecimal format.
        \"http://www.w3schools.com/colors/colors_picker.asp\"
        Examples:
        !editrole colour \"The Transistor\" #ff0000
        !editrole colour Test #ff9900"""
        author = ctx.message.author
        try:
            await self.bot.edit_role(ctx.message.server, role, color=value)
            logger.info("{}({}) changed the colour of role '{}'".format(
                author.name, author.id, role.name))
            await self.bot.say("Done.")
        except discord.Forbidden:
            await self.bot.say("I need permissions to manage roles first.")
        except Exception as e:
            print(e)
            await self.bot.say("Something went wrong.")

    @editrole.command(name="name", pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def edit_role_name(self, ctx, role: discord.Role, name: str):
        """Edits a role's name

        Use double quotes if the role or the name contain spaces.
        Examples:
        !editrole name \"The Transistor\" Test"""
        if name == "":
            await self.bot.say("Name cannot be empty.")
            return
        try:
            author = ctx.message.author
            old_name = role.name  # probably not necessary?
            await self.bot.edit_role(ctx.message.server, role, name=name)
            logger.info("{}({}) changed the name of role '{}' to '{}'".format(
                author.name, author.id, old_name, name))
            await self.bot.say("Done.")
        except discord.Forbidden:
            await self.bot.say("I need permissions to manage roles first.")
        except Exception as e:
            print(e)
            await self.bot.say("Something went wrong.")

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

    def is_mod_or_superior(self, message):
        user = message.author
        server = message.server
        admin_role = settings.get_server_admin(server)
        mod_role = settings.get_server_mod(server)

        if user.id == settings.owner:
            return True
        elif discord.utils.get(user.roles, name=admin_role):
            return True
        elif discord.utils.get(user.roles, name=mod_role):
            return True
        else:
            return False

    async def new_case(self, server, *, action, mod=None, user, reason=None):
        channel = server.get_channel(self.settings[server.id]["mod-log"])
        if channel is None:
            return

        if server.id in self.cases:
            case_n = len(self.cases[server.id]) + 1
        else:
            case_n = 1

        case = {"case"         : case_n,
                "action"       : action,
                "user"         : user.name,
                "user_id"      : user.id,
                "reason"       : reason,
                "moderator"    : mod.name if mod is not None else None,
                "moderator_id" : mod.id if mod is not None else None}

        if server.id not in self.cases:
            self.cases[server.id] = {}

        tmp = case.copy()
        if case["reason"] is None:
            tmp["reason"] = "Type [p]reason {} <reason> to add it".format(case_n)
        if case["moderator"] is None:
            tmp["moderator"] = "Unknown"
            tmp["moderator_id"] = "Nobody has claimed responsibility yet"

        case_msg = ("**Case #{case}** | {action}\n"
                    "**User:** {user} ({user_id})\n"
                    "**Moderator:** {moderator} ({moderator_id})\n"
                    "**Reason:** {reason}"
                    "".format(**tmp))

        try:
            msg = await self.bot.send_message(channel, case_msg)
        except:
            msg = None

        case["message"] = msg.id if msg is not None else None

        self.cases[server.id][str(case_n)] = case

        if mod:
            self.last_case[server.id][mod.id] = case_n

        dataIO.save_json("data/mod/modlog.json", self.cases)

    async def update_case(self, server, *, case, mod, reason):
        channel = server.get_channel(self.settings[server.id]["mod-log"])
        if channel is None:
            raise NoModLogChannel()

        case = str(case)
        case = self.cases[server.id][case]

        if case["moderator_id"] is not None:
            if case["moderator_id"] != mod.id:
                raise UnauthorizedCaseEdit()

        case["reason"] = reason
        case["moderator"] = mod.name
        case["moderator_id"] = mod.id

        case_msg = ("**Case #{case}** | {action}\n"
                    "**User:** {user} ({user_id})\n"
                    "**Moderator:** {moderator} ({moderator_id})\n"
                    "**Reason:** {reason}"
                    "".format(**case))

        dataIO.save_json("data/mod/modlog.json", self.cases)

        msg = await self.bot.get_message(channel, case["message"])
        if msg:
            await self.bot.edit_message(msg, case_msg)
        else:
            raise CaseMessageNotFound()

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
            self.cache[author].append(message)
            msgs = self.cache[author]
            if len(msgs) == 3 and \
                    msgs[0].content == msgs[1].content == msgs[2].content:
                if any([m.attachments for m in msgs]):
                    return False
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
                    self._tmp_banned_cache.append(author)
                    await self.bot.ban(author, 1)
                except:
                    logger.info("Failed to ban member for mention spam in "
                                "server {}".format(server.id))
                else:
                    await self.new_case(server,
                                        action="Ban \N{HAMMER}",
                                        mod=server.me,
                                        user=author,
                                        reason="Mention spam (Autoban)")
                    return True
                finally:
                    await asyncio.sleep(1)
                    self._tmp_banned_cache.remove(author)
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

    async def _new_message(self, message):
        """Finds the message and checks it for regex"""
        user = message.author
        if message.server is None:
            pass
        if message.server.id in self.json:
            if self.json[message.server.id]['toggle'] is True:
                if self.regex.search(message.content) is not None or self.regex_discordme.search(message.content) is not None:
                    roles = [r.name for r in user.roles]
                    bot_admin = settings.get_server_admin(message.server)
                    bot_mod = settings.get_server_mod(message.server)
                    if user.id == settings.owner:
                        pass
                    elif bot_admin in roles:
                        pass
                    elif bot_mod in roles:
                        pass
                    elif user.permissions_in(message.channel).manage_messages is True:
                        pass
                    else:
                        asyncio.sleep(0.5)
                        await self.bot.delete_message(message)
                        if self.json[message.server.id]['dm'] is True:
                            await self.bot.send_message(message.author, self.json[message.server.id]['message'])


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
        if member not in self._tmp_banned_cache:
            server = member.server
            await self.new_case(server,
                                user=member,
                                action="Ban \N{HAMMER}")

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



def check_folders():
    folders = ("data", "data/mod/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

    if not os.path.exists("data/autoapprove"):
        print("Creating data/autoapprove folder...")
        os.makedirs("data/autoapprove")

    if not os.path.exists('data/antilink'):
        os.makedirs('data/antilink')


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

    f = 'data/antilink/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})





def setup(bot):
    global logger
    check_folders()
    check_files()
    logger = logging.getLogger("red.mod")
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
    bot.add_listener(n._new_message, 'on_message')
    bot.add_cog(n)
