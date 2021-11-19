import discord
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord.ext import commands
from logger import *
import pymongo
from pymongo import MongoClient
import time

EMBED_COLOR = 0xffffff
EMBED_ERROR_COLOR = 0xff0000

guild_ids = [770625249469399051]

def addFooter(embed: discord.Embed):
    embed.add_field(name="\u200B", value="Theme Park Manager", inline=False)

def noParkErrorEmbed():
    embed = discord.Embed(title="You don't own a park yet", description="But you can creat one by using the `/Found` command", color=EMBED_COLOR)
    addFooter(embed)
    return embed

def errorEmbed(description):
    embed = discord.Embed(title="Error", description=description, color=EMBED_ERROR_COLOR)
    addFooter(embed)
    return embed

def simpleEmbed(title, description):
    embed = discord.Embed(title=title, description=description, color=EMBED_COLOR)
    addFooter(embed)
    return embed

def getToken() -> str:
    f = open("secrets/token.txt", "r")
    t = f.read()
    f.close()
    return t

def getMongodb() -> str:
    f = open("secrets/mongodb.txt", "r")
    t = f.read()
    f.close()
    return t

def main():

    # Db init
    cluster = MongoClient(getMongodb())
    print(cluster)
    db = cluster["usersParks"]
    collection = db["usersParks"]

    def getDataById(id):
        results = collection.find({"_id": id})
        r = None
        for result in results:
            r = result
        return r

    # Bot init

    client = commands.Bot(command_prefix=".")
    slash = SlashCommand(client, sync_commands=True)

    # Events
    @client.event
    async def on_ready():
        custom(f"{client.user} is now ready", "🤖")

    # Commands
    
    log("Adding commands")
    @slash.slash(name="Ping", description="Get the latency of the bot", guild_ids=guild_ids)
    async def ping(ctx: SlashContext):
        log("Ping")
        embed = discord.Embed(title="🤖 Ping", description=f"The bots latency is `{round(client.latency * 1000)}ms`", color=EMBED_COLOR)
        addFooter(embed)
        await ctx.send(embed=embed)

    @slash.slash(name="Park", description="Get information about your park", guild_ids=guild_ids, options=[
        create_option(name="user", description="Enter the name of your park", option_type=6, required=False)
    ])

    async def _park(ctx: SlashContext, user=None):
        log("Park info")

        if not user: 
            user = ctx.author.id
        else:
            user = user.id

        data = getDataById(user)

        if not data:
            error("No park")
            await ctx.send(embed=noParkErrorEmbed())
            return

        park = data["parks"]
        park = park[list(park.keys())[0]]
        
        emded = discord.Embed(title=park["name"], description=park["description"], color=EMBED_COLOR)
        emded.add_field(name="Owner", value=f"<@{str(user)}>", inline=False)
        emded.add_field(name="Created", value=f"<t:{park['created']}:f>", inline=False)
        addFooter(emded)

        await ctx.send(embed=emded)

    @slash.slash(name="Found", description="Found your own theme park", guild_ids=guild_ids,  options=[
        create_option(name="name", description="Enter the name of your park", option_type=3, required=True),
        create_option(name="description", description="Enter the description of your park", option_type=3, required=True)
    ])
    async def found(ctx: SlashContext, name: str, description: str):

        data = getDataById(ctx.author.id)

        if data:
            if data["parks"]:
                error("already one park")
                await ctx.send(embed=errorEmbed("We currently only suport you having `1` park"))
                return

        print(len(name))
        if len(name) > 32 or len(description) > 64:
            error("to long name")
            await ctx.send(embed=errorEmbed("Name or descrition is to long. Max lengt for the name is `32` characters and max lengt for the description is `64` characters. "))
            return

        collection.insert_one({"_id": ctx.author.id, "parks": {name: {"name": name, "description": description, "created": round(time.time())}}})

        await ctx.send(embed=simpleEmbed("Successfully created you theme park", "You now own a themepark. Use `/Park` to view info about your new park."))




    client.run(getToken())
    

if __name__ == "__main__":
    main()