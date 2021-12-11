import discord
from discord.ext import commands

class Ready(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        await self.client.change_presence(activity=discord.Streaming(name="Estou de volta!",url="https://www.twitch.tv/juserrrrr"))
        print(f"Entrei como o bot {self.client.user.name} e estou presente em {len(self.client.guilds)} {'servidor.' if len(self.client.guilds) == 1 else'servidores.'}")


def setup(client):
    client.add_cog(Ready(client))