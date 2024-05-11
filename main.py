# this is currently not tested and incomplete
# the config file should still be integrated

from __future__ import annotations

import asyncio
import discord

from discord.ext import commands

# missing contents
# DISCORD_API_TOKEN

if not DISCORD_API_TOKEN:
    raise ValueError("DISCORD_API_TOKEN is not set")

async def main():
    intents = discord.Intents().none()
    intents.message_content = True
    bot = commands.Bot(
        command_prefix = "/",
        intents = intents
    )

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!',f'{bot.user} is connected to the following guild: ', sep='\n')
        await bot.change_presence(status=discord.Status.online, activity=discord.Activity(name='generating AI replies'))
        for guild in bot.guilds:
            print(f'{guild.name} (id: {guild.id})')

    # command to test if bot is active and responding
    @bot.command()
    async def ping(ctx: commands.Context):
        await ctx.send("ping")

    await bot.load_extension("cogs.openttd")
    await bot.start(DISCORD_API_TOKEN)

asyncio.run(main())
