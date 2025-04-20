import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv(".env")

intents = discord.Intents.all()
client = commands.Bot(command_prefix=None, intents=intents, help_command=None)

env_type = os.getenv("ENV_TYPE", "DEVELOPMENT").upper()


async def loadEvents():
  for filename in os.listdir('events'):
    if filename.endswith('.py'):
      await client.load_extension(f'events.{filename[:-3]}')


async def loadCommands():
  for filename in os.listdir('commands'):
    if filename.endswith('.py'):
      await client.load_extension(f'commands.{filename[:-3]}')


async def main():
  await loadEvents()
  await loadCommands()

  token = os.getenv(
      "TOKEN_BOT_TEST") if env_type == "DEVELOPMENT" else os.getenv("TOKEN_BOT")
  if not token:
    raise ValueError(f"Token não encontrado para o ambiente {env_type}")

  await client.start(token)

asyncio.run(main())
