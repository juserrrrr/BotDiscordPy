import discord
from discord.ext import commands
import asyncio

class Ready(commands.Cog):# MELHORAR ESSE CODIGO TB POR FAVOR!
    def __init__(self,client):
        self.client = client

    async def precenses_update(self):#Lembrar de atualizar isso depois
        while not self.client.is_closed():
            timer = 20
            await self.client.change_presence(activity=discord.Streaming(name="Estou de volta",url="https://www.twitch.tv/juserrrrr"))
            await asyncio.sleep(timer)
            await self.client.change_presence(activity=discord.Streaming(name="v0.4",url="https://www.twitch.tv/juserrrrr"))
            await asyncio.sleep(timer)
            await self.client.change_presence(activity=discord.Streaming(name="prefixo: tb!",url="https://www.twitch.tv/juserrrrr"))
            await asyncio.sleep(timer)
            await self.client.change_presence(activity=discord.Streaming(name=f"{len(self.client.users)} membros",url="https://www.twitch.tv/juserrrrr"))
            await asyncio.sleep(timer)
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        await self.client.tree.sync()
        self.client.loop.create_task(Ready.precenses_update(self))
        print(f"Entrei como o bot {self.client.user.name} e estou presente em {len(self.client.guilds)} {'servidor.' if len(self.client.guilds) == 1 else'servidores.'}")


async def setup(client):
    await client.add_cog(Ready(client))