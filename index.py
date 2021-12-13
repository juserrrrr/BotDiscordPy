import os
from decouple import config
import json
import discord
from discord.ext import commands
from mechanics import loadCommands,loadEvents,get_prefix

intents = discord.Intents.default()
intents.members = True




client = commands.Bot(command_prefix= get_prefix,intents = intents,help_command=None)





loadEvents()
loadCommands()

token = config("TOKEN_BOT")
client.run(token)