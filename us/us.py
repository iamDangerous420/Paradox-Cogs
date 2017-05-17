import requests
import json
import discord
from discord.ext import commands
from cogs.utils import checks

class updateservers:
    """updateservers"""

    def __init__(self, bot):
        self.bot = bot

    @checks.is_owner()
    @commands.command()
    async def updateservers(self):
        """updateservers"""
        thepostdata ={
            "server_count": int(len(self.bot.servers) + 1868)
        }
        r = requests.post("https://bots.discord.pw/api/bots/217256996309565441/stats", headers={'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiIxODc1NzAxNDkyMDc4MzQ2MjQiLCJyYW5kIjo0NCwiaWF0IjoxNDc5ODYxMDUwfQ._YJ9Q5ZkQYHEK74ApGIQ0m2CMrGhUzZgvK0Dms92bdg', 'Content-Type' : 'application/json'}, data=json.dumps(thepostdata))
        await self.bot.say(r.content.decode('utf-8'))
        
def setup(bot):
    bot.add_cog(updateservers(bot))
