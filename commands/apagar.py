import discord
from discord.ext import commands
from discord import app_commands

class Apagar(commands.Cog):
    def __init__(self,client):
      self.client = client
    
    @app_commands.command(name = 'apagar',description="Apaga x mensagens no canal que foi executado o comando.")
    @app_commands.guild_only()
    async def apagar(self,interaction: discord.Interaction,quantidade:int):
      embed_message = discord.Embed(
        title = f"🎅 │ **{interaction.guild.name}**",
        description = f"**Apagando {quantidade} {'mensagem' if quantidade == 1 else 'mensagens'}!**",
        color = 0xFF0004
      )
      embed_message.set_thumbnail(url = interaction.guild.icon.replace(format="png").url)
      await interaction.response.send_message(embed = embed_message,ephemeral=True,delete_after=5)
      await interaction.channel.purge(limit = quantidade)

    @apagar.error
    async def on_apagar_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
      await interaction.guild.get_member(352240724693090305).send(error)
      await interaction.response.send_message(embed=discord.Embed(description="Aconteceu um erro interno ao executar o comando, o mesmo já foi passado para um responsavel.",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
    
async def setup(client):
    await client.add_cog(Apagar(client))