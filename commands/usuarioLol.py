import discord
from discord.ext import commands
from discord import app_commands
from services.lolService import lolService


class UsuarioLol(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client

  @app_commands.command(name='usuariolol', description="Mostra as informações de determinado usuario do lol")
  @app_commands.guild_only()
  async def usuarioLol(self, interaction: discord.Interaction, nick: str, tag: str):

    embed_message = discord.Embed(
        title="🔷 │ **Usuário não encotrado**",
        description="Por favor, tente novamente",
        color=0xFF0004
    )
    rankedSoloName = 'RANKED_SOLO_5x5'
    rankedFlexName = 'RANKED_FLEX_SR'

    embed_message.set_thumbnail(url=interaction.guild.icon.url)
    await interaction.response.defer()

    apiLol = lolService()
    account = apiLol.getAccount(nick, tag)
    dados = apiLol.getSummonerByPuuid(account.json().get('puuid'))

    if dados.status_code == 200:
      dados = dados.json()
      userId = dados.get('id')
      rankedDados = apiLol.getRankedStats(userId).json()

      for ranked in rankedDados:
        if ranked.get('queueType') == rankedSoloName:
          rankedDadosSolo = ranked
        elif ranked.get('queueType') == rankedFlexName:
          rankedDadosFlex = ranked

      soloDuoStats = f"{rankedDadosSolo.get('tier')} {rankedDadosSolo.get('rank')}"
      flexStats = f"{rankedDadosFlex.get('tier')} {rankedDadosFlex.get('rank')}"
      nomeUsuario = (account.json().get('gameName'), account.json().get('tagLine'))
      idIcon = dados.get('profileIconId')
      urlImage = apiLol.getUrlProfileIcon(idIcon)

      # EmbedChanged
      embed_message.add_field(name="Solo/Duo", value=soloDuoStats)
      embed_message.add_field(name="Flex", value=flexStats)
      embed_message.add_field(name="Level", value=dados.get('summonerLevel'))
      embed_message.set_thumbnail(url=urlImage)
      embed_message.title = f"🔷 │ **{nomeUsuario[0]}#{nomeUsuario[1]}**"
      embed_message.description = f"**Infomações sobre o jogador**"

    await interaction.edit_original_response(embed=embed_message)


async def setup(client: commands.Bot):
  await client.add_cog(UsuarioLol(client))
