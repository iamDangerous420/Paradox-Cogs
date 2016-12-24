import discord
from discord.ext import commands
from .utils.chat_formatting import *

class d:
    def __init__(self, bot):
        self.bot = bot

    async def on_server_join(self, server):
        channel = server.default_channel
        msg = ":bangbang:***Hiya There*** :smile:\n:bow:***Thanks for inviting me To this glorious server***\n:robot: I Am **{}** :robot: And my prefixes are as follows {}\n**I am A** ***fun Moderation Utility Bot***\nI Provide Various funcions which can be viewed by invoking My `~help` command\nTo get Info on a certain Command simply do `~help <cmd>`:information_source: \n**Should You encounter an error report it** ***immediately by doing*** => `~contact<msghere>`\nPlease use me as intended But **don't ** ***spam*** **my commands** :smile:\nI hope i can provide assitance to your server **{}** :thumbsup:".format(self.bot.user.name, self.bot.settings.prefixes, server.name)

        await self.bot.send_message(server, msg)

def setup(bot):
    n = d(bot)
    bot.add_cog(n)