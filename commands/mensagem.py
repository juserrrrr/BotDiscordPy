import discord
from discord.ext import commands
from discord import app_commands

class Mensagem(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @app_commands.command(name = 'mensagem')
    @commands.has_role(785650860125978635)
    async def mensagem(self,interaction: discord.Interaction,*,mensagem:str):
        embed_message = discord.Embed(
            title = f"🎅 │ **{interaction.guild.name}**",
            description = f"**{mensagem}**",
            color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = interaction.guild.icon.replace(format="png").url)
        await interaction.response.send_message(embed = embed_message)
        

async def setup(client):
    await client.add_cog(Mensagem(client))