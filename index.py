import os
from decouple import config
import json
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

def get_prefix(client,message):
    with open('prefix_servers.json','r') as file:
        Prefixs = json.load(file)
    return Prefixs[str(message.guild.id)]

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