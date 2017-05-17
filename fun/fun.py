import discord
from discord.ext import commands
import random
from random import randint
from random import choice as randchoice
from random import choice
from random import choice as rnd
import datetime
import aiohttp
import asyncio
import io, os, re
import time
import logging
#########################utils###########################
from .utils.chat_formatting import *
from __main__ import send_cmd_help
from .utils import checks
from cogs.utils.dataIO import dataIO
from __main__ import send_cmd_help, user_allowed
from cogs.utils import checks
from .utils.dataIO import fileIO
from cogs.utils.chat_formatting import box, pagify, escape_mass_mentions
from cogs.utils.settings import Settings
#############Oter#################
import urllib
import math
from copy import deepcopy
import xmltodict
import json
import requests
################tries#################
try:
        from pyfiglet import figlet_format
except:
    figlet_format = None

try:
    from PIL import Image, ImageDraw, ImageFont, ImageColor
    pil_available = True
except:
    pil_available = False

##############End OF ports###################
log = logging.getLogger("red.admin")


def slowExponent(x):
    return 1.3 * x * (1 - math.atan(x / 6.0) * 2 / math.pi)


def slowPow(x, y):
    return math.pow(x, slowExponent(y))


def caseShifts(s):
    s = re.sub('[^a-zA-Z]', '', s)
    s = re.sub('[A-Z]+', 'U', s)
    s = re.sub('[a-z]+', 'l', s)
    return len(s) - 1


def numberShifts(s):
    s = re.sub('[^a-zA-Z0-9]', '', s)
    s = re.sub('[a-zA-Z]+', 'l', s)
    s = re.sub('[0-9]+', 'n', s)
    return len(s) - 1


def is_mention(name):
    if len(name) > 3 and name[:2] == "<@" and name[-1] == ">":
        try:
            int(name[2:-1])
        except:
            pass
        else:
            return True
    return False


def getid(name):
    return name[2:-1]

class Fun:
    """Enjoy Fun stuff and memes if i made it"""

    def __init__(self, bot):
        self.bot = bot
                #################Married############################
        self.JSON = 'data/married/married.json'
        self.data = dataIO.load_json(self.JSON)

########################################### MARRIAGE #############################################

    @commands.command(pass_context=True)
    async def marry(self, ctx, user : discord.Member):
        """So you think you found the love of your life? Marry them!!"""
        server = ctx.message.server
        author = ctx.message.author.mention
        me = ctx.message.author.name
        bot = [m.mention for m in ctx.message.server.members if m.bot]
        if user.mention == author:
            em0 = discord.Embed(description='Trying to marry yourself eh... I don\'t think thats possible..', color=0X91A1AB)
            await self.bot.say(embed=em0)
            return
        if user.mention == self.bot.user.mention:
            em0 = discord.Embed(description='So you wanna marry me huh, I am married to <@187570149207834624> but Just know i still love u <3... 😚😚', color=0X00FFAF)
            await self.bot.say(embed=em0)
            return

        if user.mention == bot:
            em0 = discord.Embed(description='You are a sick fuck, Ik bots are people but we are not capable of love hop off.', color=0XF23636)
            await self.bot.say(embed=em0)
            return


        desc = ":church: {} **has proposed to** {} :ring:".format(me, user.name)
        name = ":ring: {},  Do you accept ? :bell:".format(user.name)
        em = discord.Embed(description=desc, color=0XE9AEAE)
        em.add_field(name=name, value='**Type `yes` to accept or `no` to decline.**')
        await self.bot.say(embed=em)
        response = await self.bot.wait_for_message(author=user)

        if response.content.lower().strip() == "yes":
            await self._create_author(server, ctx, user)
            await self._create_user(server, ctx, user)
            msg = ":bride_with_veil::skin-tone-3: :man_in_tuxedo::skin-tone-3: :hand_with_index_and_middle_finger_crossed::skin-tone-3: **Congratulations!!** ***``" + me + "``*** **and** ***``" + user.name + "``*** :couplekiss: :fireworks: :clap::skin-tone-3:"
            em1 = discord.Embed(description=msg, color=0Xc2c2f3)
            await self.bot.say(embed=em1)
            dataIO.save_json(self.JSON, self.data)
        else:
            msg = "😱 **The proposal between** ***``" + me + "``*** **and** ***``" + user.name + "`` has been declined.***😬😬"
            em2 = discord.Embed(description=msg, color=0XF23636)
            await self.bot.say(embed=em2)

    @commands.command(pass_context=True)
    async def divorce(self, ctx, user: discord.Member):
        """So you are reconsidering and decieded fk em time for a divoce welp nows ur chance"""
        author = ctx.message.author.name
        server = ctx.message.server
        if user.mention == author:
            em0 = discord.Embed(description='You cant\'t even marry yourself how the hell you gonna divorce yourself?', color=0XF23636)
            await self.bot.say(embed=em0)
        else:
            if user.name in self.data[server.id]["user"][author]["married_to"]:
                await self._divorce(server, ctx, user)
                me = ctx.message.author.name
                msg = '***Well Rip,*** **' + me + '** ***`has divorced `*** ***' + user.name + '.***\n***Gossip when?***'
                em = discord.Embed(description=msg, color=0XF23636)
                await self.bot.say(embed=em)
            else:
                msg = 'Ok So problem. You are trying to divorce someone you never married :thinking: :thinking: '
                em = discord.Embed(description=msg, color=0XF23636)
                await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def profile(self, ctx, user : discord.Member=None):
        """Profile info"""
        autor = ctx.message.author.name
        author = ctx.message.author
        channel = ctx.message.channel
        userr = None
        server = ctx.message.server
        na = 'N/A'
        wp = 'Working Progress...'
        if user is None:
            user = author
        if user.id == "190634577948049408" or user.id == "124946832307519492" or user.id == "166179284266778624":
            d = "<:vpGreenTick:257437292820561920>"
        else:
            d = "<:vpRedTick:257437215615877129>"

        if server.id not in self.data:
            self.data[server.id] = {}
            dataIO.save_json(self.JSON, self.data)
        if "user" not in self.data[server.id]:
            self.data[server.id]["user"] = {}
            dataIO.save_json(self.JSON, self.data)
        if user.name not in self.data[server.id]["user"]:
            self.data[server.id]["user"][user.name] = {}
            dataIO.save_json(self.JSON, self.data)
        if "married_to" not in self.data[server.id]["user"][user.name]:
            self.data[server.id]["user"][user.name]["married_to"] = {}
            dataIO.save_json(self.JSON, self.data)
        if self.data[server.id]["user"][user.name]["married_to"] == {}:
            married = "No one 😰"
        else:
            married = " \n".join(self.data[server.id]["user"][user.name]["married_to"]).replace("{}'", "")
        await self.bot.send_typing(channel)
        em = discord.Embed(color=0XAB42EE)
#        em.add_field(name='', value=na)
        em.set_author(name='{}\'s Profile'.format(user.name))
        em.add_field(name='Donator', value=d)
        em.add_field(name='Repuatation', value=wp)
        em.add_field(name='Kills', value=wp)
        em.add_field(name='hunting Rank', value=wp)
        em.add_field(name='Animals Killed', value=wp)
        em.add_field(name='Races Won', value=wp)
        em.add_field(name='Nudes', value=na)

        em.add_field(name='Married to 💍', value=married, inline=True)
        if user.avatar_url:
            name = str(user)
            name = (name) if user.nick else name
            em.set_thumbnail(url=user.avatar_url)
        await self.bot.say(embed=em)

##################################### MARRRY ################################################

    @commands.command(pass_context=True)
    async def sword(self, ctx, *, user: discord.Member):
        """Sword Duel!#SCARLETRAVEN"""
        author = ctx.message.author
        if user.id == self.bot.user.id:
            await self.bot.say("I'm not the fighting kind")
        else:
            await self.bot.say(author.mention + " and " + user.mention + " dueled for " + str(randint(2, 120)) +
                               " gruesome hours! It was a long, heated battle, but " +
                               choice([author.mention, user.mention]) + " came out victorious!")
    @commands.command(pass_context=True)
    async def loves(self, ctx, user : discord.Member):
        """Found your one true love? #SCARLETRAVEN"""
        author = ctx.message.author
        await self.bot.say("**💝 {} is capable of loving {}❣ a whopping** ***`{}%!`***💞".format(author.mention, user.mention, str(randint(0, 100))))


    @commands.command(pass_context=True)
    async def squats(self, ctx):
        """How is your workout going? #SCARLETRAVEN"""
        author = ctx.message.author
        await self.bot.say(author.mention + " **puts on their game face 😠 and does** ***`" + str(randint(2, 1000)) +
                           "`*** **squats in** ***``" + str(randint(4, 90)) + " minutes.`` Wurk it!🍑***")

    @commands.command(pass_context=True)
    async def pizza(self, ctx):
        """How many slices of pizza have you eaten today? #SCARLETRAVEN"""
        author = ctx.message.author
        await self.bot.say(author.mention + " has eaten " + str(randint(2, 120)) + " slices of pizza today.")

    @commands.command(pass_context=True)
    async def bribe(self, ctx, user : discord.Member):
        """Find out who is paying under the table #SCARLETRAVEN"""
        author = ctx.message.author
        await self.bot.say("💸 💰  **" + author.mention + " has bribed " + user.mention + " with** ***``" +
                           str(randint(10, 10000)) + "``*** **dollars!💸 💰**")


    @commands.command()
    async def calculated(self):
        """That was 100% calculated! #SCARLETRAVEN"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        t = ["https://media.giphy.com/media/3o7qDVYlD9X4JwE4X6/giphy.gif", "https://giphy.com/gifs/brawlhalla-calculated-xUPGczvwYdC5WnhkfC", "https://www.mybanktracker.com/news/wp-content/uploads/2011/02/Complex-Math-Equation-Calculation.jpg", "https://sav-cdn.azureedge.net/images/content-article/credit-score-report-how-are-credit-scores-calculated.jpg"]
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.add_field(name="\u200b", value="**That was** ***``" + str(randint(0, 100)) + "%``*** **calculated!**", inline=True)
        data.set_thumbnail(url=randchoice(t))
        await self.bot.say(embed=data)

    @commands.command(name="ascii")
    async def _ascii(self, *, text):
        msg = str(figlet_format(text, font='cybermedium'))
        if msg[0] == " ":
            msg = "." + msg[1:]
        error = figlet_format('LOL, that\'s a bit too long.',
                              font='cybermedium')
        if len(msg) > 2000:
            await self.bot.say(box(error))
        else:
            await self.bot.say(box(msg))

    @commands.command()
    async def lenny(self):
        """This does stuff( ͡° ͜ʖ ͡°)!"""

        await self.bot.say("( ͡° ͜ʖ ͡°)")

    @commands.command(pass_context=True, hidden=True)
    async def bang(self, ctx, user : discord.Member):
        """Command Idea stolen from => Voctor#0409 Owner of Vonodosh#5066"""
        channel = ctx.message.channel
        shoot = [""]
        em = discord.Embed(color=ctx.message.author.color)
        em.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
        em.set_image(url=randchoice(shoot))
        await self.bot.send_typing(channel)
        await self.bot.send_message(channel, embed = em)
    @commands.command(pass_context=True, hidden=True)
    async def shoot(self, ctx, user : discord.Member):
        channel = ctx.message.channel
        shoot = [""]
        em = discord.Embed(color=ctx.message.author.color)
        em.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
        em.set_image(url=randchoice(shoot))
        await self.bot.send_typing(channel)
        await self.bot.send_message(channel, embed = em)

    @commands.command(pass_context=True, aliases=['doggo','dogfact','dogfacts'])
    async def dogf(self,ctx):
        avatar = self.bot.user.avatar_url
        async with aiohttp.get("https://dog-api.kinduff.com/api/facts") as cfget:
            fact_json = await cfget.json()
        fact = fact_json["facts"][0]
        em = discord.Embed(color=0x738bd7)
        em.set_author(name='Doggo fact.')
        em.add_field(name='Fact', value=fact, inline=True)
        await self.bot.say(embed=em)

#        async with aiohttp.get("http://catfacts-api.appspot.com/api/facts") as cfget:
            #fact_json = await cfget.json()
        #fact = fact_json["facts"][0]
    @commands.command(no_pm=True, pass_context=True, name="cat")
    async def _catfact(self, ctx):
        """Gets a random cat fact"""
        image_type = ['gif','jpg','png']
        file = urllib.request.urlopen('http://thecatapi.com/api/images/get?api_key=MTc3NTQy&format=xml&type='+image_type[randint(0,2)]+'&results_per_page=1')
        data = file.read()
        file.close()
        data = xmltodict.parse(data)
        url = data['response']['data']['images']['image']['url']
    #    async with aiohttp.get("http://catfacts-api.appspot.com/api/facts") as cfget:
    #        fact_json = await cfget.json()
    #    fact = fact_json["facts"][0]

        em = discord.Embed(color=0x738bd7)
    #    em.set_author(name='Kitty.', url=em.Empty)
    #    em.add_field(name='Fact', value=fact, inline=True)
        em.set_image(url=url)
        await self.bot.say(embed=em)
    @commands.group(pass_context=True, no_pm=True)
    async def dandy(self, ctx):
        """Dandy stuff"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @dandy.command(pass_context=True)
    async def wow(self, ctx):
        """Dandy wowed af bruv"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://cdn.discordapp.com/emojis/230130258794250242.png")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def trash(self, ctx):
        """Dandy trash af bruv Look closer maybe youll see his ass"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        t = ["https://cdn.discordapp.com/emojis/272909168493592576.png", "https://cdn.discordapp.com/attachments/269293047962009602/302800149028012033/298594300269166592.png"]
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url=randchoice(t))
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def feels(self, ctx):
        """Dandy Feels bruv"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://goo.gl/IsNMKz")
        await self.bot.say(embed=data)

    @dandy.command(pass_context=True)
    async def love(self, ctx):
        """Dandy love <3"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        love = ["https://cdn.discordapp.com/emojis/287299874742075393.png", "https://goo.gl/JX8MyO", "https://cdn.discordapp.com/attachments/269293047962009602/302800152106762240/287299874742075393.png"]
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url=randchoice(love))
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def up(self, ctx):
        """Dandy Approves"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://goo.gl/c4SOgL")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True,aliases=["dead"])
    async def ded(self, ctx):
        """Dandys ded"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://cdn.discordapp.com/attachments/269293047962009602/302800145613979649/301719269798838272.png ")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def anger(self, ctx):
        """Dandy Is angry ? wat a gayass"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        anger =["https://goo.gl/xO3iXo", "https://cdn.discordapp.com/attachments/269293047962009602/302800143529410561/300481277155606528.png"]
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url=randchoice(anger))
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def bj(self, ctx):
        """Dandy gets sucked(jk is still a virgin LUL)"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://goo.gl/pbEQ2F")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def wotm8(self, ctx):
        """Dandy ????"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://goo.gl/iUvflC")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def study(self, ctx):
        """Dandy studys despite not going to skool"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://goo.gl/Q9EMgK")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def lisa(self, ctx):
        """Dandy is a girl now"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://cdn.discordapp.com/attachments/218497299897253888/238816394068623360/DANDY_2.jpg")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True, aliases=["ginnepig"])
    async def ginne(self, ctx):
        """ISSA hamster"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://cdn.discordapp.com/attachments/218497299897253888/218497499621490688/IMG_0314.PNG")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True)
    async def huuh(self, ctx):
        """Dandy huuh"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://cdn.discordapp.com/attachments/218497299897253888/238808123920351232/DANDY.jpg")
        await self.bot.say(embed=data)
    @dandy.command(pass_context=True, aliases=["rinsed"])
    async def rinse(self, ctx):
        """GET RINSED MATE"""
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url="https://cdn.discordapp.com/attachments/218497299897253888/218498317041139712/IMG_0365.JPG")
        await self.bot.say(embed=data)

    @commands.group(aliases=["pepe"], invoke_without_command=True, pass_context=True)
    async def _pepe(self, ctx):
        """Get your fres pepe images(may_contain_nsfw)"""
        pepes = [
        "http://i.imgur.com/7EVod1e.png",
        "http://i.imgur.com/vpIyEue.png",
        "http://i.imgur.com/0koMC0v.jpg",
        "http://i.imgur.com/9Q6KMZa.png",
        "http://i.imgur.com/54xy6jr.png",
        "http://i.imgur.com/QvCngiJ.jpg",
        "http://i.imgur.com/ftWgrOE.jpg",
        "http://i.imgur.com/rhDSqRv.jpg",
        "http://i.imgur.com/89NZ3zM.jpg",
        "http://i.imgur.com/I4cIH5b.png",
        "http://i.imgur.com/GIFc4uX.png",
        "http://i.imgur.com/bgShJpZ.png",
        "http://i.imgur.com/jpfPLyn.png",
        "http://i.imgur.com/pZeYoej.png",
        "http://i.imgur.com/M8V9WKB.jpg",
        "http://i.imgur.com/ZBzHxNk.jpg",
        "http://i.imgur.com/xTyJ6xa.png",
        "http://i.imgur.com/TOozxRQ.png",
        "http://i.imgur.com/Eli5HdZ.png",
        "http://i.imgur.com/pkikqcA.jpg",
        "http://i.imgur.com/gMF8eo5.png",
        "http://i.imgur.com/HYh8BUm.jpg",
        "http://i.imgur.com/ZGVrRye.jpg",
        "http://i.imgur.com/Au4F1px.jpg",
        "http://i.imgur.com/gh36k9y.jpg",
        "http://i.imgur.com/MHDoRuN.png",
        "http://i.imgur.com/V3MJfyK.png",
        "http://i.imgur.com/QGGTipc.jpg",
        "http://i.imgur.com/PRFrTgz.png",
        "http://i.imgur.com/9UBJrwM.jpg",
        "http://i.imgur.com/WQY9Vhb.jpg",
        "http://i.imgur.com/sIbQdou.jpg",
        "http://i.imgur.com/LlUMg00.jpg",
        "http://i.imgur.com/MmijlWa.png",
        "http://i.imgur.com/i0CrtrX.png",
        "http://i.imgur.com/Dfpudwp.jpg",
        "http://i.imgur.com/hhg0wVF.gif",
        "http://i.imgur.com/7VDiIHN.jpg",
        "http://i.imgur.com/nxvXpNV.jpg",
        "http://i.imgur.com/DZYEjrW.gif",
        "http://i.imgur.com/mnyQ0Rh.jpg",
        "http://i.imgur.com/aHawbbs.jpg",
        "http://i.imgur.com/g8cCHV7.jpg",
        "http://i.imgur.com/E2cMU7Y.jpg",
        "http://i.imgur.com/PkmcgGF.jpg",
        "http://i.imgur.com/7qLQ1xl.jpg",
        "http://i.imgur.com/7qLQ1xl.jpg",
        "http://i.imgur.com/arSsPwf.png",
        "http://i.imgur.com/xcYh4iC.png",
        "http://i.imgur.com/9692WND.jpg",
        "http://i.imgur.com/diAK5Nu.jpg",
        "http://i.imgur.com/zDs0tRW.jpg",
        "http://i.imgur.com/PEM87nV.jpg",
        "http://i.imgur.com/zlCzlND.jpg",
        "http://i.imgur.com/n0OHxDl.jpg",
        "http://i.imgur.com/TQRf1WH.png",
        "http://i.imgur.com/zi9ad15.jpg",
        "http://i.imgur.com/b8A6Qke.jpg",
        "http://i.imgur.com/YuLapEu.png",
        "http://i.imgur.com/fWFXkY1.jpg",
        "http://i.imgur.com/i5vNvWU.png",
        "http://i.imgur.com/oXwUwtJ.jpg",
        "http://i.imgur.com/hadm4jV.jpg",
        "http://i.imgur.com/gbCvkqo.png",
        "http://i.imgur.com/wDiiWBG.jpg",
        "http://i.imgur.com/Mvghx4V.jpg",
        "http://i.imgur.com/SnTAjiJ.jpg",
        "http://i.imgur.com/QvMYBnu.png",
        "http://i.imgur.com/WkzPvfB.jpg",
        "http://i.imgur.com/PfAm4ot.png",
        "http://i.imgur.com/SIk4a45.png",
        "http://i.imgur.com/aISFmQq.jpg",
        "http://i.imgur.com/sMQkToE.png",
        "http://i.imgur.com/7i3cBrP.png",
        "http://i.imgur.com/1oMSz6e.png",
        "http://i.imgur.com/nVCRnRv.png",
        "http://i.imgur.com/FzWmxmi.jpg",
        "http://i.imgur.com/rpUI20F.jpg",
        "http://i.imgur.com/FDmnFDZ.jpg",
        "http://i.imgur.com/40Z1Yyg.jpg",
        "http://i.imgur.com/osy5Nu4.png",
        "http://i.imgur.com/4w81MSS.jpg",
        "http://i.imgur.com/qRXQFYa.png",
        "http://i.imgur.com/A1af62j.jpg",
        "http://i.imgur.com/wOc6fUe.jpg",
        "http://i.imgur.com/Z6ILiJ4.jpg",
        "http://i.imgur.com/537UpEJ.jpg",
        "http://i.imgur.com/HDc6kko.png",
        "http://i.imgur.com/oyLpuXq.jpg",
        "http://i.imgur.com/iCmGtJS.jpg",
        "http://i.imgur.com/MjpnlQm.png",
        "http://i.imgur.com/c6MWRQ9.jpg"
        ]
        colour = ''.join([choice('0123456789ABCDEF') for x in range(6)])
        colour = int(colour, 16)
        data = discord.Embed(colour=discord.Colour(value=colour))
        data.set_image(url=rnd(pepes))
        await self.bot.say(embed=data)

    @commands.command(pass_context=True)
    async def compliment(self, ctx, user :discord.Member):
        """Compliment a user!"""

        a = ["You're a beautiful person, friend.", "I hope you succeed in life.", "You're a bright human being and nobody can tell you otherwise.", "You have beautiful eyes.", "Your significant other will be a model, no doubt.",
        "You will be very rich in the future. God bless you.", "DJ Khalid has nothing on you.", "You have the keys to success. You just haven't found them yet.", "You can be anything you want to be.", "Your smile is contagious.",
        "You look great today.", "You're a smart cookie.", "I bet you make babies smile.", "You have impeccable manners.", "I like your style.", "You have the best laugh.", "I appreciate you.", "You are the most perfect you there is.",
        "You are enough.", "You're strong.", "Your perspective is refreshing.", "You're an awesome friend.", "You light up the room.", "You deserve a hug right now.", "You should be proud of yourself.", "You're more helpful than you realize.",
        "You have a great sense of humor.", "You've got all the right moves!", "Is that your picture next to charming in the dictionary?", "Your kindness is a balm to all who encounter it.", "You're all that and a super-size bag of chips.",
        "You're all that and a super-size bag of chips.", "You are brave.", "You're unlucky if you get this one. Fuck you kill yourself ape.", "You're even more beautiful on the inside than you are on the outside.", "You have the courage of your convictions.",
        "Your eyes are breathtaking.", "If cartoon bluebirds were real, a bunch of them would be sitting on your shoulders singing right now.", "You are making a difference.", "You're like sunshine on a rainy day.", "You bring out the best in other people.",
        "Your ability to recall random factoids at just the right time is impressive.", "You're a great listener.", "How is it that you always look great, even in sweatpants?", "Everything would be better if more people were like you!"]
        await self.bot.say(user.mention + " " + random.choice(a))

    @commands.command(pass_context=True)
    async def insult(self, ctx, user :discord.Member):
        """Insult a user hehexd!"""

        await asyncio.sleep(1)
        a = ["You smell like pickles tbh.", "I bet your dick doesnt touch the toilet water.",
             "You look like this guy. https://gyazo.com/bd8f5888138bb91683ee1bad64a3195b", "Your girl looks like this https://gyazo.com/e461c557bc2884ce41a164dcfe0e780b", "If I had a dollar for every time I wanted you to die I would be a millioniare.", "You wouldn't even be friends with steve erkel you mother fucker you.",
              "Aj has a better chance at getting a girl than you do.", "You look like Kanwar to be honest. #NoFlame", "Is your ass jealous of the amount of shit that just came out of your mouth?", "I'm not saying I hate you, but I would unplug your life support to charge my phone.", "Your birth certificate is an apology letter from the condom factory.",
              "I bet your brain feels as good as new, seeing that you never use it.", "You must have been born on a highway because that's where most accidents happen.", "What’s the difference between you and eggs? Eggs get laid and you don't.", "I could eat a bowl of alphabet soup and shit out a smarter statement than that.", "You're so ugly you scare the shit back into people.",
              "Your family tree must be a cactus because everybody on it is a prick.", "You're so ugly, when you popped out the doctor said Aww what a treasure and your mom said Yeah, lets bury it.", "I don't exactly hate you, but if you were on fire and I had water, I'd drink it.", "Maybe if you ate some of that makeup you could be pretty on the inside.",
              "Shut up, you'll never be the man your mother is.", "If you really want to know about mistakes, you should ask your parents.", "Roses are red violets are blue, God made me pretty, what happened to you?", "Hey, you have somthing on your chin... no, the 3rd one down", "You're the reason the gene pool needs a lifeguard.", "You have two brains cells, one is lost and the other is out looking for it.",
              "Why don't you slip into something more comfortable -- like a coma.", "You're so fat the only letters of the alphabet you know are KFC.", "Well I could agree with you, but then we'd both be wrong.", "You're not funny, but your life, now that's a joke.", "You are proof that God has a sense of humor.", "You're so ugly, when you got robbed, the robbers made you wear their masks.", "You're so ugly, the only dates you get are on a calendar.",
              "You're as useless as a knitted condom.", "You're so fat you need cheat codes to play Wii Fit", "You look like something I'd draw with my left hand.", "You didn't fall out of the stupid tree. You were dragged through dumbass forest.", "So you've changed your mind, does this one work any better?", "If your brain was made of chocolate, it wouldn't fill an M&M.", "I can explain it to you, but I can’t understand it for you.",
              "It's kinda sad watching you attempt to fit your entire vocabulary into a sentence.", "You are proof that evolution CAN go in reverse.", "Looks like you traded in your neck for an extra chin!", "You're a person of rare intelligence. It's rare when you show any.", "Your parents hated you so much your bath toys were an iron and a toaster", "Learn from your parents' mistakes - use birth control!", "Fuck you.",
              "Sausage Fest, yeah I can get you that.", "If you aren't GANG I don't fuck with you.", "You don't have severe depression so you're clearly a fucking homo.", "If I had to choose between getting cancer and being your friend, I would choose cancer.",
			  "Stay healthy, because you can kill yourself later.", "Do you realize that people just tolerate you?", "You’re not pretty enough to be this stupid.", "Anyone who ever loved you was obviously brain dead.", "If you were anymore inbred you would be a sandwich.", "Now I know why everybody talks about you behind your back.", "Dying would be the only way to improve yourself.", "You're a coffin dodging oxygen thief.",
			  "Your gene pool could use a little chlorine.", "Why play so hard to get when you’re already so hard to want.", "You clearly have not been burdened by an overabundance of education.", "What doesn’t kill you…disappoints me", "I treasure the time i don’t spend with you.", "Your parents should be ashamed they didn't abort you.", "I feel bad for your parents. They have to live with you, the ultimate disappointment.", "The air you breathe is wasted because it's keeping you alive."
			  "I hope your phone explodes in your pocket.", "Living life is hard, but living life with autism is harder. Give up already, kill yourself.", "Is your ass jealous of the amount of shit that just came out of your mouth?",
"Roses are red, violets are blue, I have 5 fingers, the 3rd ones for you.",
"Your birth certificate is an apology letter from the condom factory.",
"I wasn't born with enough middle fingers to let you know how I feel about you.",
"I’m jealous of all the people that haven't met you!",
"If you are going to be two faced, at least make one of them pretty.",
"I bet your brain feels as good as new, seeing that you never use it.",
"You must have been born on a highway because that's where most accidents happen.",
"I'm not saying I hate you, but I would unplug your life support to charge my phone.",
"Yo're so ugly, when your mom dropped you off at school she got a fine for littering.",
"You bring everyone a lot of joy, when you leave the room.",
"I'd like to see things from your point of view but I can't seem to get my head that far up my ass.",
"I could eat a bowl of alphabet soup and shit out a smarter statement than that.",
"Two wrongs don't make a right, take your parents as an example.",
"If laughter is the best medicine, your face must be curing the world.",
"If I wanted to kill myself I'd climb your ego and jump to your IQ.",
"Do you know how long it takes for your mother to take a crap? Nine months.",
"Your family tree must be a cactus because everybody on it is a prick.",
"You shouldn't play hide and seek, no one would look for you.",
"I'm no proctologist, but I know as asshole when I see one.",
"If you're gonna be a smartass, first you have to be smart. Otherwise you're just an ass.",
"You're so ugly, when you popped out the doctor said 'Aww what a treasure' and your mom said 'Yeah, lets bury it.'",
"I don't exactly hate you, but if you were on fire and I had water, I'd drink it.",
"It's better to let someone think you are an Idiot than to open your mouth and prove it.",
"Maybe if you ate some of that makeup you could be pretty on the inside.",
"If I gave you a penny for your thoughts, I'd get change.",
"Roses are red violets are blue, God made me pretty, what happened to you?",
"Shut up, you'll never be the man your mother is.",
"The last time I saw a face like yours I fed it a banana.",
"How many times do I have to flush to get rid of you?",
"Hey, you have somthing on your chin... no, the 3rd one down",
"I may love to shop but I'm not buying your bullshit.",
"The only way you'll ever get laid is if you crawl up a chicken's ass and wait.",
"Somewhere out there is a tree, tirelessly producing oxygen so you can breathe. I think you owe it an apology.",
"What are you going to do for a face when the baboon wants his butt back?",
"I have neither the time nor the crayons to explain this to you.",
"I'd slap you, but shit stains.",
"At least when I do a handstand my stomach doesn't hit me in the face.",
"If I were to slap you, it would be considered animal abuse!",
"You're as useless as a knitted condom. ",
"If you really want to know about mistakes, you should ask your parents.",
"It looks like your face caught on fire and someone tried to put it out with a hammer.",
"Well I could agree with you, but then we'd both be wrong.",
"Which sexual position produces the ugliest children? Ask your mother.",
"You're so fat, you could sell shade.",
"Why don't you slip into something more comfortable -- like a coma.",
"You may not have any enemies, but your friends don't really like you either.",
"You have two brains cells, one is lost and the other is out looking for it.",
"You're so fat the only letters of the alphabet you know are KFC.",
"You're not funny, but your life, now that's a joke.",
"Oh my God, look at you. Was anyone else hurt in the accident?",
"You look like something I'd draw with my left hand.",
"What are you doing here? Did someone leave your cage open?",
"You're the reason the gene pool needs a lifeguard.",
"There's only one problem with your face, I can see it.",
"You're so ugly, the only dates you get are on a calendar.",
"Some drink from the fountain of knowledge; you only gargled.",
"You didn't fall out of the stupid tree. You were dragged through dumbass forest.",
"You are proof that God has a sense of humor.",
"If I wanted to hear from an asshole, I'd fart.",
"If you spoke your mind, you'd be speechless.",
"Why don't you check eBay and see if they have a life for sale.",
"Your parents hated you so much your bath toys were an iron and a toaster",
"I'd like to kick you in the teeth, but that would be an improvement!",
"I thought you were attractive, but then you opened your mouth.",
"You're so fat you need cheat codes to play Wii Fit",
"You're so ugly, when you got robbed, the robbers made you wear their masks.",
"You're as bright as a black hole, and twice as dense.",
"You are proof that evolution CAN go in reverse.",
"Do you still love nature, despite what it did to you?",
"I'll never forget the first time we met, although I'll keep trying.",
"You're so ugly, you scared the crap out of the toilet.",
"Don't feel sad, don't feel blue, Frankenstein was ugly too.",
"I can explain it to you, but I can’t understand it for you.",
"You do realize makeup isn't going to fix your stupidity?",
"It's kinda sad watching you attempt to fit your entire vocabulary into a sentence.",
"Your face makes onions cry.",
"Shock me, say something intelligent.",
"Learn from your parents' mistakes - use birth control!",
"I've been called worse things by better people ",
"I fart to make you smell better.",
"Looks like you traded in your neck for an extra chin!",
"You're the reason they invented double doors!",
"I don't know what makes you so stupid, but it really works!",
"You're so ugly you make blind kids cry.",
"I love what you've done with your hair. How do you get it to come out of the nostrils like that?",
"You've got photographic memory but with the lens cover glued on.",
"Why dont you shut up and give that hole in your face a chance to heal.",
"You're a person of rare intelligence. It's rare when you show any.",
"I heard you went to a haunted house and they offered you a job.",
"If assholes could fly, this place would be an airport!",
"If your brain was made of chocolate, it wouldn't fill an M&M.",
"You're so fat, when you wear a yellow rain coat people scream ''taxi''.",
"You're so stupid you tried to wake a sleeping bag.",
"You look like a before picture.",
"Ever since I saw you in your family tree, I've wanted to cut it down.",
"Aww, it's so cute when you try to talk about things you don't understand.",
"You're as useless as a screen door on a submarine.",
"You only annoy me when you're breathing.",
"We all sprang from apes, but you didn't spring far enough.",
"Am I getting smart with you? How would you know?",
"You stare at frozen juice cans because they say, 'concentrate'.",
"You fear success, but really have nothing to worry about.",
"If brains were dynamite you wouldn't have enough to blow your nose.",
"It's better to keep your mouth shut and give the 'impression' that you're stupid than to open it and remove all doubt.",
"I heard your parents took you to a dog show and you won.",
"With a face like yours, I'd wish I was blind.",
"There are more calories in your stomach than in the local supermarket!",
"You're the best at all you do - and all you do is make people hate you.",
"So you've changed your mind, does this one work any better?",
"When was the last time you could see your whole body in the mirror?",
"You must have a very low opinion of people if you think they are your equals.",
"So, a thought crossed your mind? Must have been a long and lonely journey.",
"You're so dumb, your dog teaches you tricks.",
"Just wait till you can't fit your hand in the Pringles tubes, then where will you get your daily nutrition from?",
"Looks like you fell off the ugly tree and hit every branch on the way down.",
"What’s the difference between you and eggs? Eggs get laid and you don't.",
"Any similarity between you and a human is purely coincidental.",
"Looks aren't everything; in your case, they aren't anything",
"You so ugly when who were born the doctor threw you out the window and the window threw you back! ",
"You get as much action as a nine button on a microwave.",
"Did your parents keep the placenta and throw away the baby?",
"You're so fat a picture of you would fall off the wall!",
"You are so stupid, you'd trip over a cordless phone.",
"I can't imagine what qualities you may have that would compensate for your behavior in public.",
"You're so ugly, when you threw a boomerang it didn't come back.",
"Ordinarily people live and learn. You just live.",
"If my dog had your face, I would shave his butt and make him walk backwards.",
"You're so ugly Hello Kitty said goodbye to you.",
"You must be on the seafood diet. When you see food, you eat it!",
"Did your parents ever ask you to run away from home?",
"You must be the arithmetic man; you add trouble, subtract pleasure, divide attention, and multiply ignorance.",
"Your hockey team made you goalie so you'd have to wear a mask.",
"You have enough fat to make another human.",
"Your house is so dirty you have to wipe your feet before you go outside.",
"I thought of you all day today. I was at the zoo.",
"I heard you took an IQ test and they said you're results were negative.",
"You're not exactly bad looking. There's just one little problem between your ears - your face",
"Are you always an idiot, or just when I'm around?",
"I've seen people like you, but I had to pay admission!",
"Brains aren't everything. In your case they're nothing.",
"Nice tan, orange is my favorite color.",
"What's the difference between you and Hitler? Hitler knew when to kill himself.",
"You're so ugly, you had tinted windows on your incubator.",
"Don't you need a license to be that ugly?",
"100,000 sperm, you were the fastest?",
"I'd like to help you out. Which way did you come in?",
"Even if you were twice as smart, you'd still be stupid!",
"I hear the only place you're ever invited is outside.",
"If what you don't know can't hurt you, you're invulnerable.",
"Do you wanna lose ten pounds of ugly fat? Cut off your head",
"I may be drunk, but you're ugly, and tomorrow I'll be sober.",
"Are your parents siblings?",
"I may be fat, but you're ugly, and I can lose weight.",
"You couldn't pour water out of a boot if the instructions were on the heel.",
"You should eat some of your make up so you can be pretty on the inside.",
"Everyone who ever loved you was wrong.",
"Keep talking, someday you'll say something intelligent!",
"I was pro life before I met you.",
"I'd hit you but we don't hit little girls around here. ",
"I'm not saying you're fat, but it looks like you were poured into your clothes and someone forgot to say 'when'",
"You're so fat, you have to use a mattress as a maxi-pad.",
"You're a light eater alright. As soon as it gets light, you starts eating.",
"Do you ever wonder what life would be like if you'd had enough oxygen at birth?",
"You're so fat, your double chin has a double chin.",
"You act like your arrogance is a virtue.",
"It's too bad stupidity isn't painful.",
"You are depriving some poor village of its idiot.",
"Donated his brain to science before he was done using it.",
"You're so stupid, it takes you an hour to cook minute rice.",
"You are so old, when you were a kid rainbows were black and white.",
"Is that your face? Or did your neck just throw up?",
"If ignorance is bliss, you must be the happiest person on earth.",
"Your head is so big you have to step into your shirts.",
"I'm blonde, what's your excuse?",
"You have a very sympathetic face. It has everyone's sympathy.",
"Your breath is so stinky, we look forward to your farts.",
"You're so ugly, your mother had to tie a steak around your neck to get the dog to play with you!",
"If your brain exploded, it wouldn't even mess up your hair.",
"Your house is so nasty, I tripped over a rat, and a cockroach stole my wallet.",
"You have the perfect face for radio.",
"One more wrinkle and you'd pass for a prune.",
"Beauty is skin deep, but ugly is to the bone.",
"You're so fat, if you got your shoes shined, you'd have to take their word for it!",
"You are so old, your birth-certificate expired.",
"You must think you're strong, but you only smell strong.",
"For those who never forget a face, you are an exception.",
"Your dad's condom is a bigger than your personality.",
"You are so old, even your memory is in black and white.",
"I've seen transvestites who look more feminine than you.",
"You should spend less time at the gym and more time working on your personality.",
"You're so ugly words can't explain it. So I'll just go throw up.",
"If you were any dumber I would have to water you twice a week.",
"You may not be the best looking girl here, but beauty is only a light switch away!",
"You're so ugly you have to trick or treat over the phone.",
"If a crackhead saw you, he'd think he needs to go on a diet.",
"You're as useful as an ashtray on a motorcycle.",
"If I want your opinion, I'll give it to you.",
"You must have a Teflon brain, because nothing sticks.",
"You're so old, you walked into an antique shop and they put you on display. <Paste>",
"If you had another brain, it would be lonely.",
"You conserve toilet paper by using both sides.",
"You are so old, you fart dust.",
"Your ears are so big when you stand on a mountain they look like trophy handles.",
"Come again when you can't stay quite so long.",
"God made mountains, God made trees, God made you but we all make mistakes.",
"Just reminding u there is a very fine line between hobby and mental illness.",
"You're not pretty enough to be this stupid.",
"I'd say that you're funny but looks aren't everything.",
"Jesus loves you, everyone else thinks you're an asshole!",
"I've come across decomposed bodies that are less offensive than you are.",
"You're so fat, you have to strap a beeper on your belt to warn people you are backing up.",
"You couldn't hit water if you fell out of a boat.",
"Don't get insulted, but is your life devoted to spreading ignorance?",
"You occasionally stumble over the truth, but you quickly pick yourself up and carry on as if nothing happened.",
"A sharp tongue is no indication of a keen mind.",
"Your parents must be twins.",
"You're a prime candidate for natural de-selection.",
"You're so ugly, if you stuck your head out the window, they'd arrest you for mooning!",
"You'll make a great first wife some day.",
"People like you are the reason I work out.",
"You're so skinny, that you use a bandaid as a maxi-pad.",
"Yeah you're pretty, pretty stupid",
"I look into your eyes and get the feeling someone else is driving.",
"Your family tree must be a circle.",
"You're so fat, when you take a shower your feet don't get wet!",
"Gates are down, the lights are flashing, but the train isn't coming.",
"Being around you is like having a cancer of the soul.",
"You're so ugly, they call you the exterminator, because you kill bugs on sight.",
"You're shallower than a dry seabed.",
"If I had a dollar for every brain you didn't have, I'd have one dollar.",
"You have a face only a mother could love - and she hates it!",
"You're so fat, you sweat gravy.",
"Get off your high horse! You're too fat and the horse is in pain.",
"The clothes you wear are so ugly even a scarecrow wouldn't wear them.",
"You're so fat your shadow casts a shadow.",
"Nice shirt, what brand is it? Clearance?",
"You do realize that people just tolerate you?",
"It's hard to get the big picture when you have such a small screen.",
"Your ambition outweighs your relevant skills. ",
"You better hope you marry rich.",
"You're so fat, when you jump in the air, you get stuck!",
"The best part of you is still running down your old mans leg.",
"You know you're fat when no one has mentioned you're also ginger.",
"Your asinine simian countenance alludes that your fetid stench has anulled the anthropoid ape species diversity.",
"Your mom must have a really loud bark!",
"Two legged stool sample.",
"When it comes to IQ, you lose some every time you use the bathroom.",
"You prefer three left turns to one right turn.",
"Hold on, I'll go find you a tampon.",
"Your face is so ugly, when you cry the tears run UP your face.",
"Careful now, don't let your brains go to your head!",
"You're so fat your belly button has an echo echo echo...",
"Please tell me you don't home-school your kids.",
"You you were any more stupid, you'd have to be watered twice a week.",
"You're the reason why women earn 75 cents to the dollar.",
"Is your name Maple Syrup? It should be, you sap.",
"The sound of your urine hitting the urinal sounds feminine.",
"I wish you no harm, but it would have been much better if you had never lived.",
"Your brain must be made out of rocking horse shit.",
"Is your name Dan Druff? You get into people's hair.",
"You grow on people, like a wart!",
"Every time someone calls you fat I get so depress I cut myself... a piece of cake.",
"Go apologize to your mother for not being a stillborn.",
"Did you eat paint chips when you were a kid?",
"When anorexics see you, they think they need to go on a diet.",
"You're stupid because you're blonde. ",
"You're so fat that when you were diagnosed with a flesh eating bacteria - the doctors gave you 87 years to live.",
"You're so fat you've got more chins than a Hong Kong phone book.",
"You're so fat that when you farted you started global warming.",
"You're so fat the back of your neck looks like a pack of hot-dogs.",
"You're so fat that when you fell from your bed you fell from both sides.",
"You're so fat when you get on the scale it says *To be continued.*",
"You're so fat when you go swimming the whales start singing *We Are Family*.",
"You're so fat when you stepped on the scale Buzz Lightyear popped out and said *To infinity and beyond!*",
"You're so fat when you turn around people throw you a welcome back party.",
"You're so fat when you were in school you sat by everybody.",
"You're so fat when you went to the beach Greenpeace tried to drag your ass back in the water.",
"You're so fat when you went to the circus the little girl asked if she could ride the elephant.",
"You're so fat when you go on an airplane you have to pay baggage fees for your ass.",
"You're so fat whenever you go to the beach the tide comes in.",
"You're so fat I could slap your butt and ride the waves.",
"You're so fat I'd have to grease the door frame and hold a Twinkie on the other side just to get you through.",
"You're so dumb it took you 2 hours to watch 60 minutes.",
"You're so dumb that you thought The Exorcist was a workout video.",
"You're so ugly that you went to the salon and it took 3 hours just to get an estimate.",
"You're so ugly that even Scooby Doo couldn't solve that mystery.",
"What is the weighted center between Planet X and Planet Y? Oh it's YOU!",
":eggplant: :eggplant: :eggplant:",
"Your birth certificate is an apology letter from the condom factory.",
"I wasn't born with enough middle fingers to let you know how I feel about you.",
"You must have been born on a highway because that's where most accidents happen.",
"I'm jealous of all the people that haven't met you.",
"I bet your brain feels as good as new seeing that you never use it.",
"I'm not saying I hate you but I would unplug your life support to charge my phone.",
"You're so ugly when your mom dropped you off at school she got a fine for littering.",
"You bring everyone a lot of joy when you leave the room.",
"What's the difference between you and eggs? Eggs get laid and you don't.",
"You're as bright as a black hole and twice as dense.",
"I'd like to see things from your point of view but I can't seem to get my head that far up my ass.",
"Two wrongs don't make a right take your parents as an example.",
"You're the reason the gene pool needs a lifeguard.",
"If laughter is the best medicine your face must be curing the world.",
"You're so ugly when you popped out the doctor said *Aww what a treasure* and your mom said *Yeah lets bury it.*",
"I have neither the time nor the crayons to explain this to you.",
"You have two brains cells one is lost and the other is out looking for it.",
"How many times do I have to flush to get rid of you?",
"I don't exactly hate you but if you were on fire and I had water I'd drink it.",
"You shouldn't play hide and seek no one would look for you.",
"Some drink from the fountain of knowledge; you only gargled.",
"Roses are red violets are blue God made me pretty what happened to you?",
"It's better to let someone think you are an Idiot than to open your mouth and prove it.",
"Somewhere out there is a tree tirelessly producing oxygen so you can breathe. I think you owe it an apology.",
"The last time I saw a face like yours I fed it a banana.",
"The only way you'll ever get laid is if you crawl up a chicken's ass and wait.",
"Which sexual position produces the ugliest children? Ask your mother.",
"If you really want to know about mistakes you should ask your parents.",
"At least when I do a handstand my stomach doesn't hit me in the face.",
"If I gave you a penny for your thoughts I'd get change.",
"If I were to slap you it would be considered animal abuse.",
"Do you know how long it takes for your mother to take a crap? Nine months.",
"What are you going to do for a face when the baboon wants his butt back?",
"Well I could agree with you but then we'd both be wrong.",
"You're so fat you could sell shade.",
"It looks like your face caught on fire and someone tried to put it out with a hammer.",
"You're not funny but your life now that's a joke.",
"You're so fat the only letters of the alphabet you know are KFC.",
"Oh my God look at you. Was anyone else hurt in the accident?",
"What are you doing here? Did someone leave your cage open?",
"You're so ugly the only dates you get are on a calendar.",
"I can explain it to you but I can't understand it for you.",
"You are proof that God has a sense of humor.",
"If you spoke your mind you'd be speechless.",
"Why don't you check eBay and see if they have a life for sale.",
"If I wanted to hear from an asshole I'd fart.",
"You're so fat you need cheat codes to play Wii Fit",
"You're so ugly when you got robbed the robbers made you wear their masks.",
"Do you still love nature despite what it did to you?",
"You are proof that evolution CAN go in reverse.",
"I'll never forget the first time we met although I'll keep trying.",
"Your parents hated you so much your bath toys were an iron and a toaster",
"Don't feel sad don't feel blue Frankenstein was ugly too.",
"You're so ugly you scared the crap out of the toilet.",
"It's kinda sad watching you attempt to fit your entire vocabulary into a sentence.",
"I fart to make you smell better.",
"You're so ugly you make blind kids cry.",
"You're a person of rare intelligence. It's rare when you show any.",
"You're so fat when you wear a yellow rain coat people scream ''taxi''.",
"I heard you went to a haunted house and they offered you a job.",
"You look like a before picture.",
"If your brain was made of chocolate it wouldn't fill an M&M.",
"Aww it's so cute when you try to talk about things you don't understand.",
"I heard your parents took you to a dog show and you won.",
"You stare at frozen juice cans because they say *concentrate*.",
"You're so stupid you tried to wake a sleeping bag.",
"Am I getting smart with you? How would you know?",
"We all sprang from apes but you didn't spring far enough.",
"I'm no proctologist but I know as asshole when I see one.",
"When was the last time you could see your whole body in the mirror?",
"You must have a very low opinion of people if you think they are your equals.",
"So a thought crossed your mind? Must have been a long and lonely journey.",
"You're the best at all you do - and all you do is make people hate you.",
"Looks like you fell off the ugly tree and hit every branch on the way down.",
"Looks aren't everything; in your case they aren't anything.",
"You have enough fat to make another human.",
"You're so ugly when you threw a boomerang it didn't come back.",
"You're so fat a picture of you would fall off the wall!",
"Your hockey team made you goalie so you'd have to wear a mask.",
"Ordinarily people live and learn. You just live.",
"Did your parents ever ask you to run away from home?",
"I heard you took an IQ test and they said your results were negative.",
"You're so ugly you had tinted windows on your incubator.",
"Don't you need a license to be that ugly?",
"I'm not saying you're fat but it looks like you were poured into your clothes and someone forgot to say *when*",
"I've seen people like you but I had to pay admission!",
"I hear the only place you're ever invited is outside.",
"Keep talking someday you'll say something intelligent!",
"You couldn't pour water out of a boot if the instructions were on the heel.",
"Even if you were twice as smart you'd still be stupid!",
"You're so fat you have to use a mattress as a maxi-pad.",
"I may be fat but you're ugly and I can lose weight.",
"I was pro life before I met you.",
"What's the difference between you and Hitler? Hitler knew when to kill himself.",
"You're so fat your double chin has a double chin.",
"If ignorance is bliss you must be the happiest person on earth.",
"You're so stupid it takes you an hour to cook minute rice.",
"Is that your face? Or did your neck just throw up?",
"You're so ugly you have to trick or treat over the phone.",
"I'd hit you but we don't hit girls around here.",
"Dumbass.",
"Bitch.",
"I'd give you a nasty look but you've already got one.",
"If I wanted a bitch I'd have bought a dog.",
"Scientists say the universe is made up of neutrons protons and electrons. They forgot to mention morons.",
"Why is it acceptable for you to be an idiot but not for me to point it out?",
"Did you know they used to be called *Jumpolines* until your mum jumped on one?",
"You're not stupid; you just have bad luck when thinking.",
"I thought of you today. It reminded me to take the garbage out.",
"I'm sorry I didn't get that - I don't speak idiot.",
"Hey your village called – they want their idiot back.",
"I just stepped in something that was smarter than you… and smelled better too.",
"You're so fat that at the zoo the elephants started throwing you peanuts.",
"You're so fat every time you turn around it's your birthday.",
"You're so fat your idea of dieting is deleting the cookies from your internet cache.",
"You're so fat your shadow weighs 35 pounds.",
"You're so fat I could tell you to haul ass and you'd have to make two trips.",
"You're so fat I took a picture of you at Christmas and it's still printing.",
"You're so fat I tried to hang a picture of you on my wall and my wall fell over.",
"You're so fat Mount Everest tried to climb you.",
"You're so fat you can't even jump to a conclusion.",
"You're so fat you can't fit in any timeline.",
"You're so fat you can't fit in this joke.",
"You're so fat you don't skinny dip you chunky dunk.",
"You're so fat you fell in love and broke it.",
"You're so fat you go to KFC and lick other peoples' fingers.",
"You're so fat you got arrested at the airport for ten pounds of crack.",
"You're so fat you'd have to go to Sea World to get baptized.",
"You're so fat you have your own zip code.",
"You're so fat you have more rolls than a bakery.",
"You're so fat you don't have got cellulite you've got celluheavy.",
"You're so fat you influence the tides.",
"You're so fat you jumped off the Grand Canyon and got stuck.",
"You're so fat that you laid on the beach and Greenpeace tried to push you back in the water.",
"You're so fat you leave footprints in concrete.",
"You're so fat you need GPS to find your asshole.",
"You're so fat you pull your pants down and your ass is still in them.",
"You're so fat you show up on radar."]
        await self.bot.say(user.mention + " " + random.choice(a))


    @commands.command(pass_context=True)
    async def nickometer(self, ctx, nick=None):
        """Tells you how lame a person with this name is, 100% accurate."""
        if not nick:
            try:
                nick = ctx.message.author.nick
            except:
                nick = ctx.message.author.name
            else:
                if nick is None:
                    nick = ctx.message.author.name
        elif is_mention(nick):
            members = ctx.message.server.members
            user = discord.utils.get(members, id=getid(nick))
            if user:
                try:
                    nick = ctx.message.author.nick
                except:
                    nick = user.name
                else:
                    if nick is None:
                        nick = ctx.message.author.name
        originalNick = nick

        score = 0

        specialCost = [('69', 500),
                       ('dea?th', 500),
                       ('dark', 400),
                       ('n[i1]ght', 300),
                       ('n[i1]te', 500),
                       ('fuck', 500),
                       ('sh[i1]t', 500),
                       ('coo[l1]', 500),
                       ('kew[l1]', 500),
                       ('lame', 500),
                       ('dood', 500),
                       ('dude', 500),
                       ('[l1](oo?|u)[sz]er', 500),
                       ('[l1]eet', 500),
                       ('e[l1]ite', 500),
                       ('[l1]ord', 500),
                       ('pron', 1000),
                       ('warez', 1000),
                       ('xx', 100),
                       ('\\[rkx]0', 1000),
                       ('\\0[rkx]', 1000)]

        def multipleReplacer(in_dict):
            _matcher = re.compile('|'.join(in_dict.keys()))

            def predicate(s):
                return _matcher.sub(lambda m: in_dict[m.group(0)], s)
            return predicate

        letterNumberTranslator = multipleReplacer(dict(list(zip(
            '02345718', 'ozeasttb'))))
        for special in specialCost:
            tempNick = nick
            if special[0][0] != '\\':
                tempNick = letterNumberTranslator(tempNick)

            if tempNick and re.search(special[0], tempNick, re.IGNORECASE):
                score += special[1]

        # I don't really know about either of these next two statements,
        # but they don't seem to do much harm.
        # Allow Perl referencing
        nick = re.sub('^\\\\([A-Za-z])', '\1', nick)

        # C-- ain't so bad either
        nick = re.sub('^C--$', 'C', nick)

        # Punish consecutive non-alphas
        matches = re.findall('[^\w\d]{2,}', nick)
        for match in matches:
            score += slowPow(10, len(match))

        # Remove balanced brackets ...
        while True:
            nickInitial = nick
            nick = re.sub('^([^()]*)(\()(.*)(\))([^()]*)$', '\1\3\5', nick, 1)
            nick = re.sub('^([^{}]*)(\{)(.*)(\})([^{}]*)$', '\1\3\5', nick, 1)
            nick = re.sub(
                '^([^[\]]*)(\[)(.*)(\])([^[\]]*)$', '\1\3\5', nick, 1)
            if nick == nickInitial:
                break

        # ... and punish for unmatched brackets
        unmatched = re.findall('[][(){}]', nick)
        if len(unmatched) > 0:
            score += slowPow(10, len(unmatched))

        # Punish k3wlt0k
        k3wlt0k_weights = (5, 5, 2, 5, 2, 3, 1, 2, 2, 2)
        for i in range(len(k3wlt0k_weights)):
            hits = re.findall(repr(i), nick)
            if (hits and len(hits) > 0):
                score += k3wlt0k_weights[i] * len(hits) * 30

        # An alpha caps is not lame in middle or at end, provided the first
        # alpha is caps.
        nickOriginalCase = nick
        match = re.search('^([^A-Za-z]*[A-Z].*[a-z].*?)[-_]?([A-Z])', nick)
        if match:
            nick = ''.join([nick[:match.start(2)],
                            nick[match.start(2)].lower(),
                            nick[match.start(2) + 1:]])

        match = re.search('^([^A-Za-z]*)([A-Z])([a-z])', nick)
        if match:
            nick = ''.join([nick[:match.start(2)],
                            nick[match.start(2):match.end(2)].lower(),
                            nick[match.end(2):]])

        # Punish uppercase to lowercase shifts and vice-versa, modulo
        # exceptions above

        # the commented line is the equivalent of the original, but i think
        # they intended my version, otherwise, the first caps alpha will
        # still be punished
        # cshifts = caseShifts(nickOriginalCase);
        cshifts = caseShifts(nick)
        if cshifts > 1 and re.match('.*[A-Z].*', nick):
            score += slowPow(9, cshifts)

        # Punish lame endings
        if re.match('.*[XZ][^a-zA-Z]*$', nickOriginalCase):
            score += 50

        # Punish letter to numeric shifts and vice-versa
        nshifts = numberShifts(nick)
        if nshifts > 1:
            score += slowPow(9, nshifts)

        # Punish extraneous caps
        caps = re.findall('[A-Z]', nick)
        if caps and len(caps) > 0:
            score += slowPow(7, len(caps))

        # one trailing underscore is ok. i also added a - for parasite-
        nick = re.sub('[-_]$', '', nick)

        # Punish anything that's left
        remains = re.findall('[^a-zA-Z0-9]', nick)
        if remains and len(remains) > 0:
            score += 50 * len(remains) + slowPow(9, len(remains))

        # Use an appropriate function to map [0, +inf) to [0, 100)
        percentage = 100 * (1 + math.tanh((score - 400.0) / 400.0)) * \
            (1 - 1 / (1 + score / 5.0)) // 2

        # if it's above 99.9%, show as many digits as is interesting
        score_string = re.sub('(99\\.9*\\d|\\.\\d).*', '\\1', repr(percentage))

        await self.bot.say('***The "lame nick-o-meter" reading for '
                           '``"%s"`` is ``%s%%.``***' % (originalNick, score_string))

###################Beginning of defs ###########################

    async def _create_author(self, server, ctx, user):
        author = ctx.message.author.name
        if server.id not in self.data:
            self.data[server.id] = {}
            dataIO.save_json(self.JSON, self.data)
        if "user" not in self.data[server.id]:
            self.data[server.id]["user"] = {}
            dataIO.save_json(self.JSON, self.data)
        if author not in self.data[server.id]["user"]:
            self.data[server.id]["user"][author] = {}
            dataIO.save_json(self.JSON, self.data)
        if "married_to" not in self.data[server.id]["user"][author]:
            self.data[server.id]["user"][author]["married_to"] = {}
            dataIO.save_json(self.JSON, self.data)
        if user.name not in self.data[server.id]["user"][author]["married_to"]:
            self.data[server.id]["user"][author]["married_to"][user.name] = {}
        dataIO.save_json(self.JSON, self.data)
            #if author in self.data[server.id]["user"]:
            #   self.data[server.id]["user"][author]["married_to"] = user.name
            #   dataIO.save_json(self.JSON, self.data)
            #else:
            #   self.data[server.id]["user"] = author
            #   self.data[server.id]["user"][author]["married_to"] = user.name
            #   dataIO.save_json(self.JSON, self.data)


    async def _create_user(self, server, ctx, user):
        author = ctx.message.author.name
        if server.id not in self.data:
            self.data[server.id] = {}
            dataIO.save_json(self.JSON, self.data)
        if "user" not in self.data[server.id]:
            self.data[server.id]["user"] = {}
            dataIO.save_json(self.JSON, self.data)
        if user.name not in self.data[server.id]["user"]:
            self.data[server.id]["user"][user.name] = {}
            dataIO.save_json(self.JSON, self.data)
        if "married_to" not in self.data[server.id]["user"][user.name]:
            self.data[server.id]["user"][user.name]["married_to"] = {}
            dataIO.save_json(self.JSON, self.data)
        if author not in self.data[server.id]["user"][author]["married_to"]:
            self.data[server.id]["user"][user.name]["married_to"][author] = {}
        dataIO.save_json(self.JSON, self.data)
            #if author in self.data[server.id]["user"]:
            #   self.data[server.id]["user"][author]["married_to"] = user.name
            #   dataIO.save_json(self.JSON, self.data)
            #else:
            #   self.data[server.id]["user"] = author
            #   self.data[server.id]["user"][author]["married_to"] = user.name
            #   dataIO.save_json(self.JSON, self.data)

    async def _divorce(self, server, ctx, user):
        author = ctx.message.author.name
        del self.data[server.id]["user"][author]["married_to"][user.name]
        del self.data[server.id]["user"][user.name]["married_to"][author]
        dataIO.save_json(self.JSON, self.data)


############ End of defs ##################

def check_folder():
    if not os.path.exists('data/married'):
        print('Creating data/married folder...')
        os.makedirs('data/married')


def check_files():
    f = "data/drawing/eeee.json"
    if not fileIO(f, "check"):
        print("Creating eeee.json...")
        fileIO(f, "save", {})

    f = 'data/married/married.json'
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, {})
        print('Creating default married.json...')


def setup(bot):
    if pil_available is False:
        raise RuntimeError("You don't have Pillow installed, run\n```pip3 install pillow```And try again")
        return
    check_folder()
    check_files()
    n = Fun(bot)
    bot.add_cog(n)
