import os
from decouple import config
import json
import discord
from discord.ext import commands
from mechanics import get_prefix

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix= get_prefix,intents = intents,help_command=None)

def loadEvents():
    for filename in os.listdir('events'):
        if filename.endswith('.py'):
            client.load_extension(f'events.{filename[:-3]}')

def loadCommands():
    for filename in os.listdir('commands'):
        if filename.endswith('.py'):
            client.load_extension(f'commands.{filename[:-3]}')

loadEvents()
loadCommands()

token = config("TOKEN_BOT")
client.run(token)