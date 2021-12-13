import discord
from discord.ext import commands
import json
from mechanics import saveFile,readFile

class GuildEvents(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        prefixs = readFile()
        prefixs[guild.id] = 'tb!'
        saveFile(prefixs)
    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        print()
        prefixs = readFile()
        del prefixs[guild.id]
        saveFile(prefixs)

        

def setup(client):
    client.add_cog(GuildEvents(client))