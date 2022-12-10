import discord
from discord.ext import commands

class Unmute(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'unmute')
    @commands.has_role(785650860125978635)
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
        embed_message.set_thumbnail(url = ctx.guild.icon.replace(format="png").url)
        message = await ctx.send(embed = embed_message)  
        await message.delete(delay=2)

async def setup(client):
    await client.add_cog(Unmute(client))