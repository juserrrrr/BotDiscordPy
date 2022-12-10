import discord
from discord import message
from discord.ext import commands
import asyncio

class Error(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        await ctx.message.delete()
        if isinstance(error,commands.CommandNotFound):
            message_error = f'{ctx.author.mention} esse comando não existe!'
        elif isinstance(error, commands.MissingRequiredArgument):
            message_error = f'{ctx.author.mention} por favor, é preciso passar um argumento para o comando!'
        else:
            print(error)

        message = await ctx.send(message_error)
        await message.delete(delay=3)  

        
async def setup(client):
    await client.add_cog(Error(client))