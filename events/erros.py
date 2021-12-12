import discord
from discord import message
from discord.ext import commands
import asyncio

class Error(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        if isinstance(error,commands.CommandNotFound):
            await ctx.message.delete()
            message = await ctx.send(f'{ctx.author.mention} Esse comando não existe!')
            await asyncio.sleep(2)
            await message.delete()
        
def setup(client):
    client.add_cog(Error(client))