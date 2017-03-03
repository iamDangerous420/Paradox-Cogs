from discord.ext import commands
from cogs.utils import checks
from cogs.utils.dataIO import fileIO
import discord
import asyncio
import os
from random import choice, randint

inv_settings = {"Channel": None, "joinmessage": None, "leavemessage": None, "Embed": False, "leave": False, "botroletoggle": False, "botrole" : None, "join": False, "Invites": {}}


class Welcomer:
    def __init__(self, bot):
        self.bot = bot
        self.direct = "data/welcomer/settings.json"

    @checks.admin_or_permissions(administrator=True)
    @commands.group(name='welcomer', pass_context=True, no_pm=True, aliases=["wel","welcome"])
    async def welcome(self, ctx):
        """if a sub command is not invoked server welcomer info will popup
        Welcome and leave message, with invite link. Make sure to start first by settings the welcomer joinmessage, then continue to toggle, set leave ETC
        If you need anyhelp join the support server which can be found by doing ~invite"""
        server = ctx.message.server
        channel = ctx.message.channel
        db = fileIO(self.direct, "load")
        if not server.id in db:
            await self.bot.say(":no_good: :x: **Server** ***not found***\n**Use** ***`{0.prefix}welcome channel`***  **to set a channel.**".format(ctx))
            return
        if ctx.invoked_subcommand is None:
            if server.id in db:
                if db[server.id]["botrole"]:
                    rolename =  [role.name for role in server.roles if role.id == db[server.id]["botrole"]][0]
                else:
                    rolename = "None set"
                colour = discord.Color.purple()
                t = discord.Embed()
                t.colour = colour
                t.description = "**Showing Welcomer Settings For** **{0}**\n**Do** *`{1.prefix}help {1.command.qualified_name}`* ***for more info***".format(server.name, ctx)
                t.set_author(name = "Welcomer Settings", icon_url=self.bot.user.avatar_url)
                t.add_field(name = "Welcomer Channel", value =  "<#{}>".format(db[server.id]["Channel"]))
                t.add_field(name = "Botrole", value =  rolename)
                t.add_field(name = "Botrole Toggled", value =  db[server.id]["botroletoggle"])
                t.add_field(name = "Embed Enabled", value =  db[server.id]["Embed"])
                t.add_field(name = "Join Message Toggled", value =  db[server.id]["join"])
                t.add_field(name = "Leave Message Toggled", value =  db[server.id]["leave"])
                t.add_field(name = "Join Message", value =  db[server.id]["joinmessage"], inline=False)
                t.add_field(name = "Leave Message", value =  db[server.id]["leavemessage"], inline=False)
                t.set_footer(text = "Welcomer Settings", icon_url = server.icon_url)
                t.timestamp = ctx.message.timestamp
            try:
                await self.bot.send_message(channel, embed = t)
            except discord.HTTPException:
                msg = "```css\nShowing Welcomer Settings For {0.name}.\nDo {1.prefix}help {1.command.qualified_name} for more info\n".format(server, ctx)
                msg += "Welcomer Channel Id : {0}\nBotrole Id : {1}\nBotrole Toggled : {2}\nEmbed Enabled: {3}\nJoin Message Toggled : {4}\nLeave Message Toggled : {5}\nJoin Message : {6}\nLeave Message: {7}\n```".format(db[server.id]["Channel"], db[server.id]["botrole"], db[server.id]["botroletoggle"], db[server.id]["Embed"], db[server.id]["join"], db[server.id]["leave"], db[server.id]["joinmessage"], db[server.id]["leavemessage"])
                await self.bot.send_message(channel, msg)
    @welcome.command(name='channelset', pass_context=True, no_pm=True, aliases=["cs","ch","channel"])
    async def channel(self, ctx, *, channel : discord.Channel):
        """
        Use this if you donot like the currently set welcomer channel
        """

        server = ctx.message.server
        db = fileIO(self.direct, "load")
        if not ctx.message.server.me.permissions_in(channel).manage_channels:
            await self.bot.say(":x: **I dont have the manage channels permission in** ***#{}***.:x:".format(channel))
            return
        if ctx.message.server.me.permissions_in(channel).send_messages:
            if not server.id in db:
                db[server.id] = inv_settings
                invlist = await self.bot.invites_from(server)
                db[server.id]["Channel"] = channel.id
                for i in invlist:
                    db[server.id]["Invites"][i.url] = i.uses
                fileIO(self.direct, "save", db)
            db[server.id]["Channel"] = channel.id
            await self.bot.say(":thumbsup: **Ill be sending welcome messages to** : ***#{}***:punch:".format(channel))
            fileIO(self.direct, "save", db)

    @welcome.command(name='joinmessage', pass_context=True, no_pm=True, aliases=["jm"])
    async def joinmessage(self, ctx, *, message: str):
        """
        Set a message when a user joins
        {0} is the user
        {1} is the invite that he/her joined using
        {2} is the server {2.name} <-
        Example formats:
            {0.mention} this will mention the user when he joins
            {2.name} is the name of the server
            {1.inviter} is the user that made the invite
            {1.url} is the invite link the user joined with
        Message Examples:
        {0.mention} Welcome to {2.name}, User joined with {1.url} referred by {1.inviter}
        Welcome to {2.name} {0}! I hope you enjoy your stay
        {0.mention}.. What are you doing here? Ã°Å¸Â¤ï¿½ï¿½ï¿½
        ***{2.name}***  has a new member! ***{0.name}#{0.discriminator} - {0.id}***Ã°Å¸â€˜Â
        Someone new joined! Who is it?! D: IS HE HERE TO HURT US?!
        """
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        if not server.id in db:
            await self.bot.say(":no_good: :x: **Server** ***not found***\n**Use** ***`{0.prefix}welcome channelset`***  **to set a channel.**".format(ctx))
            return
        if server.id in db:
            db[server.id]['joinmessage'] = message
            fileIO(self.direct, "save", db)
            await self.bot.say(":thumbsup: **Done** I've Successfully set the welcome greeting too :\n`{}`".format(message))
            return
        if not ctx.message.server.me.permissions_in(ctx.message.channel).manage_channels:
            await self.bot.say(":x: **I dont have the manage channels permission.** :x:")
            return

    @welcome.command(name='leavemessage', pass_context=True, no_pm=True, aliases=["lm"])
    async def leavemessage(self, ctx, *, message: str):
        """
        Set a message when a user leaves
        {0} is the user
        {1} is the server
        Example formats:
            {0.mention} this will mention the user when he joins
            {1.name} is the name of the server
            {0.name} is the name
        Message Examples:
            Sad to see {0.mention} leave us in {1.name}
            Crap we lost another ONE {0.name} lEFT!!
        """
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        if server.id in db:
            db[server.id]['leavemessage'] = message
            fileIO(self.direct, "save", db)
            await self.bot.say("**Leave message** ***changed.***:thumbsup:")
            return
    @welcome.command(name='botrole', pass_context=True, no_pm=True, aliases=["br"])
    async def botrole(self, ctx, *, role : discord.Role):
        """sets the botrole to auto assign roles to bots"""
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        if not server.id in db:
            await self.bot.say(":no_good: :x: **Server** ***not found***\n**Use** ***welcome joinmessage***  **to set a channel.**")
            return
        if ctx.message.server.me.permissions_in(ctx.message.channel).manage_roles:
            db[server.id]['botrole'] = role.id
            fileIO(self.direct, "save", db)
            await self.bot.say(":raising_hand: ***OI OI*** **Bot role** ***Saved***:punch:")
        else:
            await self.bot.say(":no_good: :x: **I do not have the manage_roles permission :x: :no_good:")

    @welcome.command(name='botroletoggle', pass_context=True, no_pm=True, aliases=["brt"])
    async def botroletoggle(self, ctx):
        """toggles bot role du"""
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        if not server.id in db:
            await self.bot.say("Server not found, use ~welcome joinmessage to set a channel.")
            return
        if db[server.id]['botrole'] == None:
            await self.bot.say(":no_good:***Role Not Found***:no_good:\n***__```set it with ~welcomer botrole```__***")
        if db[server.id]["botroletoggle"] == False:
            db[server.id]["botroletoggle"] = True
            fileIO(self.direct, "save", db)
            await self.bot.say("***Bot role enabled*** :thumbsup:")
        elif db[server.id]["botroletoggle"] == True:
            db[server.id]["botroletoggle"] = False
            fileIO(self.direct, "save", db)
            await self.bot.say("***Bot roledisabled*** :thumbsup:")


    @welcome.command(name='toggleleave', pass_context=True, no_pm=True, aliases=["tl"])
    async def toggleleave(self, ctx):
        """toggle leave message"""
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        channel = db[server.id]["Channel"]
        if db[server.id]["leave"] == False:
            db[server.id]["leave"] = True
            fileIO(self.direct, "save", db)
            await self.bot.say("**Leave messages** ***enabled***  :thumbsup: Ill be sending leave messages to : ***#{}***".format(server.get_channel(channel).name))
        elif db[server.id]["leave"] == True:
            db[server.id]["leave"] = False
            fileIO(self.direct, "save", db)
            await self.bot.say(":x:***Leave messages disabled*** :thumbsup:")

    @welcome.command(name='togglejoin', pass_context=True, no_pm=True, aliases=["tj"])
    async def togglejoin(self, ctx):
        """toggle join message"""
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        channel = db[server.id]["Channel"]
        if db[server.id]["join"] == False:
            db[server.id]["join"] = True
            fileIO(self.direct, "save", db)
            await self.bot.say(":punch:***Join messages enabled***:thumbsup: **Ill be sending welcome messages to** : ***#{}***".format(server.get_channel(channel).name))
        elif db[server.id]["join"] == True:
            db[server.id]["join"] = False
            fileIO(self.direct, "save", db)
            await self.bot.say(":bangbang::no_good:**Join messages disabled**:no_good::bangbang:")

    @welcome.command(name='embed', pass_context=True, no_pm=True, aliases=["em"])
    async def embed(self, ctx):
        """Opt into making all welcome and leave messages embeded"""
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        if not server.id in db:
            await self.bot.say(":raised_hand: **Server not found, use welcomer joinmessage to set a channel.** :raised_hand:")
            return
        if db[server.id]["Embed"] == False:
            db[server.id]["Embed"] = True
            fileIO(self.direct, "save", db)
            await self.bot.say("***Embeds enabled***:thumbsup:")
        elif db[server.id]["Embed"] == True:
            db[server.id]["Embed"] = False
            fileIO(self.direct, "save", db)
            await self.bot.say(":bangbang: :x: **Embeds disabled** :x: :bangbang:")

    @welcome.command(name='disable', pass_context=True, no_pm=True)
    async def disable(self, ctx):
        """disables the welcomer"""
        server = ctx.message.server
        db = fileIO(self.direct, "load")
        channel = db[server.id]["Channel"]
        if not server.id in db:
            await self.bot.say(":raised_hand: **Server not found, use welcomer joinmessage to set a channel.** :raised_hand:")
            return
        del db[server.id]
        fileIO(self.direct, "save", db)
        await self.bot.say(":bangbang::no_good:**I will no longer send welcome messages to** ***{}***:x:".format(server.get_channel(channel).name))

    async def on_member_join(self, member):
        server = member.server
        db = fileIO(self.direct, "load")
        if not server.id in db:
            return
        if member.bot:
            if db[server.id]['botroletoggle'] == True:
                roleobj = [r for r in server.roles if r.id == db[server.id]['botrole']]
                await self.bot.add_roles(member, roleobj[0])
        await asyncio.sleep(1)
        if db[server.id]['join'] == False:
            return
        channel = db[server.id]["Channel"]
        message = db[server.id]['joinmessage']
        json_list = db[server.id]["Invites"]
        inv_list = await self.bot.invites_from(server)
        avatar = member.avatar_url if member.avatar else server.icon_url
        for a in inv_list:
            try:
                if int(a.uses) > int(json_list[a.url]):
                    if db[server.id]["Embed"] == True:
                        color = ''.join([choice('0123456789ABCDEF') for x in range(6)])
                        color = int(color, 16)
                        data = discord.Embed(description=message.format(member, a, server),
                                             colour=discord.Colour(value=color))
                        data.set_author(name="New User!!", icon_url=server.icon_url)
                        data.set_footer(text="ID: {}".format(member.id), icon_url=self.bot.user.avatar_url)
                        data.set_thumbnail(url=avatar)
                        await self.bot.send_message(server.get_channel(channel), embed=data)
                        break
                    else:
                        await self.bot.send_message(server.get_channel(channel), message.format(member, a, server))
                        break
            except KeyError:
                if db[server.id]["Embed"] == True:
                    color = ''.join([choice('0123456789ABCDEF') for x in range(6)])
                    color = int(color, 16)
                    data = discord.Embed(description=message.format(member, a, server),
                                         colour=discord.Colour(value=color))
                    data.set_author(name="New User!!", icon_url=server.icon_url)
                    data.set_footer(text="ID: {}".format(member.id), icon_url=self.bot.user.avatar_url)
                    data.set_thumbnail(url=avatar)
                    await self.bot.send_message(server.get_channel(channel), embed=data)
                    break
                else:
                    await self.bot.send_message(server.get_channel(channel), message.format(member, a, server))
                    break
                break
            else:
                pass
        invlist = await self.bot.invites_from(server)
        for i in invlist:
            db[server.id]["Invites"][i.url] = i.uses
        fileIO(self.direct, "save", db)

    async def on_member_remove(self, member):
        server = member.server
        db = fileIO(self.direct, "load")
        if not server.id in db:
            return
        if db[server.id]['leave'] == False:
            return
        message = db[server.id]['leavemessage']
        channel = db[server.id]["Channel"]
        avatar = member.avatar_url if member.avatar else server.icon_url
        if db[server.id]["Embed"] == True:
            color = ''.join([choice('0123456789ABCDEF') for x in range(6)])
            color = int(color, 16)
            data = discord.Embed(description=message.format(member, server), icon_url=server.icon_url, colour=discord.Colour(value=color))
            data.set_author(name="", icon_url=server.icon_url)
            data.set_footer(text="ID: {}".format(member.id), icon_url=self.bot.user.avatar_url)
            await self.bot.send_message(server.get_channel(channel), embed=data)
        else:
            await self.bot.send_message(server.get_channel(channel), message.format(member, server))


def check_folder():
    if not os.path.exists('data/welcomer'):
        print('Creating data/welcomer folder...')
        os.makedirs('data/welcomer')


def check_file():
    f = 'data/welcomer/settings.json'
    if not fileIO(f, 'check'):
        print('Creating default settings.json...')
        fileIO(f, 'save', {})

def setup(bot):
    check_folder()
    check_file()
    bot.add_cog(Welcomer(bot))