import discord
from discord.ext import commands
from discord import app_commands

class Unmute(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @app_commands.command(name = 'unmute')
    @commands.has_role(785650860125978635)
    async def unmute(self,interaction: discord.Interaction):
        if not interaction.user.voice is None and interaction.user.voice.mute:
            await interaction.user.edit(mute=False)
            description_text = "Você foi desmutado."

        else:
            description_text = "Você não está em um canal de voz ou não está mutado."

        embed_message = discord.Embed(
            title = f"🎅 │ **{interaction.guild.name}**    ",
            description = f"**{description_text}**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = interaction.guild.icon.replace(format="png").url)
        message = await interaction.response.send_message(embed = embed_message)  
        await message.delete(delay=2)

async def setup(client):
    await client.add_cog(Unmute(client))