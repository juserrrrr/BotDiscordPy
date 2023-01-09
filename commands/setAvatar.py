import discord
from discord.ext import commands
from discord import app_commands
import requests

class SetAvatar(commands.Cog):
    def __init__(self,client: discord.Client):
        self.client = client

    @app_commands.command(name = 'setavatar',description="Adciona um usário ao cargo de crias.")
    @app_commands.guild_only()
    async def setAvatar(self,interaction: discord.Interaction,url:str):
      #Procedimentos
      img = requests.get(url).content
      self.client.user.edit(avatar=img)
      await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)

    @setAvatar.error
    async def on_setAvatar_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
      await interaction.guild.get_member(352240724693090305).send(error)
      await interaction.response.send_message(embed=discord.Embed(description="Aconteceu um erro interno ao executar o comando, o mesmo já foi passado para um responsavel.",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
async def setup(client):
    await client.add_cog(SetAvatar(client))