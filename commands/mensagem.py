import discord
from discord.ext import commands
from discord import app_commands

class Mensagem(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @app_commands.command(name = 'mensagem',description="Encaminha uma mensagem para o canal onde foi executado o comando.")
    async def mensagem(self,interaction: discord.Interaction,*,mensagem:str):
        embed_message = discord.Embed(
            title = f"🎅 │ **{interaction.guild.name}**",
            description = f"**{mensagem}**",
            color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = interaction.guild.icon.replace(format="png").url)
        await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
        await interaction.channel.send(embed=embed_message)
        
async def setup(client):
    await client.add_cog(Mensagem(client))