import discord
from discord.ext import commands
from discord import app_commands
import requests


class SetAvatar(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client

  def checkOwner(interaction: discord.Interaction) -> bool:
    return interaction.user == interaction.client.application.team.owner

  @app_commands.command(name='setavatar', description="Coloca uma imagem no perfil do bot.")
  @app_commands.check(checkOwner)
  async def setAvatar(self, interaction: discord.Interaction, url: str = 'https://i.imgur.com/zcJBDUq_d.webp?maxwidth=760&fidelity=grand'):
    # Procedimentos
    await interaction.response.defer(ephemeral=True)
    img = requests.get(url).content
    await interaction.client.user.edit(avatar=img)
    message = await interaction.followup.send(embed=discord.Embed(description="Comando executado com sucesso!", color=interaction.guild.me.color), ephemeral=True, wait=True, delete_after=5)
    await message.delete(delay=3)


async def setup(client: commands.Bot):
  await client.add_cog(SetAvatar(client))
