import discord
from discord.ext import commands

class Mensagem(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'mensagem')
    async def mensagem(self,ctx,*,args):
        await ctx.message.delete()  
        embed_message = discord.Embed(
            title = f"🎅 │ **{ctx.guild.name}**    ",
            description = f"**{args}**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = ctx.guild.icon_url_as(format='png'))
        await ctx.send(embed = embed_message)

def setup(client):
    client.add_cog(Mensagem(client))