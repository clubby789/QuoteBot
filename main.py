import discord
from discord import Member
from discord.ext import commands

bot = commands.Bot(command_prefix="#", case_insensitive=True, owner_ids=[85400548534145024])

import os
import dotenv

dotenv.load_dotenv("secret.env")
TOKEN = os.environ.get("bot_token")

from google.cloud import firestore
db = firestore.Client()

import random, string

def randomString(stringLength=10):
    '''
    Takes a string length.
    Returns a random string of upper/lowercase letters.
    '''
    letters = string.ascii_lowercase + string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def getQuote(id, guild):
    '''
    Takes a quote ID and queries the database for this quote.
    Returns a dict containing the information.
    '''
    docs = db.collection(u'quotes').where(u'id', u'==', int(id)).where(u'guild', u'==', int(guild)).stream()
    quote = next(docs).to_dict()
    # If this doesn't work ^^^^
    # Then use this vvvv
    # for doc in docs:
    #   quote = doc
    return quote

def createEmbed(id, guild):
    '''
    Takes a quote ID.
    Returns a discord.py embed object.
    '''
    quote = getQuote(id, guild)
    embed = discord.Embed(title=quote['author'][:-4], description=quote['content'], color=0xff0000, url=quote['url'])
    embed.set_thumbnail(url=quote['icon'])
    embed.add_field(name="Quote number", value=id, inline=False)
    return embed

@bot.event
async def on_ready():
        print("Logged on as {0.user.name}!".format(bot))
        await bot.change_presence(status=discord.Status('online'), activity=discord.Game(f"use {bot.command_prefix}help"))

@bot.command()
@commands.has_permissions(manage_roles=True, manage_channels=True)
async def setup(ctx):
    '''
    If user has correct permissions, create
    the quotes channel and role
    '''
    guild = ctx.message.guild
    message = ""

    channel_exists = False
    for channel in guild.channels:
        if channel.name == "quotes":
            channel_exists = True
    if not channel_exists:
        await guild.create_text_channel("quotes")
        message += "Created quotes channel. "
    else:
        message += "Quotes channel exists. "
    
    role_exists = False
    for role in guild.roles:
        if role.name == "Quoter":
            role_exists = True
    if not role_exists:
        await guild.create_role(name="Quoter",colour=discord.Colour(0xd00000))
        message += "Created 'Quoter' role."
    else:
        message += "Quoter role exists."

    await ctx.send(message)

@bot.command()
@commands.has_role("Quoter")
async def addQuote(ctx, id):
    '''
    Takes a message ID and creates a corresponding Firestore document,
    then sends the quote to the quotes channel
    '''
    msg = await ctx.fetch_message(int(id))
    guild = int(ctx.guild.id)

    quotes_ref = db.collection(u'quotes')
    docs = db.collection(u'quotes').where(u'guild', u'==', int(guild)).order_by(u'id', direction=firestore.Query.DESCENDING).limit(1)
    result = docs.stream()

    r = next(result).to_dict()
    quoteId = int(r['id']) + 1
    author = msg.author.display_name + msg.author.discriminator
    icon = msg.author.avatar_url
    content = msg.content
    url = msg.jump_url

    quote = {'id': quoteId, 'author': author, 'content': content, 'guild': guild, 'icon': str(icon), 'url': url}
    quotes_ref.document(randomString(20)).set(quote)

    embed = createEmbed(quoteId, guild)
    for channel in ctx.guild.channels:
        if channel.name == "quotes":
            await channel.send(embed=embed)
    await ctx.send("Created quote {0}".format(quote['id']))

@bot.command()
async def quote(ctx, id):
    '''
    Takes a quote ID, gets an embed.
    Sends the embed to the channel.
    '''
    embed = createEmbed(id, int(ctx.guild.id))
    await ctx.send(embed=embed)

bot.run(TOKEN)
