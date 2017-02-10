from discord.ext import commands
from __main__ import send_cmd_help
from .utils.dataIO import dataIO
from .utils import checks
import datetime
import asyncio
import discord
import time
import os

try:
    import psutil
except:
    psutil = False


class Statistics:
    """
    Statistics
    """

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/statistics/settings.json')
        self.sent_messages = self.settings['SENT_MESSAGES']
        self.received_messages = self.settings['RECEIVED_MESSAGES']
        self.refresh_rate = self.settings['REFRESH_RATE']

    @commands.command()
    async def stats(self):
        """
        Retreive statistics
        """
        message = await self.retrieve_statistics()
        await self.bot.say(embed=message)

    @commands.command(pass_context=True)
    async def statsrefresh(self, context, seconds: int=0):
        """
        Set the refresh rate by which the statistics are updated
        Example: [p]statsrefresh 42
        Default: 5
        """

        if not self.refresh_rate:  # If statement incase someone removes it or sets it to 0
            self.refresh_rate = 5

        if seconds == 0:
            message = 'Current refresh rate is {}'.format(self.refresh_rate)
            await send_cmd_help(context)
        elif seconds < 5:
            message = '`I can\'t do that, the refresh rate has to be above 5 seconds`'
        else:
            self.refresh_rate = seconds
            self.settings['REFRESH_RATE'] = self.refresh_rate
            dataIO.save_json('data/statistics/settings.json', self.settings)
            message = '`Changed refresh rate to {} seconds`'.format(
                self.refresh_rate)
        await self.bot.say(message)

    @commands.command(no_pm=True, pass_context=True)
    @checks.serverowner_or_permissions(manage_server=True)
    async def statschannel(self, context, channel: discord.Channel=None):
        """
        Set the channel to which the bot will sent its continues updates.
        Example: [p]statschannel #statistics
        """
        if channel:
            self.settings['CHANNEL_ID'] = str(channel.id)
            dataIO.save_json('data/statistics/settings.json', self.settings)
            message = 'Channel set to {}'.format(channel.mention)
        elif not self.settings['CHANNEL_ID']:
            message = 'No Channel set'
            await send_cmd_help(context)
        else:
            channel = discord.utils.get(
                self.bot.get_all_channels(), id=self.settings['CHANNEL_ID'])
            if channel:
                message = 'Current channel is {}'.format(channel.mention)
                await send_cmd_help(context)
            else:
                self.settings['CHANNEL_ID'] = None
                message = 'No channel set'
                await send_cmd_help(context)

        await self.bot.say(message)

    async def retrieve_statistics(self):
        name = self.bot.user.name
        try:
            uptime = abs(self.bot.uptime - int(time.perf_counter()))
        except TypeError:
            uptime = time.time() - time.mktime(self.bot.uptime.timetuple())
        up = datetime.timedelta(seconds=uptime)
        days = up.days
        hours = int(up.seconds / 3600)
        minutes = int(up.seconds % 3600 / 60)
        users = str(len(set(self.bot.get_all_members())))
        servers = str(len(self.bot.servers))
        text_channels = 0
        voice_channels = 0
        t1 = time.perf_counter()
        await self.bot.type()
        t2 = time.perf_counter()

        cpu_p = psutil.cpu_percent(interval=None, percpu=True)
        cpu_usage = sum(cpu_p) / len(cpu_p)

        mem_v = psutil.virtual_memory()

        for channel in self.bot.get_all_channels():
            if channel.type == discord.ChannelType.text:
                text_channels += 1
            elif channel.type == discord.ChannelType.voice:
                voice_channels += 1
        channels = text_channels + voice_channels
        cl = "***Updates:***\n***Replaced:***  **Old welcomer with a brand new More optimizable one**\n***Revamped:***  **Stats cog, Urban**\n***Fixed:*** **~unban Fully functional Ty sinatra**\n\n+***Created:***\n**RoleInfo, welcomer cs...**\n\n***`This is the end of Changelog As of 2/10/2017(1:22am)Eastern Caribbean`***\n═══════════════  ஜ۩۞۩ஜ  ═══════════════"
        list = []
        for e in self.bot.servers:
            if e.me.voice_channel is not None:
                list.append(e.name)
        bi = "***Shards:***  **None Enabled**\n***Processor Usage: `{0:.1f}%`\nMemory Usage: `{1:.1f}`%***".format(cpu_usage, mem_v.percent)

        em = discord.Embed(description='\a\n', color=discord.Color.purple())
        avatar = self.bot.user.avatar_url if self.bot.user.avatar else self.bot.user.default_avatar_url
        em.set_author(name='{} \'s Statistical Data'.format(name), icon_url=avatar)

        em.add_field(
            name='**Uptime**', value='{} D - {} H - {} M⌚'.format(str(days), str(hours), str(minutes)))
        em.add_field(name="Ping", value="{}ms⏱".format(round((t2-t1)*1000)))

        em.add_field(name='**Connected To**💻', value="***`{}`*** **Servers Containing** ***`{}`***  **Unique Members**🎊\n***`{}`***  **Total Channels** **(** ***`{}`***  **Text &** ***`{}`*** **Voice)**\n***Connected To `{}` Voice Channels***\n".format(servers, users, str(channels), str(text_channels), str(voice_channels), len(list)))

        em.add_field(name='**Message Stats**📨',
                     value="**Aquring** ***`{}`*** **Messages\nRelayed** ***`{}`*** **Messages**".format(str(self.received_messages), str(self.sent_messages)))

        em.add_field(name='**Cog Stats**', value="***`{}`*** **Active Modules Containing** ***`{}`*** **Subcommands.**".format(str(len(self.bot.cogs)), str(len(self.bot.commands))))
        em.add_field(name='BotInfo', value=bi)

        em.add_field(name='Changelog📝', value=cl)

        em.set_footer(text='API version {}'.format(discord.__version__), icon_url='https://cdn.discordapp.com/attachments/133251234164375552/279456379981529088/232720527448342530.png')
        em.set_thumbnail(url=avatar)
        return em

    async def incoming_messages(self, message):
        if message.author.id == self.bot.user.id:
            self.sent_messages += 1
        else:
            self.received_messages += 1
        self.settings['SENT_MESSAGES'] = self.sent_messages
        self.settings['RECEIVED_MESSAGES'] = self.received_messages
        dataIO.save_json('data/statistics/settings.json', self.settings)

    async def reload_stats(self):
        await asyncio.sleep(30)
        while self == self.bot.get_cog('Statistics'):
            if self.settings['CHANNEL_ID']:
                msg = await self.retrieve_statistics()
                channel = discord.utils.get(
                    self.bot.get_all_channels(), id=self.settings['CHANNEL_ID'])
                messages = False
                async for message in self.bot.logs_from(channel, limit=1):
                    messages = True
                    if message.author.name == self.bot.user.name:
                        await self.bot.edit_message(message, embed=msg)
                if not messages:
                    await self.bot.send_message(channel, embed=msg)
            else:
                pass
            await asyncio.sleep(self.refresh_rate)


def check_folder():
    if not os.path.exists('data/statistics'):
        print('Creating data/statistics folder...')
        os.makedirs('data/statistics')


def check_file():
    data = {}
    data['CHANNEL_ID'] = ''
    data['SENT_MESSAGES'] = 0
    data['RECEIVED_MESSAGES'] = 0
    data['REFRESH_RATE'] = 5
    f = 'data/statistics/settings.json'
    if not dataIO.is_valid_json(f):
        print('Creating default settings.json...')
        dataIO.save_json(f, data)


def setup(bot):
    if psutil is False:
        raise RuntimeError('psutil is not installed. Run `pip3 install psutil --upgrade` to use this cog.')
    else:
        check_folder()
        check_file()
        n = Statistics(bot)
        bot.add_cog(n)
        bot.add_listener(n.incoming_messages, 'on_message')
        bot.loop.create_task(n.reload_stats())