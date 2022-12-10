import discord
from discord.ext import commands

class Anunciar(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'anunciar')
    @commands.has_role(785650860125978635)
    async def anunciar(self,ctx,*,args):
        await ctx.message.delete()
        embed_message = discord.Embed(
            title = "🎮 │ **Anuncio   **",
            description = f"**{args}**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = ctx.guild.icon.replace(format="png").url)
        await ctx.send(embed = embed_message)
        await ctx.send('||@everyone||')

async def setup(client):
    await client.add_cog(Anunciar(client))