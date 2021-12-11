import discord
from discord.ext import commands

class Anunciar(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'anunciar')
    async def anunciar(self,ctx,*,args):
        await ctx.message.delete()
        embed_message = discord.Embed(
            title = "🎅 │ **Anuncio   **",
            description = f"**{args}**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = ctx.guild.icon_url_as(format='png'))
        message = await ctx.send(embed = embed_message)
        await ctx.send('||@everyone||')

def setup(client):
    client.add_cog(Anunciar(client))