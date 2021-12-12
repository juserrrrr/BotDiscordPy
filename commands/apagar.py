import discord
from time import sleep
from discord.channel import _single_delete_strategy
from discord.ext import commands

class Apagar(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'apagar')
    async def apagar(self,ctx,arg:int):
        await ctx.message.delete()
        await ctx.channel.purge(limit = arg)
        embed_message = discord.Embed(
            title = f"🎅 │ **{ctx.guild.name}     **",
            description = f"**{arg} {'mensagem apagada' if arg == 1 else 'mensagens apagadas'} com sucesso**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = ctx.guild.icon_url_as(format='png'))
        message = await ctx.send(embed = embed_message)
        sleep(2)
        await message.delete()

def setup(client):
    client.add_cog(Apagar(client))