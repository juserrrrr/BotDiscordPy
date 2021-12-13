import discord
from discord.ext import commands
import asyncio
import json
from mechanics import saveFile,readFile

class Ready(commands.Cog):# MELHORAR ESSE CODIGO TB POR FAVOR!
    def __init__(self,client):
        self.client = client

    def checkServersPrefix(self):
        change = False
        prefixs = readFile()
        for guild in self.client.guilds:
            if not str(guild.id) in list(prefixs.keys()):
                change = True
                prefixs[guild.id] = 'tb!'
        if change:
            saveFile(prefixs)
        return prefixs

    def getAll_id_servers(self): 
        list_guild = []
        for guild in self.client.guilds:
            list_guild.append(guild.id) 
        return list_guild
    def clearInactiveServers(self,prefixs):
        
        change = False
        list_guild = Ready.getAll_id_servers(self)
        for id in list(prefixs.keys()):
            if not id in list_guild:
                change = True
                del prefixs[id]
        if change:
            saveFile(prefixs)

    async def precenses_update(self):#Lembrar de atualizar isso depois
        while not self.client.is_closed():
            timer = 20
            await self.client.change_presence(activity=discord.Streaming(name="Estou de volta",url="https://www.twitch.tv/juserrrrr"))
            await asyncio.sleep(timer)
            await self.client.change_presence(activity=discord.Game(name="v0.1"))
            await asyncio.sleep(timer)
            await self.client.change_presence(activity=discord.Game(name="prefixo: tb!"))
            await asyncio.sleep(timer)
            await self.client.change_presence(activity=discord.Streaming(name=f"{len(self.client.users)} membros",url="https://www.twitch.tv/juserrrrr"))
            await asyncio.sleep(timer)
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        self.client.loop.create_task(Ready.precenses_update(self))
        prefixs = Ready.checkServersPrefix(self)
        Ready.clearInactiveServers(self,prefixs)
        print(f"Entrei como o bot {self.client.user.name} e estou presente em {len(self.client.guilds)} {'servidor.' if len(self.client.guilds) == 1 else'servidores.'}")


def setup(client):
    client.add_cog(Ready(client))