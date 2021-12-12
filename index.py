import os
import discord
from decouple import config
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

client = commands.Bot('tb!',intents = intents,help_command=None)

for filename in os.listdir('events'):
    if filename.endswith('.py'):
        client.load_extension(f'events.{filename[:-3]}')

for filename in os.listdir('commands'):
    if filename.endswith('.py'):
        client.load_extension(f'commands.{filename[:-3]}')

# for filename in os.listdir('tasks'):
#     if filename.endswith('.py'):
#         client.load_extension(f'tasks.{filename[:-3]}')

token = config("TOKEN_BOT")
client.run(token)