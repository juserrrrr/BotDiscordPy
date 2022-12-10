import discord
from discord.ext import commands

class Message(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_message(self,message):
        if message == self.client.user or not message.content.startswith('tb!'):
            return
        if message.guild is None:
            return

async def setup(client):
    await client.add_cog(Message(client))