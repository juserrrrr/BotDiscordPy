import discord
from discord.ext import commands
from discord import app_commands

class Registrar(commands.Cog):
    def __init__(self,client: commands.Bot):
        self.client = client


    @app_commands.command(name = 'registrar',description="Adciona um usário ao cargo de crias.")
    @app_commands.guild_only()
    async def registrar(self,interaction: discord.Interaction,usuario:discord.Member):
      #Procedimentos
      cargoCriaId = 785650374195019806
      cargoCria = interaction.guild.get_role(cargoCriaId)

      await usuario.add_roles(cargoCria)
      await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)

async def setup(client: commands.Bot):
    await client.add_cog(Registrar(client))