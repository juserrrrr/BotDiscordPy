import discord
from discord.ext import commands
from discord import app_commands
from services.timbasService import timbasService


class UsuarioLol(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client

  @app_commands.command(name='usuariolol', description="Mostra as informações de determinado usuario do lol")
  @app_commands.guild_only()
  async def usuarioLol(self, interaction: discord.Interaction, nick: str, tag: str):

    embed_message = discord.Embed(
        title="🔷 │ **Usuário não encontrado**",
        description="Por favor, tente novamente",
        color=0xFF0004
    )
    embed_message.set_thumbnail(url=interaction.guild.icon.url)
    await interaction.response.defer()

    timbas = timbasService()
    response = timbas.getPlayerLol(nick, tag)

    if response and response.status_code == 200:
      data = response.json()
      solo = data.get('solo', {})
      flex = data.get('flex', {})

      solo_tier = solo.get('tier', 'Unranked')
      solo_rank = solo.get('rank', '')
      flex_tier = flex.get('tier', 'Unranked')
      flex_rank = flex.get('rank', '')

      soloDuoStats = f"{solo_tier} {solo_rank}".strip() if solo_tier != 'Unranked' else 'Unranked'
      flexStats = f"{flex_tier} {flex_rank}".strip() if flex_tier != 'Unranked' else 'Unranked'

      embed_message.add_field(name="Solo/Duo", value=soloDuoStats)
      embed_message.add_field(name="Flex", value=flexStats)
      embed_message.add_field(name="Level", value=data.get('summonerLevel'))
      embed_message.set_thumbnail(url=data.get('profileIconUrl', interaction.guild.icon.url))
      embed_message.title = f"🔷 │ **{data.get('gameName')}#{data.get('tagLine')}**"
      embed_message.description = "**Informações sobre o jogador**"

    await interaction.edit_original_response(embed=embed_message)


async def setup(client: commands.Bot):
  await client.add_cog(UsuarioLol(client))
