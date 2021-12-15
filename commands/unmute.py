import discord
from discord.ext import commands

class Unmute(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'unmute')
    async def unmute(self,ctx):
        await ctx.message.delete() 
        if not ctx.author.voice is None and ctx.author.voice.mute:
            await ctx.author.edit(mute=False)
            description_text = "Você foi desmutado."
        else:
            description_text = "Você não está em um canal de voz ou não está mutado."

        embed_message = discord.Embed(
            title = f"🎅 │ **{ctx.guild.name}**    ",
            description = f"**{description_text}**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = ctx.guild.icon_url_as(format='png'))
        msg = await ctx.send(embed = embed_message)  
        await msg.delete(delay=2)

def setup(client):
    client.add_cog(Unmute(client))