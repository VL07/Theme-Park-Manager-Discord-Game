import discord
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord.ext import commands
from logger import *
import pymongo
from pymongo import MongoClient
import time
import math
import rideData

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

        if r:
            park = r["parks"][0]

            tb = round(time.time()) - park["moneyLastUpdated"]

            hours = math.floor(tb / 3600)
            overflow = tb - hours * 3600

            log(hours)
            log(overflow)

            print(tb)
            collection.update_one({"_id": id, "parks.name": park["name"]}, 
            {
                "$set": 
                {
                    "parks.$.moneyLastUpdated": round(time.time()) - overflow 
                },
                "$inc":
                {
                    "parks.$.money": park["iph"] * hours if hours else 0
                }
            }
            )
            r = collection.find({"_id": id})
            for result in r:
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

        park = data["parks"][0]
        print(park.items())

        emded = discord.Embed(title=park["name"], description=park["description"], color=EMBED_COLOR)
        emded.add_field(name="Money", value=f"{str(park['money'])}$", inline=False)
        emded.add_field(name="Income per hour", value=f"{str(park['iph'])}/h", inline=False)

        emded.set_thumbnail(url=ctx.author.avatar_url)

        emded.add_field(name="Expansions", value=f"{str(park['expansions'])}/36", inline=False)
        emded.add_field(name="Used tiles", value=f"{str(park['usedTiles'])}/{str(256*park['expansions'])}", inline=False)

        emded.add_field(name="Rides", value=f"{str(len(park['rides']))} rides", inline=False)

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

        collection.insert_one({
            "_id": ctx.author.id,
            "parks": [{
                "name": name, 
                "description": description, 
                "created": round(time.time()),
                "money": 11000,
                "expansions": 4,
                "iph": 10,
                "usedTiles": 0,
                "rides": {},
                "upgrades": {},
                "moneyLastUpdated": round(time.time())
            }]
        })

        await ctx.send(embed=simpleEmbed("Successfully created you theme park", "You now own a themepark. Use `/Park` to view info about your new park."))

    @slash.slash(name="Shop", description="Buy new rides and rollercoasters here", guild_ids=guild_ids)
    async def shop(ctx: SlashContext):
        data = getDataById(ctx.author.id)
        park = data["parks"][0]

        embed = discord.Embed(title="Shop", description=f"You currently have `{park['money']}`$", color=EMBED_COLOR)

        rides = []
        for category in rideData.rides:
            l = ""
            for ride in category:
                l += f'**{ride["name"]}**\nPrice: `{str(ride["price"])}$`\nMoney/h: `{str((ride["dep"] * ride["seats"]) * (ride["stats"]["excitement"] / 5))}$`\n'
            rides.append(l)
        
        embed.add_field(name="Gentle rides", value=rides[0] if rides[0] else "More rides comming soon")
        embed.add_field(name="Intense rides", value=rides[1] if rides[1] else "More rides comming soon")
        embed.add_field(name="Roller coasters", value=rides[2] if rides[2] else "More rides comming soon")

        embed.add_field(name="\u200B", value="Use `/ride info` to get more info about a spesific ride")
        addFooter(embed)

        await ctx.send(embed=embed)


    client.run(getToken())
    

if __name__ == "__main__":
    main()