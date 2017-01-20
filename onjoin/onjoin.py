import time
import discord
from discord.ext import commands
from .utils.chat_formatting import *
from random import randint
from random import choice as randchoice
import asyncio

class Dangerous:
	def __init__(self, bot):
		self.bot = bot

	async def on_server_join(self, server):
		channel = server.default_channel
		donate = "https://www.patreon.com/user?u=3635475"
		sinv = "https://discord.gg/Tgg4kaF"
		inv ="https://discordapp.com/oauth2/authorize?client_id=217256996309565441&scope=bot&permissions=536214655"
		msg = ":bangbang:***Hiya There*** :smile:\n:bow:***Thanks for inviting me To this glorious server***\n:robot: I Am **{}** :robot: And my prefixes are as follows `{}`\n**I am A** ***fun Moderation Utility Bot Which also includes Music***\nI Provide Various funcions which can be viewed by invoking My `~help` command\n:desktop: To get Info on a certain Command simply do `~help <cmd>`:information_source: \n**Should You encounter an error report it** ***immediately by doing*** => `~contact<msghere> Or By joining the support server listed below`\nPlease use me as intended But **don't ** ***spam*** **my commands** :smile:\nI hope i can provide assitance to your server **{}** :thumbsup:".format(self.bot.user.name, self.bot.settings.prefixes, server.name)
		em = discord.Embed(description=msg, color=discord.Color.purple(), timestamp=__import__('datetime').datetime.utcnow())
		if self.bot.user.avatar_url:
			em.set_author(name="", url=self.bot.user.avatar_url)
			em.set_footer(text="Currently in {} Servers 🎇".format(len(self.bot.servers)), icon_url=self.bot.user.avatar_url)
			em.add_field(name="Invite", value="[Clickly]({})".format(inv))
			em.add_field(name="Support Server", value="[Click Here]({})".format(sinv))
			em.add_field(name="Donate", value="[Click Me]({})".format(donate))
			em.add_field(name="Owner", value="<@187570149207834624>")
			em.set_thumbnail(url=self.bot.user.avatar_url)
		await self.bot.send_message(server, embed=em)

def setup(bot):
	n = Dangerous(bot)
	bot.add_cog(n)