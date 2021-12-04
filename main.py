import discord
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord.ext import commands
from logger import *
from pymongo import MongoClient
import time
import math
import rideData

EMBED_COLOR = 0x36393F
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
        create_option(name="user", description="Enter the owners name", option_type=6, required=False)
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
        emded.add_field(name="💰 Money", value=f"{str(park['money'])}$\n", inline=False)
        emded.add_field(name="⏱ Income per hour", value=f"{str(park['iph'])}/h\n", inline=False)

        emded.set_thumbnail(url=ctx.author.avatar_url)

        emded.add_field(name="🔳 Expansions", value=f"{str(park['expansions'])}/36\n", inline=False)
        emded.add_field(name="⬜️ Used tiles", value=f"{str(park['usedTiles'])}/{str(256*park['expansions'])}\n", inline=False)

        emded.add_field(name="🎡 Rides", value=f"{str(len(park['rides']))} rides\n", inline=False)

        emded.add_field(name="😀 Owner", value=f"<@{str(user)}>\n", inline=False)
        emded.add_field(name="📆 Created", value=f"<t:{park['created']}:f>\n", inline=False)
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
                "rides": [],
                "upgrades": [],
                "moneyLastUpdated": round(time.time())
            }]
        })

        await ctx.send(embed=simpleEmbed("Successfully created you theme park", "You now own a themepark. Use `/Park` to view info about your new park."))

    @slash.slash(name="Shop", description="Buy new rides and rollercoasters here", guild_ids=guild_ids)
    async def shop(ctx: SlashContext):
        data = getDataById(ctx.author.id)

        if not data:
            error("No park")
            await ctx.send(embed=noParkErrorEmbed())
            return

        park = data["parks"][0]

        embed = discord.Embed(title="Shop", description=f"You currently have `{park['money']}`$", color=EMBED_COLOR)

        rides = []
        for category in rideData.rides:
            l = ""
            for ride in category:
                m = round((ride["dep"] * ride["seats"]) * (ride["stats"]["excitement"] / 10) * ((100 / min([len(park["rides"]) + 1, 100])) / 100))
                l += f'**{ride["name"]}**\nPrice: `{str(ride["price"])}$`\nMoney/h: `{str(m)}$`\nSize: `{str(ride["size"]["x"])}x{str(ride["size"]["y"])} ({str(ride["size"]["x"] * ride["size"]["y"])} tiles)`\n`/buy {ride["id"]}`\n\n'
            rides.append(l)
        
        embed.add_field(name="Gentle rides", value=rides[0] if rides[0] else "More rides comming soon")
        embed.add_field(name="Intense rides", value=rides[1] if rides[1] else "More rides comming soon")
        embed.add_field(name="Roller coasters", value=rides[2] if rides[2] else "More rides comming soon")

        embed.add_field(name="\u200B", value="Use `/rideinfo <ride id>` to get more info about a spesific ride")
        addFooter(embed)

        await ctx.send(embed=embed)

    @slash.slash(name="Buy", description="Buy anything from the shop", guild_ids=guild_ids, options=[
        create_option(name="ride", description="Enter the id of the ride", option_type=3, required=True)
    ])
    async def buy(ctx: SlashContext, ride: str):
        exists = False
        r = None
        ride = ride.lower()
        for category in rideData.rides[0:1]:
            for _ride in category:
                if _ride["id"] == ride:
                    exists = True
                    r = _ride
                    break
            if exists:
                break
        
        isARollercoaster = False

        for _ride in rideData.rides[2]:
            if exists: break
            if _ride["id"] == ride:
                exists = True
                r = _ride
                isARollercoaster = True
                break
        
        if not exists:
            await ctx.send(embed=errorEmbed(f"`{ride}` is not a valid ride! Use `/shop` to get a list of all rides"))
            return

        ride = r

        data = getDataById(ctx.author.id)

        if not data:
            error("No park")
            await ctx.send(embed=noParkErrorEmbed())
            return

        park = data["parks"][0]

        if len(park["rides"]) == 50:
            await ctx.send(embed=errorEmbed(f"You have reached the limit of `50` rides in your park"))
            return

        if park["money"] < ride["price"]:
            await ctx.send(embed=errorEmbed(f"You need `{str(ride['price'] - park['money'])}$` more money to buy `{ride['name']}`"))
            return

        if (park["usedTiles"] + ride["size"]["total"]) > park["expansions"] * 256:
            await ctx.send(embed=errorEmbed(f"You need `{str(park['usedTiles'] + ride['size']['total'] - park['expansions'] * 256)} tiles` more space to buy `{ride['name']}`"))
            return

        iph = round((ride["dep"] * ride["seats"]) * (ride["stats"]["excitement"] / 10) * ((100 / min([len(park["rides"]) + 1, 100])) / 100))

        collection.update_one({"_id": ctx.author.id, "parks.name": park["name"]}, 
            {
                "$push": 
                {
                    "parks.$.rides": 
                    {
                        "id": ride["id"], 
                        "name": ride["name"],
                        "created": round(time.time()),
                        "iph": iph
                    }
                },
                "$inc":
                {
                    "parks.$.iph": iph,
                    "parks.$.usedTiles": ride["size"]["total"]
                }
            }
            )

        embed = simpleEmbed("Successfully bought new ride", f"`{ride['name']}` was successfully built. You now earn `{str(iph + park['iph'])}$` per hour")
        await ctx.send(embed = embed)

    @slash.slash(name="Rideinfo", description="Get more information about a ride", guild_ids=guild_ids, options=[
        create_option(name="ride", description="Enter the id of the ride", option_type=3, required=True)
    ])
    async def rideinfo(ctx: SlashContext, ride: str):
        ride = ride.lower()
        exists = False
        r = None
        for category in rideData.rides[0:1]:
            for _ride in category:
                if _ride["id"] == ride:
                    exists = True
                    r = _ride
                    break
            if exists:
                break

        if not exists:
            await ctx.send(embed=errorEmbed(f"`{ride}` is not a valid ride! Use `/shop` to get a list of all rides"))
            return

        embed = discord.Embed(title=ride, description=f"Showing info for `{ride}`", color=EMBED_COLOR)
        embed.add_field(name="Price", value=f"`{str(r['price'])}$`")
        embed.add_field(name="Default entry price", value=f"`{str(r['dep'])}$`")
        embed.add_field(name="Seats", value=f"`{str(r['seats'])}$`")
        embed.add_field(name="Size", value=f"`{str(r['size']['x'])}x{str(r['size']['y'])} ({str(r['size']['total'])} tiles)`")
        embed.add_field(name="Stats", value=f"""Excitement: `{str(r['stats']['excitement'])}\n`Intensity: `{str(r['stats']['intensity'])}\n`Nausea: `{str(r['stats']['nausea'])}`""")

        addFooter(embed)

        await ctx.send(embed=embed)
    
    @slash.slash(name="Rides", description="Get info about all your rides", guild_ids=guild_ids, options=[
        create_option(name="user", description="Enter the name of the owner of the park you want to get info about", option_type=6, required=False)
    ])
    async def rides(ctx: SlashContext, user=None):

        if not user:
            user = ctx.author

        data = getDataById(user.id)

        if not data:
            error("No park")
            await ctx.send(embed=noParkErrorEmbed())
            return

        embed = discord.Embed(title="Rides", description=f"All of {user.mention}s rides ", color=EMBED_COLOR)
        for ride in data["parks"][0]["rides"]:
            embed.add_field(name=ride["name"], value=f"Income per hour: `{str(ride['iph'])}$`\nBuilt: <t:{str(ride['created'])}:f>")

        addFooter(embed)

        await ctx.send(embed=embed)

    @slash.slash(name="Github", description="Get link to this bots Github page", guild_ids=guild_ids)
    async def github(ctx: SlashContext):
        embed = discord.Embed(title="Github", description="[Here](https://github.com/VL07/Theme-Park-Manager-Discord-Game) is the bots repository!", url="https://github.com/VL07/Theme-Park-Manager-Discord-Game")
        addFooter(embed)
        await ctx.send(embed=embed)
        


    client.run(getToken())
    

if __name__ == "__main__":
    main()