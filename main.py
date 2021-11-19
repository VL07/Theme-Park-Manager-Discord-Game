import discord
from discord_slash import SlashCommand, SlashContext
from discord.ext import commands
from logger import *

EMBED_COLOR = 0xffffff

def addFooter(embed: discord.Embed):
    embed.add_field(name="\u200B", value="Theme Park Manager", inline=False)

def getToken() -> str:
    f = open("secrets/token.txt", "r")
    t = f.read()
    f.close()
    return t

def main():
    client = commands.Bot(command_prefix=".")
    slash = SlashCommand(client, sync_commands=True)

    # Events
    @client.event
    async def on_ready():
        custom(f"{client.user} is now ready", "🤖")

    # Commands
    
    log("Adding commands")
    @slash.slash(name="Ping", description="Get the latency of the bot")
    async def ping(ctx: SlashContext):
        log("Pinged")
        embed = discord.Embed(title="🤖 Ping", description=f"The bots latency is `{round(client.latency * 1000)}ms`")
        addFooter(embed)
        await ctx.send(embed=embed)

    client.run(getToken())
    

if __name__ == "__main__":
    main()