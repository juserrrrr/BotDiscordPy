from discord import app_commands
from discord.ext import commands
from .utilsPerson.viewInterfaces import *
from .utilsPerson.leagueVerification import *
from .utilsPerson.utilsFunc import *


class CriarPerson(commands.Cog):
  def __init__(self, client: discord.Client):
    self.client = client
    # Função para gerar a mensagem embed dos jogadores confirmados

  def generateEmbedConfirmed(self, confirmed: list, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int]):
    stringConfirmed = generateTextUsersLeague(confirmed, onlineMode, formate)
    embedMessage = discord.Embed(
        description=f"\n```{stringConfirmed}```",
        color=0xFF0004,
    )
    embedMessage.set_footer(
        text="⏳Aguardando jogadores...")
    return embedMessage

  def embedMessageTeam(self, blueUsers, redUsers):
    embedMessage = discord.Embed(
        title="**Partida personalizada ⚔️ **",
        description="**League of Legends**",
        color=0xFF0004,
    )
    embedMessage.set_footer(
        text="⏳Aguardando início da partida")
    embedMessage.add_field(
        name="**Time Azul 🔵**", value=f"{blueUsers}", inline=True)
    embedMessage.add_field(
        name="**Time Vermelho 🔴**", value=f"{redUsers}", inline=True)
    embedMessage.set_image(url='https://i.imgur.com/kNWEtds.png')
    return embedMessage

  def embedMessageWinner(self, winnerTeam, blueUsers, redUsers):
    iconWinner = '🏆'
    iconLoser = '❌'
    stateBlue = iconWinner if winnerTeam == 'blue' else iconLoser
    stateRed = iconWinner if winnerTeam == 'red' else iconLoser
    embed_message = discord.Embed(
        title="**Partida personalizada ⚔️ **",
        description="**League of Legends**",
        color=0xFF0004,
    )
    embed_message.set_footer(
        text="=✅Finalizada")
    embed_message.add_field(
        name=f"**Time Azul 🔵[{stateBlue}]**", value=f"{blueUsers}", inline=True)
    embed_message.add_field(
        name=f"**Time Vermelho 🔴[{stateRed}]**", value=f"{redUsers}", inline=True)
    embed_message.set_image(url='https://i.imgur.com/kNWEtds.png')
    return embed_message

  @app_commands.command(name='criarperson', description="Cria uma mensagem para que os usuarios possam entrar no sorteio da partida personalizada.")
  @app_commands.guild_only()
  @app_commands.rename(onlineMode="modo", formate="formato")
  @app_commands.choices(onlineMode=[
      app_commands.Choice(name="Online", value=1),
      app_commands.Choice(name="Offline", value=0)
  ], formate=[
      app_commands.Choice(name="Aleatório", value=0),
      app_commands.Choice(name="Livre", value=1),
  ])
  async def criarPerson(self, interaction: discord.Interaction, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int]):

    # Variaveis
    confirmedUsers = []
    guildChannelsDict = {
        channel.name: channel for channel in interaction.guild.channels}
    channelNameWaiting = '| 🕘 | AGUARDANDO'
    channelNameBlue = 'LADO [ |🔵| ]'
    channelNameRed = 'LADO [ |🔴| ]'
    userCallCommand = interaction.user  # Usuario que chamou o comando

    # Verificar se o servidor possui os canais essenciais para o funcionamento da fila.
    if not all(channel in guildChannelsDict.keys() for channel in [channelNameWaiting, channelNameBlue, channelNameRed]):
      # Criar a view para confirmar a criação dos canais.
      viewCreateChannels = ViewActionConfirm(
          channels=[channelNameWaiting, channelNameBlue, channelNameRed])
      # Enviar a mensagem para o usuario permitir a criação dos canais.
      await interaction.response.send_message(content="Percebi que o servidor não possui os canais de voz essenciais para o funcionamento da fila. Será que você poderia me permitir criar esses canais?", ephemeral=True, view=viewCreateChannels)
      try:
        responseCreate = await asyncio.wait_for(viewCreateChannels.future, timeout=60)
        if responseCreate == '0':
          return
      except asyncio.TimeoutError:
        # Limite de tempo excedido, evento cancelado.
        return await interaction.delete_original_response()

    # 1. Pegar os canais de voz essenciais para o funcionamento da fila.
    guildChannelsDict = {
        channel.name: channel for channel in interaction.guild.channels}

    channelWaiting = guildChannelsDict[channelNameWaiting]
    channelBlue = guildChannelsDict[channelNameBlue]
    channelRed = guildChannelsDict[channelNameRed]
    # 2. Fazer os views para configuração da personalizada.

    # 3. Criar a personalizada.
    embedMessageCreate = self.generateEmbedConfirmed(
        confirmedUsers, onlineMode, formate)
    viewBtns = ViewBtnInterface(userCallCommand, channelWaiting, channelBlue,
                                channelRed, confirmedUsers, self.generateEmbedConfirmed, self.embedMessageTeam, onlineMode, formate)
    # Verificar se ja foi respondida a mensagem, se não, responde, se sim manda um follwup
    if interaction.response.is_done():
      await interaction.delete_original_response()
      await interaction.followup.send(embed=embedMessageCreate, view=viewBtns, file=discord.File('./images/timbasQueue.png'))
    else:
      await interaction.response.send_message(embed=embedMessageCreate, view=viewBtns, file=discord.File('./images/timbasQueue.png'))


async def setup(client):
  await client.add_cog(CriarPerson(client))
