import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from services.timbasService import timbasService

load_dotenv("config.env")

intents = discord.Intents.all()
client = commands.Bot(command_prefix= None,intents = intents,help_command=None)

async def loadEvents():
    for filename in os.listdir('events'):
        if filename.endswith('.py'):
           await client.load_extension(f'events.{filename[:-3]}')    

async def loadCommands():
    for filename in os.listdir('commands'):
        if filename.endswith('.py'):
           await client.load_extension(f'commands.{filename[:-3]}')

async def main ():  
    await loadEvents()
    await loadCommands()
    token = os.getenv("TOKEN_BOT_TEST")
    await client.start(token)

asyncio.run(main())