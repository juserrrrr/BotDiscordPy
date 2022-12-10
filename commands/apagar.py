import discord
from discord.ext import commands

class Apagar(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'apagar')
    @commands.has_role(785650860125978635)
    async def apagar(self,ctx,arg:int):
        await ctx.message.delete()
        await ctx.channel.purge(limit = arg)
        embed_message = discord.Embed(
            title = f"🎅 │ **{ctx.guild.name}     **",
            description = f"**{arg} {'mensagem apagada' if arg == 1 else 'mensagens apagadas'} com sucesso!**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = ctx.guild.icon.replace(format="png").url)
        message = await ctx.send(embed = embed_message)
        await message.delete(delay=2)


async def setup(client):
    await client.add_cog(Apagar(client))