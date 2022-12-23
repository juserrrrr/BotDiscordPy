import discord
from discord.ext import commands
from discord import app_commands

class Registrar(commands.Cog):
    def __init__(self,client: discord.Client):
        self.client = client

    @app_commands.command(name = 'registrar',description="Adciona um usário ao cargo de crias.")
    @app_commands.guild_only
    async def registrar(self,interaction: discord.Interaction,usuario:discord.Member):
      #Procedimentos
      cargoCriaId = 785650374195019806
      cargoCria = interaction.guild.get_role(cargoCriaId)

      await usuario.add_roles(cargoCria)
      await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)

    @registrar.error
    async def on_registrar_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
      print(f"Aconteceu um erro no servidor [{interaction.guild.name}]\nErro: {error}")
      await interaction.response.send_message(embed=discord.Embed(description="Aconteceu um erro interno ao executar o comando.",color=interaction.guild.me.color),ephemeral=True,delete_after=4)

async def setup(client):
    await client.add_cog(Registrar(client))